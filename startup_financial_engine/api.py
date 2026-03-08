from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request body schema
class SimulationRequest(BaseModel):
    price_per_unit: float
    monthly_unit_sales: List[int]
    cost_per_unit: float
    rent: float
    payroll: float
    marketing: float
    utilities: float
    equipment_cost: float
    buildout_cost: float
    owner_equity: float
    loan_amount: float
    loan_interest_rate: float
    equipment_life_years: int
    revenue_growth_rate: float
    cost_growth_rate: float
    fixed_expense_growth_rate: float

@app.post("/api/simulate")
def simulate(request: SimulationRequest):
    # Import existing engine classes
    from models.assumptions import StartupAssumptions
    from models.forecast import ForecastAssumptions
    from models.year_simulator import YearSimulator, apply_growth

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
        equipment_life_years=request.equipment_life_years,
    )

    forecast = ForecastAssumptions(
        revenue_growth_rate=request.revenue_growth_rate,
        cost_growth_rate=request.cost_growth_rate,
        fixed_expense_growth_rate=request.fixed_expense_growth_rate,
    )

    # Run 3 years
    year1 = YearSimulator(base).run_year()

    year2_assumptions = apply_growth(base, forecast)
    year2 = YearSimulator(year2_assumptions).run_year()

    year3_assumptions = apply_growth(year2_assumptions, forecast)
    year3 = YearSimulator(year3_assumptions).run_year()

    return {
        "year1": year1,
        "year2": year2,
        "year3": year3,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)