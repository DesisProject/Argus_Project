"""
resilience.py — Financial resilience scoring engine.
Grades survivability across simulation horizons with industry benchmarks.
"""

from __future__ import annotations
from typing import List, Optional

# ---------------------------------------------------------------------------
# Grade definitions
# ---------------------------------------------------------------------------

GRADE_DETAILS: dict[str, dict] = {
    "O": {
        "score": 100,
        "label": "Outstanding",
        "description": "Survives the full simulation horizon with a strong cash cushion",
        "min_runway_months": None,   # horizon-length check handled separately
        "min_cash_cushion_months": 12,
    },
    "A": {
        "score": 90,
        "label": "Excellent",
        "description": "Survives the full simulation horizon with adequate stability",
        "min_runway_months": None,
        "min_cash_cushion_months": 0,
    },
    "B": {
        "score": 75,
        "label": "Good",
        "description": "Strong survivability, but vulnerable beyond two years",
        "min_runway_months": 24,
        "min_cash_cushion_months": 0,
    },
    "C": {
        "score": 60,
        "label": "Fair",
        "description": "Moderate survivability — fundraising or cost reduction likely needed",
        "min_runway_months": 12,
        "min_cash_cushion_months": 0,
    },
    "D": {
        "score": 40,
        "label": "Poor",
        "description": "Limited survivability — immediate action needed",
        "min_runway_months": 1,
        "min_cash_cushion_months": 0,
    },
    "F": {
        "score": 0,
        "label": "Critical",
        "description": "Cash flow negative — urgent intervention required",
        "min_runway_months": 0,
        "min_cash_cushion_months": 0,
    },
}

GRADE_RANK: dict[str, int] = {g: i for i, g in enumerate(["F", "D", "C", "B", "A", "O"])}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _average_monthly_burn(timeline: List[dict]) -> float:
    burns = [abs(m.get("net_cash_flow", 0)) for m in timeline if m.get("net_cash_flow", 0) < 0]
    return sum(burns) / len(burns) if burns else 0.0


def _peak_monthly_burn(timeline: List[dict]) -> float:
    burns = [abs(m.get("net_cash_flow", 0)) for m in timeline if m.get("net_cash_flow", 0) < 0]
    return max(burns) if burns else 0.0


def _months_cash_flow_positive(timeline: List[dict]) -> int:
    return sum(1 for m in timeline if m.get("net_cash_flow", 0) >= 0)


def _gross_margin_trend(timeline: List[dict]) -> Optional[str]:
    """Detect if gross margin is improving, declining, or flat over the horizon."""
    margins = []
    for m in timeline:
        rev = m.get("revenue", 0)
        gp = m.get("gross_profit", 0)
        if rev > 0:
            margins.append(gp / rev)
    if len(margins) < 6:
        return None
    first_half = sum(margins[: len(margins) // 2]) / (len(margins) // 2)
    second_half = sum(margins[len(margins) // 2 :]) / (len(margins) - len(margins) // 2)
    diff = second_half - first_half
    if diff > 0.02:
        return "improving"
    if diff < -0.02:
        return "declining"
    return "flat"


def _calculate_grade(
    runway_months: float,
    min_cash_balance: float,
    horizon_months: int,
    average_monthly_burn: float,
    cash_cushion_months: float,
) -> str:
    if runway_months >= horizon_months and min_cash_balance >= 0:
        if average_monthly_burn == 0 or cash_cushion_months >= 12:
            return "O"
        return "A"
    if runway_months >= 36:
        return "B"
    if runway_months >= 12:
        return "C"
    if runway_months > 0:
        return "D"
    return "F"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def summarize_resilience(timeline: List[dict]) -> dict:
    """
    Compute a full resilience summary for a single scenario timeline.
    Returns grade, score, runway, insolvency month, and extended metrics.
    """
    if not timeline:
        details = GRADE_DETAILS["F"]
        return {
            "grade": "F",
            "score": details["score"],
            "label": details["label"],
            "description": "No simulation data available",
            "runway_months": 0,
            "insolvency_month": None,
            "min_cash_balance": 0,
            "ending_cash_balance": 0,
            "survives_horizon": False,
            "simulation_horizon_months": 0,
            "average_monthly_burn": 0,
            "peak_monthly_burn": 0,
            "cash_cushion_months": 0,
            "months_cash_flow_positive": 0,
            "gross_margin_trend": None,
        }

    cash_balances = [m.get("cash_balance", 0) for m in timeline]
    min_cash_balance = min(cash_balances)
    ending_cash_balance = cash_balances[-1]
    horizon_months = len(timeline)

    insolvency_month: Optional[int] = next(
        (idx + 1 for idx, cash in enumerate(cash_balances) if cash < 0),
        None,
    )
    survives_horizon = insolvency_month is None
    runway_months = horizon_months if survives_horizon else max(insolvency_month - 1, 0)

    avg_burn = _average_monthly_burn(timeline)
    peak_burn = _peak_monthly_burn(timeline)

    if avg_burn > 0 and min_cash_balance > 0:
        cash_cushion_months = min_cash_balance / avg_burn
    elif avg_burn == 0 and min_cash_balance >= 0:
        cash_cushion_months = float(horizon_months)
    else:
        cash_cushion_months = 0.0

    grade = _calculate_grade(runway_months, min_cash_balance, horizon_months, avg_burn, cash_cushion_months)
    details = GRADE_DETAILS[grade]

    return {
        "grade": grade,
        "score": details["score"],
        "label": details["label"],
        "description": details["description"],
        "runway_months": runway_months,
        "insolvency_month": insolvency_month,
        "min_cash_balance": min_cash_balance,
        "ending_cash_balance": ending_cash_balance,
        "survives_horizon": survives_horizon,
        "simulation_horizon_months": horizon_months,
        "average_monthly_burn": avg_burn,
        "peak_monthly_burn": peak_burn,
        "cash_cushion_months": cash_cushion_months,
        "months_cash_flow_positive": _months_cash_flow_positive(timeline),
        "gross_margin_trend": _gross_margin_trend(timeline),
    }


def compare_resilience_grades(baseline_grade: str, scenario_grade: str) -> dict:
    """Return grade drop severity and a human label."""
    drop = GRADE_RANK.get(baseline_grade, 0) - GRADE_RANK.get(scenario_grade, 0)
    if drop <= 0:
        severity = "none"
    elif drop == 1:
        severity = "minor"
    elif drop == 2:
        severity = "moderate"
    else:
        severity = "severe"
    return {"grade_drop": drop, "severity": severity}
