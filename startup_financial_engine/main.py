from models.assumptions import StartupAssumptions
from models.forecast import ForecastAssumptions
from models.year_simulator import YearSimulator, apply_growth

def run_multi_year():

    # Base Year Assumptions
    base_assumptions = StartupAssumptions(
        price_per_unit=100,
        monthly_unit_sales=[10,20,30,40,50,60,70,80,90,100,110,120],
        cost_per_unit=40,
        rent=2000,
        payroll=5000,
        marketing=1000,
        utilities=500,
        equipment_cost=50000,
        buildout_cost=20000,
        owner_equity=60000,
        loan_amount=50000,
        loan_interest_rate=0.08,
        equipment_life_years=5
    )

    forecast = ForecastAssumptions(
        revenue_growth_rate=0.10,
        cost_growth_rate=0.05,
        fixed_expense_growth_rate=0.04
    )

    # year 1
    simulator = YearSimulator(base_assumptions)
    year1 = simulator.run_year()

    # year 2
    year2_assumptions = apply_growth(base_assumptions, forecast)
    simulator2 = YearSimulator(year2_assumptions)
    year2 = simulator2.run_year()

    # year 3
    year3_assumptions = apply_growth(year2_assumptions, forecast)
    simulator3 = YearSimulator(year3_assumptions)
    year3 = simulator3.run_year()

    print("Year 1 Profit:", sum([m["operating_income"] for m in year1]))
    print("Year 2 Profit:", sum([m["operating_income"] for m in year2]))
    print("Year 3 Profit:", sum([m["operating_income"] for m in year3]))
