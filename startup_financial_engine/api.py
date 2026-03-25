from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel,Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import InvalidTokenError
import copy

# Import your DB and Auth files
from database import SessionLocal, engine, Base
from models.user import User
from auth import verify_password, get_password_hash, create_access_token, SECRET_KEY, ALGORITHM

# --- NEW IMPORTS FOR SIMULATION LOGIC ---
from event_calculators import apply_event_wrapper
from main import calculate_cash_metrics

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # In development, this allows requests from anywhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# The security scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# Pydantic Schemas
class UserCreate(BaseModel):
    email: str
    password: str= Field(..., max_length=72)

class Token(BaseModel):
    access_token: str
    token_type: str

class SimulationRequest(BaseModel):
    # Core Assumption Fields
    price_per_unit: float
    monthly_unit_sales: List[int]
    cost_per_unit: float
    revenue_growth_rate: float
    
    # Financial Fields (with defaults from main.py)
    rent: float = 2000
    payroll: float = 5000
    marketing: float = 1000
    utilities: float = 500
    equipment_cost: float = 50000
    buildout_cost: float = 20000
    owner_equity: float = 60000
    loan_amount: float = 50000
    loan_interest_rate: float = 0.08
    equipment_life_years: int = 5
    
    # --- NEW FIELDS FOR INTERNAL EVENTS ---
    event_type: Optional[str] = None
    event_payload: Optional[Dict[str, Any]] = None

