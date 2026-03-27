from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from models.assumptions import StartupAssumptions
from models.forecast import ForecastAssumptions
from models.year_simulator import YearSimulator, apply_growth
from models.decisions import InternalDecision, DecisionImpact 
from models.audit import AuditEngine
from models.alerts import generate_alerts
from models.stress import StressTester

import copy

def compare_scenarios(timelines, starting_cash):
    from resilience import summarize_resilience
    from risk_signals import detect_fragility_signal

    comparison = []

    baseline_summary = summarize_resilience(timelines["BASELINE"])

    for name, tl in timelines.items():
        summary = summarize_resilience(tl)

        comparison.append({
            "scenario": name,
            "ending_cash": tl[-1]["cash_balance"],
            "min_cash": min(m["cash_balance"] for m in tl),
            "runway_months": summary["runway_months"],
            "volatility": volatility(tl),
            "grade": summary["grade"]
        })

    # Sort by best outcome (growth)
    comparison.sort(key=lambda x: x["ending_cash"], reverse=True)

    print("\n================ SCENARIO COMPARISON ================")
    for c in comparison:
        print(
            f"{c['scenario']}: "
            f"Ending Cash={c['ending_cash']:,.2f}, "
            f"Min Cash={c['min_cash']:,.2f}, "
            f"Runway={c['runway_months']}, "
            f"Volatility={c['volatility']:.2f}, "
            f"Grade={c['grade']}"
        )

    print("\n--- DOWNSIDE ANALYSIS ---")

    for name, tl in timelines.items():
        if name == "BASELINE":
            continue

        target_summary = summarize_resilience(tl)
        fragility = detect_fragility_signal(baseline_summary, target_summary, name)

        if fragility:
            print(f"⚠️ {name}: {fragility['message']}")


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

def min_cash(timeline):
    return min(m["cash_balance"] for m in timeline)

def first_runway_breach(timeline, threshold=3):
    for m in timeline:
        if m["runway_months"] < threshold:
            return m["month"]
    return None

def volatility(timeline):
    flows = [m["net_cash_flow"] for m in timeline]
    mean = sum(flows) / len(flows)
    var = sum((x - mean)**2 for x in flows) / len(flows)
    return var ** 0.5

