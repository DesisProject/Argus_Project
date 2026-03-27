"""
main.py — Financial simulation orchestrator.

Pipeline:
  1. Build assumptions & 3-year baseline
  2. Branch into BEST / EXPECTED / WORST timelines
  3. Apply business events via event_calculator
  4. Recalculate cash metrics
  5. Run automated audit (integrity + plausibility + consistency)
  6. Compute resilience grades per scenario
  7. Detect risk signals per scenario
  8. Run stress tests + Monte Carlo on EXPECTED
  9. Print structured report
"""

from __future__ import annotations

import copy
import json
import textwrap
from typing import Dict, List

# ── Model imports ─────────────────────────────────────────────────────────────
from models.assumptions import StartupAssumptions
from models.forecast import ForecastAssumptions
from models.year_simulator import YearSimulator, apply_growth
from event_calculators import apply_events_batch
from resilience import summarize_resilience
from risk_signals import detect_all_scenario_signals
from models.audit import run_full_audit
from models.alerts import generate_alerts
from models.stress import (
    run_stress_tests,
    run_monte_carlo,
    run_sensitivity_sweep,
    MonteCarloConfig,
    STANDARD_SHOCKS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Cash & runway recalculation
# ─────────────────────────────────────────────────────────────────────────────

def recalculate_cash(timeline: List[dict], starting_cash: float) -> None:
    cash = starting_cash
    for m in timeline:
        cash += m.get("net_cash_flow", 0)
        m["cash_balance"] = cash
        burn = -m.get("net_cash_flow", 0)
        if cash <= 0:
            m["runway_months"] = 0
        elif burn > 0:
            m["runway_months"] = cash / burn
        else:
            m["runway_months"] = 999.0


# ─────────────────────────────────────────────────────────────────────────────
# Report helpers
# ─────────────────────────────────────────────────────────────────────────────

SEP = "─" * 70


def _fmt_cash(v: float) -> str:
    return f"${v:>12,.0f}"


def _print_section(title: str) -> None:
    print(f"\n{'═' * 70}")
    print(f"  {title}")
    print('═' * 70)


def _print_resilience_table(scenario_resilience: Dict[str, dict]) -> None:
    _print_section("RESILIENCE GRADES")
    header = f"{'Scenario':<12} {'Grade':<7} {'Score':>6} {'Runway':>8} {'Ending Cash':>14} {'Survives':>9}"
    print(header)
    print(SEP)
    for name, r in scenario_resilience.items():
        print(
            f"{name:<12} {r['grade']:<7} {r['score']:>6} "
            f"{r['runway_months']:>7.0f}m "
            f"{_fmt_cash(r['ending_cash_balance'])} "
            f"{'✅' if r['survives_horizon'] else '❌':>9}"
        )


def _print_risk_signals(all_signals: Dict[str, List[dict]]) -> None:
    _print_section("RISK SIGNALS")
    for scenario, signals in all_signals.items():
        if not signals:
            print(f"\n  [{scenario}] No risk signals detected ✅")
            continue
        print(f"\n  [{scenario}]")
        for s in signals:
            icon = "🔴" if s["level"] == "critical" else ("🟡" if s["level"] == "warning" else "🔵")
            month = f" (month {s['month']})" if s.get("month") else ""
            print(f"    {icon} {s['title']}{month}")
            print(f"       {s['message']}")


def _print_audit_reports(audit_reports: Dict) -> None:
    _print_section("AUTOMATED AUDIT")
    for scenario, report in audit_reports.items():
        print(f"\n  {report.summary_line()}")
        for finding in report.findings:
            icon = "❌" if finding.severity == "error" else ("⚠️ " if finding.severity == "warning" else "ℹ️ ")
            print(f"    {icon} [{finding.code}] {finding.title}")
            print(f"        {finding.detail}")


def _print_stress_tests(stress_results) -> None:
    _print_section("STRESS TESTS (applied to EXPECTED baseline)")
    print(f"  {'Shock':<35} {'Grade':<7} {'Drop':>5} {'Runway':>8} {'Ending Cash':>14} {'Survives':>9}")
    print(f"  {SEP}")
    for r in stress_results:
        drop_str = f"-{r.grade_drop}" if r.grade_drop > 0 else "  0"
        print(
            f"  {r.shock_name:<35} {r.grade:<7} {drop_str:>5} "
            f"{r.runway_months:>7.0f}m "
            f"{_fmt_cash(r.ending_cash)} "
            f"{'✅' if r.survives else '❌':>9}"
        )


def _print_monte_carlo(mc) -> None:
    _print_section("MONTE CARLO SIMULATION (1 000 iterations, EXPECTED baseline)")
    print(f"  Survival rate:          {mc.survival_rate:.1%}")
    print(f"  Insolvency probability: {mc.insolvency_probability:.1%}")
    if mc.avg_insolvency_month:
        print(f"  Avg insolvency month:   {mc.avg_insolvency_month:.1f}")
    print(f"  Median ending cash:     {_fmt_cash(mc.median_ending_cash)}")
    print(f"  P10 ending cash:        {_fmt_cash(mc.p10_ending_cash)}")
    print(f"  P90 ending cash:        {_fmt_cash(mc.p90_ending_cash)}")
    print(f"  VaR (5th pct):          {_fmt_cash(mc.var_95)}")
    print(f"  Median runway:          {mc.median_runway_months:.1f} months")
    print(f"\n  Grade distribution:")
    for grade in ["O", "A", "B", "C", "D", "F"]:
        pct = mc.grade_distribution.get(grade, 0)
        bar = "█" * int(pct * 40)
        print(f"    {grade}  {bar:<40} {pct:.1%}")


def _print_sensitivity(points, variable: str) -> None:
    _print_section(f"SENSITIVITY SWEEP — {variable.upper()} (EXPECTED baseline)")
    print(f"  {'Change':>8}  {'Grade':<7}  {'Ending Cash':>14}  {'Runway':>8}")
    print(f"  {SEP}")
    for p in points:
        sign = "+" if p.value >= 0 else ""
        print(f"  {sign}{p.value:>6.1f}%  {p.grade:<7}  {_fmt_cash(p.ending_cash)}  {p.runway_months:>7.0f}m")


def _print_monthly_table(timeline: List[dict], label: str, n_months: int = 12) -> None:
    _print_section(f"MONTHLY DETAIL — {label} (first {n_months} months)")
    header = (
        f"  {'Mo':>3}  {'Revenue':>10}  {'COGS':>10}  {'Gross P':>10}  "
        f"{'Op Inc':>10}  {'Net CF':>10}  {'Cash Bal':>12}  {'Runway':>8}"
    )
    print(header)
    print(f"  {SEP}")
    for m in timeline[:n_months]:
        mo = m.get("month", "?")
        print(
            f"  {mo:>3}  "
            f"{m.get('revenue', 0):>10,.0f}  "
            f"{m.get('cogs', 0):>10,.0f}  "
            f"{m.get('gross_profit', 0):>10,.0f}  "
            f"{m.get('operating_income', 0):>10,.0f}  "
            f"{m.get('net_cash_flow', 0):>10,.0f}  "
            f"{m.get('cash_balance', 0):>12,.0f}  "
            f"{m.get('runway_months', 0):>7.1f}m"
        )


def _print_scenario_comparison(resilience_map: Dict[str, dict]) -> None:
        _print_section("SCENARIO COMPARISON")

        print(f"{'Metric':<25} {'BEST':>12} {'EXPECTED':>12} {'WORST':>12}")
        print(SEP)

        def get(metric):
            return (
                resilience_map["BEST"][metric],
                resilience_map["EXPECTED"][metric],
                resilience_map["WORST"][metric],
            )

        # Grade
        b, e, w = get("grade")
        print(f"{'Grade':<25} {b:>12} {e:>12} {w:>12}")

        # Runway
        b, e, w = get("runway_months")
        print(f"{'Runway (months)':<25} {b:>12.0f} {e:>12.0f} {w:>12.0f}")

        # Ending Cash
        b, e, w = get("ending_cash_balance")
        print(f"{'Ending Cash':<25} {_fmt_cash(b):>12} {_fmt_cash(e):>12} {_fmt_cash(w):>12}")

        # Survival
        b, e, w = get("survives_horizon")
        print(f"{'Survives Horizon':<25} {str(b):>12} {str(e):>12} {str(w):>12}")
        
# ─────────────────────────────────────────────────────────────────────────────
# Main simulation
# ─────────────────────────────────────────────────────────────────────────────

def run_simulation() -> None:

    # ── 1. Assumptions ────────────────────────────────────────────────────────
    base = StartupAssumptions(
        price_per_unit=100,
        monthly_unit_sales=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120],
        cost_per_unit=40,
        rent=2_000,
        payroll=5_000,
        marketing=1_000,
        utilities=500,
        equipment_cost=50_000,
        buildout_cost=20_000,
        owner_equity=60_000,
        loan_amount=50_000,
        loan_interest_rate=0.08,
        equipment_life_years=5,
    )

    forecast = ForecastAssumptions(
        revenue_growth_rate=0.10,
        cost_growth_rate=0.05,
        fixed_expense_growth_rate=0.04,
    )

    starting_cash = base.starting_cash

    # ── 2. Three-year baseline timeline ───────────────────────────────────────
    year1 = YearSimulator(base).run_year()
    year2 = YearSimulator(apply_growth(base, forecast)).run_year()
    year3 = YearSimulator(apply_growth(apply_growth(base, forecast), forecast)).run_year()
    baseline_timeline = year1 + year2 + year3

    # ── 3. Branch into scenario timelines ─────────────────────────────────────
    timeline_map: Dict[str, List[dict]] = {
        "BEST":     copy.deepcopy(baseline_timeline),
        "EXPECTED": copy.deepcopy(baseline_timeline),
        "WORST":    copy.deepcopy(baseline_timeline),
    }

    # ── 4. Apply business events ──────────────────────────────────────────────
    events = [
        {
            "name": "Hire Senior Sales Rep",
            "type": "hire",
            "payload": {"start_month": 6, "upfront_cost": 5_000, "recurring_cost": 4_000},
        },
        {
            "name": "Reduce Vendor Costs",
            "type": "reduce",
            "payload": {"start_month": 4, "upfront_cost": 2_000, "impact": -1_500, "lag_months": 1, "ramp_months": 2},
        },
        {
            "name": "Bulk Inventory Purchase",
            "type": "inventory",
            "payload": {"start_month": 3, "upfront_cost": 10_000, "impact": -500},
        },
        {
            "name": "Summer Marketing Campaign",
            "type": "marketing",
            "payload": {
                "startMonth": 7, "upfront_cost": 3_000, "recurring_cost": 500,
                "impact": 8_000, "lag_months": 1, "ramp_months": 3, "duration_months": 6,
            },
        },
        {
            "name": "Enterprise Contract — Acme Corp",
            "type": "contract",
            "payload": {"startMonth": 10, "impact": 6_000, "duration_months": 12},
        },
    ]

    dispatch_summary = apply_events_batch(timeline_map, events)
    print(f"\n✅ Events applied:  {dispatch_summary['applied']}")
    if dispatch_summary["skipped"]:
        print(f"⚠️  Events skipped:  {dispatch_summary['skipped']}")

    # ── 5. Recalculate cash & runway ──────────────────────────────────────────
    # recalculate_cash(baseline_timeline, starting_cash)
    for tl in timeline_map.values():
        recalculate_cash(tl, starting_cash)

    # ── 6. Automated audit ────────────────────────────────────────────────────
    audit_reports = run_full_audit(timeline_map, starting_cash)
    _print_audit_reports(audit_reports)

    # ── 7. Resilience ─────────────────────────────────────────────────────────
    scenario_resilience = {name: summarize_resilience(tl) for name, tl in timeline_map.items()}
    _print_resilience_table(scenario_resilience)
    _print_scenario_comparison(scenario_resilience)

    # ── Alerts ───────────────────────────────────────────────────────────────
    _print_section("ALERTS")

    for scenario, tl in timeline_map.items():
        alerts = generate_alerts(tl)

        print(f"\n  [{scenario}]")

        if not alerts:
            print("    No alerts ✅")
            continue

        for a in alerts:
            print(f"    - [{a['type'].upper()}] {a['message']}")

    # ── 8. Risk signals ───────────────────────────────────────────────────────
    all_signals = detect_all_scenario_signals(timeline_map, scenario_resilience)
    _print_risk_signals(all_signals)

    # ── 9. Stress tests ───────────────────────────────────────────────────────
    stress_results = run_stress_tests(timeline_map["EXPECTED"], starting_cash)
    _print_stress_tests(stress_results)

    # ── 10. Monte Carlo ───────────────────────────────────────────────────────
    mc = run_monte_carlo(
        timeline_map["EXPECTED"],
        starting_cash,
        config=MonteCarloConfig(iterations=1_000, seed=42),
    )
    _print_monte_carlo(mc)

    # ── 11. Sensitivity sweeps ────────────────────────────────────────────────
    for var in ["revenue", "cost"]:
        points = run_sensitivity_sweep(timeline_map["EXPECTED"], starting_cash, variable=var)
        _print_sensitivity(points, var)

    # ── 12. Monthly detail tables ─────────────────────────────────────────────
    _print_monthly_table(timeline_map["EXPECTED"], "EXPECTED", n_months=18)

    # ── 13. Summary ───────────────────────────────────────────────────────────
    _print_section("EXECUTIVE SUMMARY")
    exp_r = scenario_resilience["EXPECTED"]
    total_signals = sum(len(v) for v in all_signals.values())
    total_errors  = sum(r.errors for r in audit_reports.values())
    critical_signals = sum(
        1 for sigs in all_signals.values() for s in sigs if s["level"] == "critical"
    )

    print(f"  Expected grade:        {exp_r['grade']} ({exp_r['label']})")
    print(f"  Expected runway:       {exp_r['runway_months']:.0f} months")
    print(f"  Expected ending cash:  {_fmt_cash(exp_r['ending_cash_balance'])}")
    print(f"  MC survival rate:      {mc.survival_rate:.1%}")
    print(f"  MC insolvency prob:    {mc.insolvency_probability:.1%}")
    print(f"  Audit errors:          {total_errors}")
    print(f"  Risk signals:          {total_signals} total, {critical_signals} critical")
    print()


    
if __name__ == "__main__":
    run_simulation()
