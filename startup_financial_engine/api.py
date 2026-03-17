from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import InvalidTokenError

# Import your DB and Auth files
from database import SessionLocal, engine, Base
from models.user import User
from auth import verify_password, get_password_hash, create_access_token, SECRET_KEY, ALGORITHM

# Create the tables in the database (Run once)
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
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
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class SimulationRequest(BaseModel):
    price_per_unit: float
    monthly_unit_sales: List[int]
    cost_per_unit: float
    # ... (Keep your other SimulationRequest fields here)
    revenue_growth_rate: float

# --- AUTHENTICATION ROUTES ---

@app.post("/api/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/api/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Authenticate user
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT Token
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

# --- PROTECTED SIMULATION ROUTE ---

@app.post("/api/simulate")
def simulate(request: SimulationRequest, current_user: User = Depends(get_current_user)):
    # The current_user dependency locks this route!
    # If a React request doesn't have a valid JWT in the header, FastAPI will reject it.
    
    from models.assumptions import StartupAssumptions
    from models.forecast import ForecastAssumptions
    from models.year_simulator import YearSimulator, apply_growth

    base = StartupAssumptions(
        price_per_unit=request.price_per_unit,
        monthly_unit_sales=request.monthly_unit_sales,
        cost_per_unit=request.cost_per_unit,
        # ... map the rest of your variables here
    )

    forecast = ForecastAssumptions(
        revenue_growth_rate=request.revenue_growth_rate,
        # ... map the rest of your variables here
    )

    # Run 3 years
    year1 = YearSimulator(base).run_year()
    year2_assumptions = apply_growth(base, forecast)
    year2 = YearSimulator(year2_assumptions).run_year()
    year3_assumptions = apply_growth(year2_assumptions, forecast)
    year3 = YearSimulator(year3_assumptions).run_year()

    return {
        "user_email": current_user.email, # Optional: just to prove it knows who is logged in
        "year1": year1,
        "year2": year2,
        "year3": year3,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