def recommend_strategy(timeline):
    end_cash = timeline[-1]["cash_balance"]
    min_c = min_cash(timeline)

    if end_cash < 0:
        return "CRITICAL: Raise funds or cut costs"
    if min_c < 10000:
        return "WARNING: Low safety buffer"
    return "Healthy"

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
    # 1. Hiring
    hiring_decision = InternalDecision(
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
    # 2. Cost Reduction 
    cost_cut_decision = InternalDecision( 
        name="Reduce Vendor Costs", 
        start_month=4, 
        upfront_cost=2000, 
        recurring_cost=0, 
        impacts=[
             DecisionImpact("BEST", 0, -2000, 1), 
            DecisionImpact("EXPECTED", 0, -1500, 1), 
             DecisionImpact("WORST", 0, -800, 2) 
        ] 
        )
    
    # 3. Inventory 
    inventory_decision = InternalDecision(
         name="Bulk Inventory Purchase", 
         start_month=3, upfront_cost=10000, 
         recurring_cost=0, 
         impacts=[
                 DecisionImpact("BEST", 0, -800, 0),
                DecisionImpact("EXPECTED", 0, -500, 0),
                  DecisionImpact("WORST", 0, -200, 0) 
            ]
        )
    
    decisions = [
         hiring_decision, 
         cost_cut_decision, 
         inventory_decision ]
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
    for decision in decisions: 
        print(f"\n=== Applying Decision: {decision.name} ===")

        for month_index in range(36): 
            current_month = month_index + 1 
            if current_month >= decision.start_month: 
                print(f"{decision.name} active at month {current_month}")
                # Apply guaranteed costs 
                for timeline in timeline_map.values(): 
                    timeline[month_index]["operating_income"] -= decision.recurring_cost 
                    timeline[month_index]["net_cash_flow"] -= decision.recurring_cost 
                    
                    if current_month == decision.start_month: 
                        timeline[month_index]["operating_income"] -= decision.upfront_cost 
                        timeline[month_index]["net_cash_flow"] -= decision.upfront_cost 
                
                # Apply uncertain impacts 
                for impact in decision.impacts: 
                    active_timeline = timeline_map.get(impact.scenario_type) 
                    impact_start = decision.start_month + impact.delay_months 
                    
                    if active_timeline and current_month >= impact_start: 
                        delta = impact.revenue_boost - impact.cost_change 
                        active_timeline[month_index]["operating_income"] += delta 
                        active_timeline[month_index]["net_cash_flow"] += delta

    # Calculate Cash and Runway using the REAL cash flow
    calculate_cash_metrics(baseline_timeline, starting_cash)
    calculate_cash_metrics(best_timeline, starting_cash)
    calculate_cash_metrics(expected_timeline, starting_cash)
    calculate_cash_metrics(worst_timeline, starting_cash)

    audit_engine = AuditEngine()

    print("\n================ AUDIT + ALERTS ================")

    timelines = {
        "BASELINE": baseline_timeline,
        "BEST": best_timeline,
        "EXPECTED": expected_timeline,
        "WORST": worst_timeline
    }

    for name, tl in timelines.items():
        print(f"\n--- {name} ---")

        # AUDIT
        issues = audit_engine.run_audit(tl)
        print("Audit Issues:")
        for issue in issues:
            print(" -", issue)

        # ALERTS
        alerts = generate_alerts(tl)
        print("Alerts:")
        for alert in alerts:
            print(" -", alert)

    stress = StressTester()

    print("\n================ STRESS TEST ================")

    # Demand crash scenario
    shock_assumptions = stress.apply_shock(base_assumptions, "demand_crash")
    shock_timeline = YearSimulator(shock_assumptions).run_year()

    calculate_cash_metrics(shock_timeline, starting_cash)

    print("Demand Crash Ending Cash:",
        shock_timeline[-1]["cash_balance"])


    # Cost spike scenario
    shock_assumptions2 = stress.apply_shock(base_assumptions, "cost_spike")
    shock_timeline2 = YearSimulator(shock_assumptions2).run_year()

    calculate_cash_metrics(shock_timeline2, starting_cash)

    print("\n================ MONTE CARLO ================")

    mc_results = stress.monte_carlo(base_assumptions, starting_cash, simulations=50)

    print("Worst Case:", min(mc_results))
    print("Best Case:", max(mc_results))
    print("Average:", sum(mc_results)/len(mc_results))

    print("\n================ DECISION RANKING ================")

    baseline_cash = baseline_timeline[-1]["cash_balance"]

    results = []

    for name, tl in timelines.items():
        if name == "BASELINE":
            continue
        
        improvement = tl[-1]["cash_balance"] - baseline_cash
        results.append((name, improvement))

    # Sort best → worst
    results.sort(key=lambda x: x[1], reverse=True)

    for name, value in results:
        print(f"{name}: {value:+,.2f}")

    print("\n================ MIN CASH (RISK) ================")

    for name, tl in timelines.items():
        print(f"{name}: {min_cash(tl):,.2f}")

    
    print("\n================ RUNWAY RISK ================")

    for name, tl in timelines.items():
        breach = first_runway_breach(tl)
        print(f"{name}: Runway <3 months at:", breach)

    
    print("\n================ VOLATILITY ================")

    for name, tl in timelines.items():
        print(f"{name}: {volatility(tl):,.2f}")

    print("\n================ STRATEGY ================")

    for name, tl in timelines.items():
        print(f"{name}: {recommend_strategy(tl)}")


    compare_scenarios(timelines, starting_cash)


    print("Cost Spike Ending Cash:",
        shock_timeline2[-1]["cash_balance"])
    # 5. Print the Results!
    print(f"\n--- SIMULATION RESULTS: {hiring_decision.name} ---")
    print(f"Starting Cash: ${starting_cash:,.2f}\n")
    
    print(f"BASELINE: Ending Cash: ${baseline_timeline[-1]['cash_balance']:,.2f}")
    print(f"BEST:     Ending Cash: ${best_timeline[-1]['cash_balance']:,.2f}")
    print(f"EXPECTED: Ending Cash: ${expected_timeline[-1]['cash_balance']:,.2f}")
    print(f"WORST:    Ending Cash: ${worst_timeline[-1]['cash_balance']:,.2f}\n")


    print("\n--- DEBUG (FIRST 6 MONTHS) ---")

    for i in range(6):
        print(f"\nMonth {i+1}")
        print("BASELINE:", baseline_timeline[i]["net_cash_flow"])
        print("BEST:    ", best_timeline[i]["net_cash_flow"])
        print("EXPECTED:", expected_timeline[i]["net_cash_flow"])
        print("WORST:   ", worst_timeline[i]["net_cash_flow"])

if __name__ == "__main__":
    run_multi_year()
