"""
audit.py — Automated financial model audit engine.

Runs integrity, consistency, and plausibility checks across:
  - Timeline arithmetic (accounting identities)
  - Assumption plausibility (industry benchmarks)
  - Scenario divergence (best/worst bounds)
  - Data completeness
  - Cash flow reconciliation
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Audit finding
# ---------------------------------------------------------------------------

@dataclass
class AuditFinding:
    code: str           # machine-readable identifier
    severity: str       # "error" | "warning" | "info"
    category: str       # "integrity" | "plausibility" | "consistency" | "completeness"
    title: str
    detail: str
    month: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "category": self.category,
            "title": self.title,
            "detail": self.detail,
            "month": self.month,
        }


# ---------------------------------------------------------------------------
# Industry benchmark ranges (adjustable)
# ---------------------------------------------------------------------------

BENCHMARKS = {
    "gross_margin_min": 0.10,        # < 10% gross margin is concerning
    "gross_margin_max": 0.99,
    "opex_ratio_max": 1.5,           # opex > 1.5× revenue is unusual
    "monthly_burn_max_pct": 0.30,    # burn > 30% of cash balance in one month
    "cogs_ratio_max": 0.90,          # COGS should not exceed 90% of revenue
    "revenue_month_over_month_max": 3.0,  # 3× month-over-month growth is suspicious
}


# ---------------------------------------------------------------------------
# Integrity checks (accounting identities)
# ---------------------------------------------------------------------------

def _check_accounting_identities(timeline: List[dict]) -> List[AuditFinding]:
    findings: List[AuditFinding] = []
    tolerance = 0.01  # $0.01 rounding tolerance

    for idx, m in enumerate(timeline):
        month_num = m.get("month", idx + 1)
        rev = m.get("revenue", 0)
        cogs = m.get("cogs", 0)
        gp = m.get("gross_profit", 0)
        oi = m.get("operating_income", 0)
        ncf = m.get("net_cash_flow", 0)

        # gross_profit = revenue − cogs
        expected_gp = rev - cogs
        if abs(gp - expected_gp) > tolerance:
            findings.append(AuditFinding(
                code="INT001",
                severity="error",
                category="integrity",
                title="Gross Profit Identity Violation",
                detail=(
                    f"Month {month_num}: gross_profit ({gp:.2f}) ≠ "
                    f"revenue ({rev:.2f}) − cogs ({cogs:.2f}) = {expected_gp:.2f}"
                ),
                month=month_num,
            ))

        # net_cash_flow should equal operating_income
        # (simplified model; flag large divergences)
        if abs(ncf - oi) > tolerance * 100:
            findings.append(AuditFinding(
                code="INT002",
                severity="warning",
                category="integrity",
                title="Cash Flow / Operating Income Divergence",
                detail=(
                    f"Month {month_num}: net_cash_flow ({ncf:.2f}) diverges from "
                    f"operating_income ({oi:.2f}) by {abs(ncf - oi):.2f}"
                ),
                month=month_num,
            ))

        # Cash balance must be non-decreasing when cash flow ≥ 0
        cash = m.get("cash_balance")
        if cash is not None and cash < 0 and ncf >= 0:
            findings.append(AuditFinding(
                code="INT003",
                severity="warning",
                category="integrity",
                title="Negative Cash Despite Positive Flow",
                detail=(
                    f"Month {month_num}: cash_balance is {cash:.2f} but "
                    f"net_cash_flow is {ncf:.2f} — possible prior deficit"
                ),
                month=month_num,
            ))

    return findings


def _check_cash_balance_continuity(timeline: List[dict], starting_cash: float) -> List[AuditFinding]:
    """Verify cumulative cash flow reconciles with reported cash balance."""
    findings: List[AuditFinding] = []
    running = starting_cash
    tolerance = 1.00  # $1 tolerance for floating-point accumulation

    for idx, m in enumerate(timeline):
        month_num = m.get("month", idx + 1)
        running += m.get("net_cash_flow", 0)
        reported = m.get("cash_balance")
        if reported is not None and abs(reported - running) > tolerance:
            findings.append(AuditFinding(
                code="INT004",
                severity="error",
                category="integrity",
                title="Cash Balance Continuity Break",
                detail=(
                    f"Month {month_num}: reported cash_balance ({reported:.2f}) does not "
                    f"reconcile with running cumulative total ({running:.2f}). "
                    f"Difference: {abs(reported - running):.2f}"
                ),
                month=month_num,
            ))
            running = reported  # re-anchor to avoid cascading errors

    return findings


# ---------------------------------------------------------------------------
# Plausibility checks (benchmarks)
# ---------------------------------------------------------------------------

def _check_plausibility(timeline: List[dict]) -> List[AuditFinding]:
    findings: List[AuditFinding] = []
    prev_revenue: Optional[float] = None

    for idx, m in enumerate(timeline):
        month_num = m.get("month", idx + 1)
        rev = m.get("revenue", 0)
        cogs = m.get("cogs", 0)
        gp = m.get("gross_profit", 0)
        cash = m.get("cash_balance", 0)
        ncf = m.get("net_cash_flow", 0)

        # Gross margin range
        if rev > 0:
            gm = gp / rev
            if gm < BENCHMARKS["gross_margin_min"]:
                findings.append(AuditFinding(
                    code="PLB001",
                    severity="warning",
                    category="plausibility",
                    title="Very Low Gross Margin",
                    detail=f"Month {month_num}: gross margin {gm:.1%} is below {BENCHMARKS['gross_margin_min']:.0%}",
                    month=month_num,
                ))
            if cogs / rev > BENCHMARKS["cogs_ratio_max"]:
                findings.append(AuditFinding(
                    code="PLB002",
                    severity="warning",
                    category="plausibility",
                    title="Exceptionally High COGS Ratio",
                    detail=f"Month {month_num}: COGS is {cogs/rev:.1%} of revenue",
                    month=month_num,
                ))

            # Revenue growth spike
            if prev_revenue is not None and prev_revenue > 0:
                growth = rev / prev_revenue
                if growth > BENCHMARKS["revenue_month_over_month_max"]:
                    findings.append(AuditFinding(
                        code="PLB003",
                        severity="warning",
                        category="plausibility",
                        title="Implausible Revenue Jump",
                        detail=(
                            f"Month {month_num}: revenue grew {growth:.1f}× month-over-month "
                            f"({prev_revenue:.0f} → {rev:.0f})"
                        ),
                        month=month_num,
                    ))

        # Single-month burn vs cash balance
        burn = -ncf
        if burn > 0 and cash > 0 and (burn / cash) > BENCHMARKS["monthly_burn_max_pct"]:
            findings.append(AuditFinding(
                code="PLB004",
                severity="warning",
                category="plausibility",
                title="High Burn-to-Cash Ratio",
                detail=(
                    f"Month {month_num}: burning {burn/cash:.0%} of remaining cash "
                    f"(burn={burn:.0f}, cash={cash:.0f})"
                ),
                month=month_num,
            ))

        if rev > 0:
            prev_revenue = rev

    return findings


# ---------------------------------------------------------------------------
# Completeness checks
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = ["revenue", "cogs", "gross_profit", "operating_income", "net_cash_flow"]
RECOMMENDED_FIELDS = ["cash_balance", "runway_months"]


def _check_completeness(timeline: List[dict]) -> List[AuditFinding]:
    findings: List[AuditFinding] = []

    if not timeline:
        findings.append(AuditFinding(
            code="CMP000",
            severity="error",
            category="completeness",
            title="Empty Timeline",
            detail="Timeline contains no months.",
        ))
        return findings

    if len(timeline) < 12:
        findings.append(AuditFinding(
            code="CMP001",
            severity="warning",
            category="completeness",
            title="Short Simulation Horizon",
            detail=f"Timeline covers only {len(timeline)} months (recommended: 36)",
        ))

    for idx, m in enumerate(timeline):
        month_num = m.get("month", idx + 1)
        for f in REQUIRED_FIELDS:
            if f not in m or m[f] is None:
                findings.append(AuditFinding(
                    code="CMP002",
                    severity="error",
                    category="completeness",
                    title=f"Missing Required Field: {f}",
                    detail=f"Month {month_num} is missing '{f}'",
                    month=month_num,
                ))
        for f in RECOMMENDED_FIELDS:
            if f not in m or m[f] is None:
                findings.append(AuditFinding(
                    code="CMP003",
                    severity="info",
                    category="completeness",
                    title=f"Missing Recommended Field: {f}",
                    detail=f"Month {month_num} is missing '{f}'",
                    month=month_num,
                ))

    return findings


# ---------------------------------------------------------------------------
# Scenario consistency checks
# ---------------------------------------------------------------------------

def _check_scenario_consistency(timeline_map: Dict[str, List[dict]]) -> List[AuditFinding]:
    """
    Verify that BEST ≥ EXPECTED ≥ WORST for key financial metrics
    in at least the majority of months.
    """
    findings: List[AuditFinding] = []
    best = timeline_map.get("BEST", [])
    expected = timeline_map.get("EXPECTED", [])
    worst = timeline_map.get("WORST", [])

    if not (best and expected and worst):
        return findings

    n = min(len(best), len(expected), len(worst))
    violations = {"revenue": 0, "net_cash_flow": 0}

    for i in range(n):
        for metric in ["revenue", "net_cash_flow"]:
            b = best[i].get(metric, 0)
            e = expected[i].get(metric, 0)
            w = worst[i].get(metric, 0)
            if not (b >= e >= w):
                violations[metric] += 1

    for metric, count in violations.items():
        if count > n * 0.10:  # > 10% of months violate ordering
            findings.append(AuditFinding(
                code="CON001",
                severity="warning",
                category="consistency",
                title=f"Scenario Ordering Violation: {metric}",
                detail=(
                    f"BEST ≥ EXPECTED ≥ WORST ordering for '{metric}' is violated "
                    f"in {count}/{n} months ({count/n:.0%}). "
                    "Check event multipliers and scenario profiles."
                ),
            ))

    # Check that scenarios diverge (non-trivial scenario spread)
    for metric in ["ending_cash"]:
        last_best = best[-1].get("cash_balance", 0) if best else 0
        last_exp  = expected[-1].get("cash_balance", 0) if expected else 0
        last_worst = worst[-1].get("cash_balance", 0) if worst else 0
        if abs(last_best - last_worst) < 100:
            findings.append(AuditFinding(
                code="CON002",
                severity="info",
                category="consistency",
                title="Minimal Scenario Divergence",
                detail=(
                    f"BEST and WORST ending cash are nearly identical "
                    f"({last_best:.0f} vs {last_worst:.0f}). "
                    "Consider reviewing scenario multipliers."
                ),
            ))

    return findings


# ---------------------------------------------------------------------------
# Main audit runner
# ---------------------------------------------------------------------------

@dataclass
class AuditReport:
    scenario: str
    total_findings: int
    errors: int
    warnings: int
    infos: int
    findings: List[AuditFinding]
    passed: bool   # True if zero errors

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "total_findings": self.total_findings,
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
            "passed": self.passed,
            "findings": [f.to_dict() for f in self.findings],
        }

    def summary_line(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return (
            f"{status} [{self.scenario}] — "
            f"{self.errors} error(s), {self.warnings} warning(s), {self.infos} info(s)"
        )


def run_audit(
    timeline: List[dict],
    starting_cash: float,
    scenario_name: str = "EXPECTED",
) -> AuditReport:
    """Run all single-timeline audit checks and return a report."""
    findings: List[AuditFinding] = []
    findings += _check_completeness(timeline)
    findings += _check_accounting_identities(timeline)
    findings += _check_cash_balance_continuity(timeline, starting_cash)
    findings += _check_plausibility(timeline)

    # Sort: errors first, then warnings, then info; then by month
    findings.sort(key=lambda f: (
        {"error": 0, "warning": 1, "info": 2}.get(f.severity, 3),
        f.month or 999,
    ))

    errors   = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    infos    = sum(1 for f in findings if f.severity == "info")

    return AuditReport(
        scenario=scenario_name,
        total_findings=len(findings),
        errors=errors,
        warnings=warnings,
        infos=infos,
        findings=findings,
        passed=(errors == 0),
    )


def run_full_audit(
    timeline_map: Dict[str, List[dict]],
    starting_cash: float,
) -> Dict[str, AuditReport]:
    """
    Run audits for all scenarios plus cross-scenario consistency check.
    Returns a mapping of scenario_name → AuditReport.
    """
    reports: Dict[str, AuditReport] = {}

    for scenario_name, timeline in timeline_map.items():
        reports[scenario_name] = run_audit(timeline, starting_cash, scenario_name)

    # Cross-scenario consistency (stored under special key)
    consistency_findings = _check_scenario_consistency(timeline_map)
    if consistency_findings:
        errors   = sum(1 for f in consistency_findings if f.severity == "error")
        warnings = sum(1 for f in consistency_findings if f.severity == "warning")
        infos    = sum(1 for f in consistency_findings if f.severity == "info")
        reports["_CROSS_SCENARIO"] = AuditReport(
            scenario="_CROSS_SCENARIO",
            total_findings=len(consistency_findings),
            errors=errors,
            warnings=warnings,
            infos=infos,
            findings=consistency_findings,
            passed=(errors == 0),
        )

    return reports