# --- AUTHENTICATION ROUTES ---
@app.post("/api/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/api/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- PROTECTED DEPENDENCY ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# --- UPDATED SIMULATION ROUTE ---
@app.post("/api/simulate")
def simulate(request: SimulationRequest, current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    from models.assumptions import StartupAssumptions
    from models.forecast import ForecastAssumptions
    from year_simulator import YearSimulator, apply_growth
    from models.simulation_run import SimulationRun

    # 1. Map Assumptions
    base = StartupAssumptions(
        price_per_unit=request.price_per_unit,
        monthly_unit_sales=request.monthly_unit_sales,
        cost_per_unit=request.cost_per_unit,
        rent=request.rent,
        payroll=request.payroll,
        marketing=request.marketing,
        utilities=request.utilities,
        equipment_cost=request.equipment_cost,
        buildout_cost=request.buildout_cost,
        owner_equity=request.owner_equity,
        loan_amount=request.loan_amount,
        loan_interest_rate=request.loan_interest_rate,
        equipment_life_years=request.equipment_life_years
    )

    forecast = ForecastAssumptions(
        revenue_growth_rate=request.revenue_growth_rate,
        cost_growth_rate=0.05,
        fixed_expense_growth_rate=0.04
    )

    # 2. Calculate Day 0 Starting Cash
    starting_cash = (base.owner_equity + base.loan_amount) - (base.equipment_cost + base.buildout_cost)

    # 3. Generate the 3-Year Baseline
    year1 = YearSimulator(base).run_year()
    year2_assumptions = apply_growth(base, forecast)
    year2 = YearSimulator(year2_assumptions).run_year()
    year3_assumptions = apply_growth(year2_assumptions, forecast)
    year3 = YearSimulator(year3_assumptions).run_year()
    
    baseline_timeline = year1 + year2 + year3


    scenario = db.query(Scenario).filter(Scenario.user_id == current_user.id).first()
    db_decisions = scenario.decisions if scenario else []
    scenario_timeline = copy.deepcopy(baseline_timeline)
    # This ensures "Best/Expected/Worst" reflect your persistent events
    for d in db_decisions:
        # Example: Applying a hiring event to the timeline
        current_decision_data = {
            "impact": d.impact,
            "startMonth": d.start_month,
            "lag": d.lag_months,
            "ramp": d.ramp_months,
            "duration": d.duration_months if d.duration_months else "permanent"
        }
        
        temp_scenario_map = {
            "BEST": scenario_timeline,
            "EXPECTED": scenario_timeline,
            "WORST": scenario_timeline
        }
        
        apply_event_wrapper(
            temp_scenario_map, 
            d.type, 
            current_decision_data 
        )
    
    best_timeline = copy.deepcopy(baseline_timeline)
    expected_timeline = copy.deepcopy(baseline_timeline)
    worst_timeline = copy.deepcopy(baseline_timeline)

    timeline_map = {
        "BEST": best_timeline,
        "EXPECTED": expected_timeline,
        "WORST": worst_timeline
    }

    # 5. Apply Internal Events using the Dispatcher
    apply_event_wrapper(timeline_map, request.event_type, request.event_payload)

    # 6. Finalize Cash & Runway Metrics
    calculate_cash_metrics(baseline_timeline, starting_cash)
    calculate_cash_metrics(scenario_timeline, starting_cash)
    calculate_cash_metrics(best_timeline, starting_cash)
    calculate_cash_metrics(expected_timeline, starting_cash)
    calculate_cash_metrics(worst_timeline, starting_cash)

    simulation_run = SimulationRun(
        user_id=current_user.id,
        inputs=request.dict(),
        result={
            "baseline": baseline_timeline,
            "scenario": scenario_timeline,
            "best": best_timeline,
            "expected": expected_timeline,
            "worst": worst_timeline
        },
    )
    db.add(simulation_run)
    db.commit()


    return {
        "user_email": current_user.email,
        "baseline": baseline_timeline,
        "year1": baseline_timeline[0:12],
        "year2": baseline_timeline[12:24],
        "year3": baseline_timeline[24:36],
        "scenario_year1": scenario_timeline[0:12],
        "scenario_year2": scenario_timeline[12:24],
        "scenario_year3": scenario_timeline[24:36],
        "best": best_timeline,
        "expected": expected_timeline,
        "worst": worst_timeline
    }


# Add this route to your startup_financial_engine/api.py

from models.simulation_run import SimulationRun

@app.get("/api/simulation/latest")
def get_latest_simulation(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Retrieve the most recent simulation run for this specific user
    last_run = db.query(SimulationRun)\
                 .filter(SimulationRun.user_id == current_user.id)\
                 .order_by(SimulationRun.created_at.desc())\
                 .first()
    
    if not last_run:
        return {"inputs": None}
    
    return {
        "inputs": last_run.inputs,
        "result": last_run.result
    }
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
    # READ: Get the user's most recent simulation run
    last_run = db.query(SimulationRun)\
                 .filter(SimulationRun.user_id == current_user.id)\
                 .order_by(SimulationRun.created_at.desc())\
                 .first()
    
    if not last_run:
        return {"inputs": None}
    
    return {
        "id": last_run.id,
        "inputs": last_run.inputs,
        "result": last_run.result
    }

@app.delete("/api/simulation/{run_id}")
def delete_simulation(
    run_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # DELETE: Remove a specific run from the database
    run = db.query(SimulationRun).filter(
        SimulationRun.id == run_id, 
        SimulationRun.user_id == current_user.id
    ).first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    db.delete(run)
    db.commit()
    return {"status": "deleted"}

# startup_financial_engine/api.py
from models.scenario import Scenario
from models.scenario_decision import ScenarioDecision

# startup_financial_engine/api.py

# startup_financial_engine/api.py

@app.post("/api/scenarios/decisions")
def add_decision(decision_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scenario = db.query(Scenario).filter(Scenario.user_id == current_user.id).first()
    if not scenario:
        scenario = Scenario(user_id=current_user.id, name="Active Scenario")
        db.add(scenario)
        db.commit()
        db.refresh(scenario)
    
    # Manually map keys from frontend (camelCase) to DB (snake_case)
    new_decision = ScenarioDecision(
        scenario_id=scenario.id,
        type=decision_data['type'],
        name=decision_data.get('name', decision_data['type']),
        impact=float(decision_data['impact']),
        start_month=int(decision_data['startMonth']),
        lag_months=int(decision_data.get('lag', 0)),
        ramp_months=int(decision_data.get('ramp', 1)),
        duration_months=None if decision_data['duration'] == "permanent" else int(decision_data['duration'])
    )
    db.add(new_decision)
    db.commit()
    db.refresh(new_decision) 
    return new_decision

@app.get("/api/scenarios/active/decisions")
def get_active_decisions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scenario = db.query(Scenario).filter(Scenario.user_id == current_user.id).first()
    if not scenario:
        return []
        
    # Map DB objects back to Frontend interface
    return [
        {
            "id": str(d.id),
            "type": d.type,
            "name": d.name,
            "impact": d.impact,
            "startMonth": d.start_month,
            "lag": d.lag_months,
            "ramp": d.ramp_months,
            "duration": "permanent" if d.duration_months is None else str(d.duration_months)
        } for d in scenario.decisions
    ]
    scenario = db.query(Scenario).filter(Scenario.user_id == current_user.id).first()
    
    # payload mapping
    new_decision = ScenarioDecision(
        scenario_id=scenario.id,
        type=decision_data['type'],
        name=decision_data.get('name', 'New Decision'),
        impact=float(decision_data['impact']),
        start_month=int(decision_data['startMonth']), # Map frontend 'startMonth' to DB 'start_month'
        lag_months=int(decision_data.get('lag', 0)),
        ramp_months=int(decision_data.get('ramp', 1)),
        duration_months=None if decision_data['duration'] == "permanent" else int(decision_data['duration'])
    )
    
    db.add(new_decision)
    db.commit()
    db.refresh(new_decision)
    return new_decision

@app.delete("/api/scenarios/decisions/{decision_id}")
def delete_decision(decision_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    decision = db.query(ScenarioDecision).join(Scenario).filter(
        ScenarioDecision.id == decision_id, 
        Scenario.user_id == current_user.id
    ).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    db.delete(decision)
    db.commit()
    return {"message": "Deleted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
