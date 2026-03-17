from models.assumptions import StartupAssumptions
from models.forecast import ForecastAssumptions
from models.year_simulator import YearSimulator, apply_growth
from models.decisions import InternalDecision, DecisionImpact 
import copy

def calculate_cash_metrics(timeline, starting_cash):
    current_cash = starting_cash
    for month_data in timeline:
        # 1. Update cash using REAL cash flow, not profit!
        current_cash += month_data["net_cash_flow"]
        month_data["cash_balance"] = current_cash
        
        # 2. Calculate the Runway based on cash burn
        burn_rate = -month_data["net_cash_flow"]
        if burn_rate > 0: 
            month_data["runway_months"] = current_cash / burn_rate
        else: 
            month_data["runway_months"] = 999 # Profitable, safe runway!

def run_multi_year():

    # 1. Base Year Assumptions
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

    # Calculate Day 0 Starting Cash
    starting_cash = (base_assumptions.owner_equity + base_assumptions.loan_amount) - (base_assumptions.equipment_cost + base_assumptions.buildout_cost)

    # 2. Loading the Decision (With Delays!)
    test_decision = InternalDecision(
        name="Hire Senior Sales Rep",
        start_month=6, 
        upfront_cost=5000, 
        recurring_cost=4000,
        impacts=[
            DecisionImpact(scenario_type="BEST", revenue_boost=15000, cost_change=0, delay_months=2),
            DecisionImpact(scenario_type="EXPECTED", revenue_boost=8000, cost_change=0, delay_months=2),
            DecisionImpact(scenario_type="WORST", revenue_boost=1000, cost_change=1000, delay_months=2)
        ]
    )

    # 3. Generate the 3-Year Baseline
    year1 = YearSimulator(base_assumptions).run_year()
    year2_assumptions = apply_growth(base_assumptions, forecast)
    year2 = YearSimulator(year2_assumptions).run_year()
    year3_assumptions = apply_growth(year2_assumptions, forecast)
    year3 = YearSimulator(year3_assumptions).run_year()

    baseline_timeline = year1 + year2 + year3

    # 4. The Optimized Simulation Engine (Branching the timelines)
    best_timeline = copy.deepcopy(baseline_timeline)
    expected_timeline = copy.deepcopy(baseline_timeline)
    worst_timeline = copy.deepcopy(baseline_timeline)

    # Bundle timelines for clean mapping
    timeline_map = {
        "BEST": best_timeline,
        "EXPECTED": expected_timeline,
        "WORST": worst_timeline
    }

    # Apply the decision's financial impacts
    for month_index in range(36):
        current_month = month_index + 1 
        
        if current_month >= test_decision.start_month:
            # A. Apply guaranteed costs to ALL timelines
            for timeline in timeline_map.values():
                timeline[month_index]["operating_income"] -= test_decision.recurring_cost
                timeline[month_index]["net_cash_flow"] -= test_decision.recurring_cost
                
                # Upfront cost only hits on the exact start month
                if current_month == test_decision.start_month:
                    timeline[month_index]["operating_income"] -= test_decision.upfront_cost
                    timeline[month_index]["net_cash_flow"] -= test_decision.upfront_cost

            # B. Apply uncertain impacts safely based on scenario type AND time delay
            for impact in test_decision.impacts:
                active_timeline = timeline_map.get(impact.scenario_type)
                
                # Calculate exactly when the revenue/cost changes should actually start
                impact_start_month = test_decision.start_month + impact.delay_months
                
                if active_timeline and current_month >= impact_start_month:
                    active_timeline[month_index]["operating_income"] += impact.revenue_boost - impact.cost_change
                    active_timeline[month_index]["net_cash_flow"] += impact.revenue_boost - impact.cost_change

    # Calculate Cash and Runway using the REAL cash flow
    calculate_cash_metrics(baseline_timeline, starting_cash)
    calculate_cash_metrics(best_timeline, starting_cash)
    calculate_cash_metrics(expected_timeline, starting_cash)
    calculate_cash_metrics(worst_timeline, starting_cash)

    # 5. Print the Results!
    print(f"\n--- SIMULATION RESULTS: {test_decision.name} ---")
    print(f"Starting Cash: ${starting_cash:,.2f}\n")
    
    print(f"BASELINE: Ending Cash: ${baseline_timeline[-1]['cash_balance']:,.2f}")
    print(f"BEST:     Ending Cash: ${best_timeline[-1]['cash_balance']:,.2f}")
    print(f"EXPECTED: Ending Cash: ${expected_timeline[-1]['cash_balance']:,.2f}")
    print(f"WORST:    Ending Cash: ${worst_timeline[-1]['cash_balance']:,.2f}\n")

if __name__ == "__main__":
    run_multi_year()