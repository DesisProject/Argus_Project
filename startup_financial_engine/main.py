"""
main.py — Financial simulation orchestrator with AI layer.

Pipeline:
  1.  Build assumptions & 3-year baseline
  2.  Branch into BEST / EXPECTED / WORST timelines
  3.  Apply business events via event_calculator
  4.  Recalculate cash metrics
  5.  Run automated audit
  6.  Compute resilience grades
  7.  Detect risk signals
  8.  Run stress tests + Monte Carlo
  9.  Print structured report
  10. Launch AI-powered interactive menu
"""

from __future__ import annotations

import copy
import os
from typing import Dict, List

# ── Model imports ──────────────────────────────────────────────────────────────
from models.assumptions import StartupAssumptions
from models.forecast import ForecastAssumptions
from models.year_simulator import YearSimulator, apply_growth
from event_calculators import apply_events_batch
from resilience import summarize_resilience
from risk_signals import detect_all_scenario_signals
from models.audit import run_full_audit
from models.stress import (
    run_stress_tests,
    run_monte_carlo,
    MonteCarloConfig,
)

# ── AI imports ─────────────────────────────────────────────────────────────────
from ai.client import SimulationContext
from ai.query import QueryInterface
from ai.audit_narrator import generate_audit_narrative, generate_finding_explanation
from ai.risk_advisor import generate_risk_brief, explain_signal, interpret_stress_tests
from ai.event_recommender import recommend_events, evaluate_event, what_if


# ─────────────────────────────────────────────────────────────────────────────
# Cash recalculation
# ─────────────────────────────────────────────────────────────────────────────

def recalculate_cash(timeline: List[dict], starting_cash: float) -> None:
    cash = starting_cash
    for m in timeline:
        cash += m.get("net_cash_flow", 0)
        m["cash_balance"] = cash
        burn = -m.get("net_cash_flow", 0)
        m["runway_months"] = (cash / burn) if burn > 0 else 999.0


# ─────────────────────────────────────────────────────────────────────────────
# Print helpers
# ─────────────────────────────────────────────────────────────────────────────

SEP = "─" * 70

def _fmt(v: float) -> str:
    return f"${v:>12,.0f}"

def _section(title: str) -> None:
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}")

def _print_resilience(scenario_resilience):
    _section("RESILIENCE GRADES")
    print(f"{'Scenario':<12} {'Grade':<7} {'Score':>6} {'Runway':>8} {'Ending Cash':>14} {'Survives':>9}")
    print(SEP)
    for name, r in scenario_resilience.items():
        print(f"{name:<12} {r['grade']:<7} {r['score']:>6} {r['runway_months']:>7.0f}m "
              f"{_fmt(r['ending_cash_balance'])} {'YES' if r['survives_horizon'] else 'NO':>9}")

def _print_signals(all_signals):
    _section("RISK SIGNALS")
    for scenario, signals in all_signals.items():
        if not signals:
            print(f"\n  [{scenario}] No signals detected"); continue
        print(f"\n  [{scenario}]")
        for s in signals:
            level = "[CRITICAL]" if s["level"] == "critical" else "[WARNING] "
            mo    = f" (month {s['month']})" if s.get("month") else ""
            print(f"    {level} {s['title']}{mo}\n             {s['message']}")

def _print_audit(audit_reports):
    _section("AUTOMATED AUDIT")
    for _, report in audit_reports.items():
        print(f"\n  {report.summary_line()}")
        for f in report.findings:
            sev = "[ERROR]  " if f.severity == "error" else "[WARNING]"
            print(f"    {sev} [{f.code}] {f.title}\n             {f.detail}")

def _print_stress(stress_results):
    _section("STRESS TESTS")
    print(f"  {'Shock':<35} {'Grade':<7} {'Drop':>5} {'Runway':>8} {'Ending Cash':>14}")
    print(f"  {SEP}")
    for r in stress_results:
        drop = f"-{r.grade_drop}" if r.grade_drop > 0 else "  0"
        print(f"  {r.shock_name:<35} {r.grade:<7} {drop:>5} "
              f"{r.runway_months:>7.0f}m {_fmt(r.ending_cash)}")

def _print_monte_carlo(mc):
    _section("MONTE CARLO (1,000 iterations)")
    print(f"  Survival rate:    {mc.survival_rate:.1%}")
    print(f"  Insolvency prob:  {mc.insolvency_probability:.1%}")
    if mc.avg_insolvency_month:
        print(f"  Avg insolvency:   month {mc.avg_insolvency_month:.1f}")
    print(f"  Median cash:      {_fmt(mc.median_ending_cash)}")
    print(f"  P10 / P90:        {_fmt(mc.p10_ending_cash)} / {_fmt(mc.p90_ending_cash)}")
    print(f"  VaR (5th pct):    {_fmt(mc.var_95)}")
    print("\n  Grade distribution:")
    for g in ["O","A","B","C","D","F"]:
        pct = mc.grade_distribution.get(g, 0)
        bar = "#" * int(pct * 40)
        print(f"    {g}  {bar:<40} {pct:.1%}")

