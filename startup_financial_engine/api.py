from fastapi import FastAPI, Depends, HTTPException, status, Response
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
from models.scenario import Scenario
from models.scenario_decision import ScenarioDecision
from models.simulation_run import SimulationRun
from auth import verify_password, get_password_hash, create_access_token, SECRET_KEY, ALGORITHM

# --- NEW IMPORTS FOR SIMULATION LOGIC ---
from event_calculators import apply_event_wrapper
from main import calculate_cash_metrics
from mitigation_engine import generate_mitigation_suggestions
from resilience import summarize_resilience
from risk_signals import (
    detect_fragility_signal,
    detect_timeline_risk_signals,
    sort_risk_signals,
)

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
    scenario_id: Optional[int] = None


class ScenarioDecisionIn(BaseModel):
    type: str
    name: str
    impact: float
    start_month: int
    lag_months: int = 0
    ramp_months: int = 1
    duration_months: Optional[int] = None


class ScenarioCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    decisions: List[ScenarioDecisionIn] = Field(default_factory=list)


class ScenarioUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    decisions: Optional[List[ScenarioDecisionIn]] = None


def _serialize_decision(decision: ScenarioDecision) -> Dict[str, Any]:
    return {
        "id": decision.id,
        "scenario_id": decision.scenario_id,
        "type": decision.type,
        "name": decision.name,
        "impact": decision.impact,
        "start_month": decision.start_month,
        "lag_months": decision.lag_months,
        "ramp_months": decision.ramp_months,
        "duration_months": decision.duration_months,
        "created_at": decision.created_at,
    }


def _serialize_scenario(scenario: Scenario) -> Dict[str, Any]:
    return {
        "id": scenario.id,
        "name": scenario.name,
        "description": scenario.description,
        "created_at": scenario.created_at,
        "updated_at": scenario.updated_at,
        "decisions": [_serialize_decision(d) for d in sorted(scenario.decisions, key=lambda x: x.id)],
    }


def _get_user_scenario(db: Session, user_id: int, scenario_id: int) -> Scenario:
    scenario = (
        db.query(Scenario)
        .filter(Scenario.id == scenario_id, Scenario.user_id == user_id)
        .first()
    )
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


def _get_active_scenario(db: Session, user_id: int) -> Optional[Scenario]:
    return (
        db.query(Scenario)
        .filter(Scenario.user_id == user_id)
        .order_by(Scenario.updated_at.desc(), Scenario.id.desc())
        .first()
    )


def _decision_to_event_payload(decision: ScenarioDecision) -> Dict[str, Any]:
    payload = {
        "impact": decision.impact,
        "startMonth": decision.start_month,
        "start_month": decision.start_month,
        "lag": decision.lag_months,
        "lag_months": decision.lag_months,
        "ramp": decision.ramp_months,
        "ramp_months": decision.ramp_months,
        "duration": decision.duration_months if decision.duration_months else "permanent",
        "duration_months": decision.duration_months,
    }

    if decision.type in {"hire", "hiring"}:
        payload["recurring_cost"] = abs(min(decision.impact, 0))
        payload["upfront_cost"] = 0
    elif decision.type in {"expand", "expansion"}:
        payload["recurring_cost"] = abs(min(decision.impact, 0))
        payload["upfront_cost"] = 0

    return payload