def _print_monthly(timeline, label, n=18):
    _section(f"MONTHLY DETAIL -- {label} (first {n} months)")
    print(f"  {'Mo':>3}  {'Revenue':>10}  {'COGS':>10}  {'Gross P':>10}  "
          f"{'Op Inc':>10}  {'Net CF':>10}  {'Cash Bal':>12}  {'Runway':>8}")
    print(f"  {SEP}")
    for m in timeline[:n]:
        print(f"  {m.get('month','?'):>3}  "
              f"{m.get('revenue',0):>10,.0f}  {m.get('cogs',0):>10,.0f}  "
              f"{m.get('gross_profit',0):>10,.0f}  {m.get('operating_income',0):>10,.0f}  "
              f"{m.get('net_cash_flow',0):>10,.0f}  {m.get('cash_balance',0):>12,.0f}  "
              f"{m.get('runway_months',0):>7.1f}m")


# ─────────────────────────────────────────────────────────────────────────────
# Interactive AI menu
# ─────────────────────────────────────────────────────────────────────────────

AI_MENU = """
+----------------------------------------------------------------------+
|                      AI FINANCIAL ADVISOR                            |
+----------------------------------------------------------------------+
|  1. Ask a question about your simulation  (Query Interface)          |
|  2. Generate AI audit narrative memo                                 |
|  3. Generate board-level risk brief                                  |
|  4. Explain a specific risk signal                                   |
|  5. Interpret stress test results                                    |
|  6. Get event recommendations (improve runway / grade)               |
|  7. Evaluate a specific event you are considering                    |
|  8. What-if analysis                                                 |
|  9. Explain a specific audit finding code                            |
|  0. Exit                                                             |
+----------------------------------------------------------------------+
"""

def _run_ai_menu(ctx: SimulationContext) -> None:
    qi = QueryInterface(ctx)

    while True:
        print(AI_MENU)
        choice = input("Choose an option [0-9]: ").strip()

        if choice == "0":
            print("\nGoodbye.")
            break

        elif choice == "1":
            qi.run()

        elif choice == "2":
            scen = input("  Scenario (BEST/EXPECTED/WORST or Enter for all): ").strip().upper()
            generate_audit_narrative(ctx, scen if scen in ctx.timeline_map else None)

        elif choice == "3":
            generate_risk_brief(ctx)

        elif choice == "4":
            print("  Available signals:")
            seen = set()
            for sigs in ctx.all_signals.values():
                for s in sigs:
                    if s["title"] not in seen:
                        print(f"    - {s['title']}")
                        seen.add(s["title"])
            title = input("  Signal to explain: ").strip()
            explain_signal(ctx, title)

        elif choice == "5":
            interpret_stress_tests(ctx)

        elif choice == "6":
            goal = input("  Your goal (Enter for default): ").strip()
            recommend_events(ctx, goal or "Maximise runway and achieve at least a B resilience grade")

        elif choice == "7":
            print("  Event types: hire / marketing / reduce / contract / inventory / expand")
            etype = input("  Event type: ").strip()
            desc  = input("  Describe what you are considering: ").strip()
            evaluate_event(ctx, etype, desc)

        elif choice == "8":
            question = input("  What-if question: ").strip()
            what_if(ctx, question)

        elif choice == "9":
            code = input("  Audit finding code (e.g. PLB004): ").strip().upper()
            generate_finding_explanation(ctx, code)

        else:
            print("  Invalid option.")

        input("\n  [Press Enter to return to menu]")


# ─────────────────────────────────────────────────────────────────────────────
# Main simulation
# ─────────────────────────────────────────────────────────────────────────────

def run_simulation(interactive: bool = True) -> SimulationContext:

    # 1. Assumptions
    base = StartupAssumptions(
        price_per_unit=100,
        monthly_unit_sales=[10,20,30,40,50,60,70,80,90,100,110,120],
        cost_per_unit=40,
        rent=2_000, payroll=5_000, marketing=1_000, utilities=500,
        equipment_cost=50_000, buildout_cost=20_000,
        owner_equity=60_000, loan_amount=50_000,
        loan_interest_rate=0.08, equipment_life_years=5,
    )
    forecast = ForecastAssumptions(
        revenue_growth_rate=0.10,
        cost_growth_rate=0.05,
        fixed_expense_growth_rate=0.04,
    )
    starting_cash = base.starting_cash

    # 2. Three-year baseline
    y2_base = apply_growth(base, forecast)
    y3_base = apply_growth(y2_base, forecast)
    baseline_timeline = (
        YearSimulator(base).run_year()
        + YearSimulator(y2_base).run_year()
        + YearSimulator(y3_base).run_year()
    )

    # 3. Branch timelines
    timeline_map: Dict[str, List[dict]] = {
        "BEST":     copy.deepcopy(baseline_timeline),
        "EXPECTED": copy.deepcopy(baseline_timeline),
        "WORST":    copy.deepcopy(baseline_timeline),
    }

    # 4. Events
    events = [
        {"name": "Hire Senior Sales Rep",           "type": "hire",
         "payload": {"start_month": 6, "upfront_cost": 5_000, "recurring_cost": 4_000}},
        {"name": "Reduce Vendor Costs",              "type": "reduce",
         "payload": {"start_month": 4, "upfront_cost": 2_000, "impact": -1_500,
                     "lag_months": 1, "ramp_months": 2}},
        {"name": "Bulk Inventory Purchase",          "type": "inventory",
         "payload": {"start_month": 3, "upfront_cost": 10_000, "impact": -500}},
        {"name": "Summer Marketing Campaign",        "type": "marketing",
         "payload": {"startMonth": 7, "upfront_cost": 3_000, "recurring_cost": 500,
                     "impact": 8_000, "lag_months": 1, "ramp_months": 3, "duration_months": 6}},
        {"name": "Enterprise Contract -- Acme Corp", "type": "contract",
         "payload": {"startMonth": 10, "impact": 6_000, "duration_months": 12}},
    ]
    summary = apply_events_batch(timeline_map, events)
    print(f"\nEvents applied: {summary['applied']}")
    if summary["skipped"]:
        print(f"Skipped:        {summary['skipped']}")

    # 5. Cash recalculation
    recalculate_cash(baseline_timeline, starting_cash)
    for tl in timeline_map.values():
        recalculate_cash(tl, starting_cash)

    # 6-8. Reports
    audit_reports      = run_full_audit(timeline_map, starting_cash)
    scenario_resilience = {n: summarize_resilience(tl) for n, tl in timeline_map.items()}
    all_signals        = detect_all_scenario_signals(timeline_map, scenario_resilience)
    stress_results     = run_stress_tests(timeline_map["EXPECTED"], starting_cash)
    mc                 = run_monte_carlo(timeline_map["EXPECTED"], starting_cash,
                                         config=MonteCarloConfig(iterations=1_000, seed=42))

    _print_audit(audit_reports)
    _print_resilience(scenario_resilience)
    _print_signals(all_signals)
    _print_stress(stress_results)
    _print_monte_carlo(mc)
    _print_monthly(timeline_map["EXPECTED"], "EXPECTED", n=18)

    # Executive summary
    exp_r  = scenario_resilience["EXPECTED"]
    n_crit = sum(1 for sigs in all_signals.values() for s in sigs if s["level"] == "critical")
    n_tot  = sum(len(v) for v in all_signals.values())
    _section("EXECUTIVE SUMMARY")
    print(f"  Grade:             {exp_r['grade']} ({exp_r['label']})")
    print(f"  Runway:            {exp_r['runway_months']:.0f} months")
    print(f"  Ending cash:       {_fmt(exp_r['ending_cash_balance'])}")
    print(f"  MC survival rate:  {mc.survival_rate:.1%}")
    print(f"  Audit errors:      {sum(r.errors for r in audit_reports.values())}")
    print(f"  Risk signals:      {n_tot} total, {n_crit} critical")

    # 9. Build SimulationContext for AI
    ctx = SimulationContext(
        assumptions         = base.to_dict(),
        starting_cash       = starting_cash,
        timeline_map        = timeline_map,
        scenario_resilience = scenario_resilience,
        all_signals         = all_signals,
        audit_reports       = {n: r.to_dict() for n, r in audit_reports.items()},
        stress_results      = [
            {"shock_name": r.shock_name, "description": r.description,
             "grade": r.grade, "score": r.score, "grade_drop": r.grade_drop,
             "insolvency_month": r.insolvency_month, "runway_months": r.runway_months,
             "ending_cash": r.ending_cash, "survives": r.survives}
            for r in stress_results
        ],
        monte_carlo = {
            "survival_rate":          mc.survival_rate,
            "insolvency_probability": mc.insolvency_probability,
            "avg_insolvency_month":   mc.avg_insolvency_month,
            "median_ending_cash":     mc.median_ending_cash,
            "p10_ending_cash":        mc.p10_ending_cash,
            "p90_ending_cash":        mc.p90_ending_cash,
            "var_95":                 mc.var_95,
            "grade_distribution":     mc.grade_distribution,
        },
        events = events,
    )

    # 10. AI menu
    if interactive:
        if not os.environ.get("GROQ_API_KEY"):
            print("\nNote: Set GROQ_API_KEY to enable AI features.")
            print("  export GROQ_API_KEY=your-key-from-console.groq.com")
        else:
            print("\n\nSimulation complete. Launching AI advisor...")
            _run_ai_menu(ctx)

    return ctx


if __name__ == "__main__":
    run_simulation(interactive=True)