def _decision_snapshot(decision: ScenarioDecision) -> Dict[str, Any]:
    return {
        "type": decision.type,
        "name": decision.name,
        "impact": decision.impact,
        "start_month": decision.start_month,
        "lag_months": decision.lag_months,
        "ramp_months": decision.ramp_months,
        "duration_months": decision.duration_months,
    }

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
def simulate(
    request: SimulationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from models.assumptions import StartupAssumptions
    from models.forecast import ForecastAssumptions
    from models.year_simulator import YearSimulator, apply_growth
    from models.stress import StressTester
    tester = StressTester()

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


    selected_scenario = (
        _get_user_scenario(db, current_user.id, request.scenario_id)
        if request.scenario_id is not None
        else _get_active_scenario(db, current_user.id)
    )
    db_decisions = (
        sorted(selected_scenario.decisions, key=lambda decision: decision.id)
        if selected_scenario
        else []
    )
    decision_snapshots = [_decision_snapshot(decision) for decision in db_decisions]
    has_direct_event = bool(request.event_type and request.event_payload)
    has_active_scenario = bool(db_decisions) or has_direct_event

    scenario_best_timeline = copy.deepcopy(baseline_timeline)
    scenario_expected_timeline = copy.deepcopy(baseline_timeline)
    scenario_worst_timeline = copy.deepcopy(baseline_timeline)
    scenario_map = {
        "BEST": scenario_best_timeline,
        "EXPECTED": scenario_expected_timeline,
        "WORST": scenario_worst_timeline,
    }

    for decision in db_decisions:
        apply_event_wrapper(
            scenario_map,
            decision.type,
            _decision_to_event_payload(decision),
        )

    scenario_timeline = copy.deepcopy(scenario_expected_timeline)
    best_timeline = copy.deepcopy(scenario_best_timeline)
    expected_timeline = copy.deepcopy(scenario_expected_timeline)
    worst_timeline = copy.deepcopy(scenario_worst_timeline)

    timeline_map = {
        "BEST": best_timeline,
        "EXPECTED": expected_timeline,
        "WORST": worst_timeline
    }

    # 5. Apply Internal Events using the Dispatcher
    apply_event_wrapper(timeline_map, request.event_type, request.event_payload)

    # 6. Finalize Cash & Runway Metrics
    calculate_cash_metrics(baseline_timeline, starting_cash)
    calculate_cash_metrics(best_timeline, starting_cash)
    calculate_cash_metrics(expected_timeline, starting_cash)
    calculate_cash_metrics(worst_timeline, starting_cash)

    calculate_cash_metrics(scenario_timeline, starting_cash)
    resilience_summary = {
        "baseline": summarize_resilience(baseline_timeline),
        "scenario": summarize_resilience(scenario_timeline),
        "best": summarize_resilience(best_timeline),
        "expected": summarize_resilience(expected_timeline),
        "worst": summarize_resilience(worst_timeline),
    }
    scenario_signal_timeline = expected_timeline if has_direct_event else scenario_timeline
    scenario_signal_resilience = (
        resilience_summary["expected"] if has_direct_event else resilience_summary["scenario"]
    )
    risk_signals = {
        "baseline": detect_timeline_risk_signals(
            baseline_timeline,
            resilience_summary["baseline"],
        ),
        "scenario": [],
        "worst": [],
    }

    if has_active_scenario:
        risk_signals["scenario"] = detect_timeline_risk_signals(
            scenario_signal_timeline,
            scenario_signal_resilience,
        )
        risk_signals["worst"] = detect_timeline_risk_signals(
            worst_timeline,
            resilience_summary["worst"],
        )

        scenario_fragility = detect_fragility_signal(
            resilience_summary["baseline"],
            scenario_signal_resilience,
            "Scenario",
        )
        if scenario_fragility:
            risk_signals["scenario"].append(scenario_fragility)
            sort_risk_signals(risk_signals["scenario"])

        worst_fragility = detect_fragility_signal(
            resilience_summary["baseline"],
            resilience_summary["worst"],
            "Worst-case",
        )
        if worst_fragility:
            risk_signals["worst"].append(worst_fragility)
            sort_risk_signals(risk_signals["worst"])

    mitigation_suggestions = generate_mitigation_suggestions(
        request,
        decision_snapshots,
        {
            "resilience": resilience_summary,
        },
        risk_signals,
        has_direct_event,
    )

    mc_results = tester.monte_carlo(base, starting_cash, simulations=50)

    result_payload = {
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
        "worst": worst_timeline,
        "resilience": resilience_summary,
        "risk_signals": risk_signals,
        "mitigation_suggestions": mitigation_suggestions,
        "monte_carlo_outcomes": mc_results,
    }

    request_payload = request.dict()
    simulation_run = SimulationRun(
        user_id=current_user.id,
        scenario_id=request.scenario_id,
        inputs=request_payload,
        result=result_payload,
    )
    db.add(simulation_run)
    db.commit()
    db.refresh(simulation_run)

    result_payload["simulation_run_id"] = simulation_run.id
    return result_payload


@app.get("/api/scenarios")
def list_scenarios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scenarios = (
        db.query(Scenario)
        .filter(Scenario.user_id == current_user.id)
        .order_by(Scenario.updated_at.desc())
        .all()
    )
    return [_serialize_scenario(scenario) for scenario in scenarios]


@app.post("/api/scenarios", status_code=201)
def create_scenario(
    payload: ScenarioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scenario = Scenario(
        user_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description,
    )
    db.add(scenario)
    db.flush()

    for decision in payload.decisions:
        db.add(
            ScenarioDecision(
                scenario_id=scenario.id,
                type=decision.type,
                name=decision.name,
                impact=decision.impact,
                start_month=decision.start_month,
                lag_months=decision.lag_months,
                ramp_months=decision.ramp_months,
                duration_months=decision.duration_months,
            )
        )

    db.commit()
    db.refresh(scenario)
    return _serialize_scenario(scenario)


@app.get("/api/scenarios/{scenario_id}")
def get_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scenario = _get_user_scenario(db, current_user.id, scenario_id)
    return _serialize_scenario(scenario)


@app.put("/api/scenarios/{scenario_id}")
def update_scenario(
    scenario_id: int,
    payload: ScenarioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scenario = _get_user_scenario(db, current_user.id, scenario_id)

    if payload.name is not None:
        scenario.name = payload.name.strip()
    if payload.description is not None:
        scenario.description = payload.description

    if payload.decisions is not None:
        db.query(ScenarioDecision).filter(ScenarioDecision.scenario_id == scenario.id).delete()
        for decision in payload.decisions:
            db.add(
                ScenarioDecision(
                    scenario_id=scenario.id,
                    type=decision.type,
                    name=decision.name,
                    impact=decision.impact,
                    start_month=decision.start_month,
                    lag_months=decision.lag_months,
                    ramp_months=decision.ramp_months,
                    duration_months=decision.duration_months,
                )
            )

    db.commit()
    db.refresh(scenario)
    return _serialize_scenario(scenario)


@app.delete("/api/scenarios/{scenario_id}", status_code=204)
def delete_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scenario = _get_user_scenario(db, current_user.id, scenario_id)
    db.delete(scenario)
    db.commit()
    return Response(status_code=204)


@app.get("/api/simulation/latest")
def get_latest_simulation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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


@app.get("/api/simulation-runs")
def list_simulation_runs(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    runs = (
        db.query(SimulationRun)
        .filter(SimulationRun.user_id == current_user.id)
        .order_by(SimulationRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "scenario_id": r.scenario_id,
            "inputs": r.inputs,
            "result": r.result,
            "created_at": r.created_at,
        }
        for r in runs
    ]


@app.delete("/api/simulation-runs/all", status_code=204)
def delete_all_simulation_runs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(SimulationRun).filter(
        SimulationRun.user_id == current_user.id
    ).delete()
    db.commit()
    return Response(status_code=204)


@app.delete("/api/simulation-runs/{run_id}", status_code=204)
def delete_simulation_run(
    run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    run = db.query(SimulationRun).filter(
        SimulationRun.id == run_id,
        SimulationRun.user_id == current_user.id
    ).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    db.delete(run)
    db.commit()
    return Response(status_code=204)

@app.post("/api/scenarios/decisions")
def add_decision(
    decision_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scenario = db.query(Scenario).filter(Scenario.user_id == current_user.id).first()
    if not scenario:
        scenario = Scenario(user_id=current_user.id, name="Active Scenario")
        db.add(scenario)
        db.commit()
        db.refresh(scenario)

    new_decision = ScenarioDecision(
        scenario_id=scenario.id,
        type=decision_data["type"],
        name=decision_data.get("name", decision_data["type"]),
        impact=float(decision_data["impact"]),
        start_month=int(decision_data["startMonth"]),
        lag_months=int(decision_data.get("lag", 0)),
        ramp_months=int(decision_data.get("ramp", 1)),
        duration_months=(
            None if decision_data["duration"] == "permanent" else int(decision_data["duration"])
        ),
    )
    db.add(new_decision)
    db.commit()
    db.refresh(new_decision)
    return _serialize_decision(new_decision)


@app.get("/api/scenarios/active/decisions")
def get_active_decisions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scenario = (
        db.query(Scenario)
        .filter(Scenario.user_id == current_user.id)
        .order_by(Scenario.updated_at.desc())
        .first()
    )
    if not scenario:
        return []

    return [
        {
            "id": str(d.id),
            "type": d.type,
            "name": d.name,
            "impact": d.impact,
            "startMonth": d.start_month,
            "lag": d.lag_months,
            "ramp": d.ramp_months,
            "duration": "permanent" if d.duration_months is None else str(d.duration_months),
        }
        for d in scenario.decisions
    ]


@app.delete("/api/scenarios/decisions/{decision_id}")
def delete_decision(
    decision_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    decision = (
        db.query(ScenarioDecision)
        .join(Scenario)
        .filter(
            ScenarioDecision.id == decision_id,
            Scenario.user_id == current_user.id,
        )
        .first()
    )
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    db.delete(decision)
    db.commit()
    return {"message": "Deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
