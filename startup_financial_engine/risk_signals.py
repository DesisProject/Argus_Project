"""
risk_signals.py — Automated risk signal detection engine.
Detects timeline anomalies, fragility, burn acceleration, and margin erosion.
"""

from __future__ import annotations
from typing import List, Optional, Tuple
from resilience import GRADE_RANK


# ---------------------------------------------------------------------------
# Signal builder
# ---------------------------------------------------------------------------

def _signal(signal_type: str, level: str, title: str, message: str, month: Optional[int] = None) -> dict:
    payload = {
        "type": signal_type,
        "level": level,          # "critical" | "warning" | "info"
        "title": title,
        "message": message,
    }
    if month is not None:
        payload["month"] = month
    return payload


def sort_risk_signals(signals: List[dict]) -> List[dict]:
    signals.sort(
        key=lambda s: (
            {"critical": 0, "warning": 1, "info": 2}.get(s["level"], 3),
            s.get("month", 999),
            s["title"],
        )
    )
    return signals


# ---------------------------------------------------------------------------
# Timeline helpers
# ---------------------------------------------------------------------------

def _month_number(month_data: dict, month_index: int) -> int:
    return int(month_data.get("month", month_index + 1))


def _first_low_runway_month(timeline: List[dict], threshold: float) -> Tuple[Optional[int], Optional[float]]:
    for idx, month in enumerate(timeline):
        rw = month.get("runway_months")
        if rw is not None and rw < threshold:
            return _month_number(month, idx), rw
    return None, None


def _longest_negative_cash_flow_streak(timeline: List[dict]) -> Tuple[Optional[int], int]:
    longest_start = current_start = None
    longest_len = current_len = 0
    for idx, month in enumerate(timeline):
        if month.get("net_cash_flow", 0) < 0:
            if current_start is None:
                current_start = _month_number(month, idx)
            current_len += 1
            if current_len > longest_len:
                longest_start, longest_len = current_start, current_len
        else:
            current_start, current_len = None, 0
    return longest_start, longest_len


def _detect_burn_acceleration(timeline: List[dict], window: int = 3) -> Optional[Tuple[int, float]]:
    """
    Returns (month, acceleration_pct) if burn rate accelerates > 25% over
    any rolling `window`-month period.
    """
    burns = [abs(m.get("net_cash_flow", 0)) if m.get("net_cash_flow", 0) < 0 else 0 for m in timeline]
    for i in range(window, len(burns)):
        prev_avg = sum(burns[i - window : i]) / window
        if prev_avg > 0:
            accel = (burns[i] - prev_avg) / prev_avg
            if accel > 0.25:
                return _month_number(timeline[i], i), round(accel * 100, 1)
    return None


def _detect_margin_erosion(timeline: List[dict], drop_threshold: float = 0.05) -> Optional[Tuple[int, float]]:
    """
    Returns (month, margin_drop) if gross margin falls more than
    `drop_threshold` in any single month vs. the prior month.
    """
    prev_margin: Optional[float] = None
    for idx, month in enumerate(timeline):
        rev = month.get("revenue", 0)
        gp = month.get("gross_profit", 0)
        margin = gp / rev if rev > 0 else None
        if margin is not None and prev_margin is not None:
            drop = prev_margin - margin
            if drop >= drop_threshold:
                return _month_number(month, idx), round(drop * 100, 1)
        if margin is not None:
            prev_margin = margin
    return None


def _detect_cash_cliff(timeline: List[dict], pct_threshold: float = 0.40) -> Optional[Tuple[int, float]]:
    """
    Returns (month, drop_pct) if cash balance drops > 40% in a single month.
    """
    prev_cash: Optional[float] = None
    for idx, month in enumerate(timeline):
        cash = month.get("cash_balance")
        if cash is None:
            continue
        if prev_cash is not None and prev_cash > 0:
            drop = (prev_cash - cash) / prev_cash
            if drop >= pct_threshold:
                return _month_number(month, idx), round(drop * 100, 1)
        prev_cash = cash
    return None


def _detect_revenue_stall(timeline: List[dict], window: int = 3, growth_threshold: float = 0.0) -> Optional[int]:
    """
    Returns the first month where rolling average revenue growth
    is flat or negative for `window` consecutive months.
    """
    revenues = [m.get("revenue", 0) for m in timeline]
    stall_count = 0
    for i in range(1, len(revenues)):
        growth = revenues[i] - revenues[i - 1]
        if growth <= growth_threshold:
            stall_count += 1
            if stall_count >= window:
                return _month_number(timeline[i], i)
        else:
            stall_count = 0
    return None


# ---------------------------------------------------------------------------
# Primary detection functions
# ---------------------------------------------------------------------------

def detect_timeline_risk_signals(timeline: List[dict], resilience_summary: dict) -> List[dict]:
    """
    Full automated scan of a single scenario timeline.
    Returns a sorted list of risk signals.
    """
    signals: List[dict] = []

    # 1. Insolvency
    insolvency_month = resilience_summary.get("insolvency_month")
    if insolvency_month is not None:
        signals.append(_signal(
            "critical_insolvency_risk", "critical",
            "Critical Insolvency Risk",
            f"Cash balance turns negative in month {insolvency_month}.",
            insolvency_month,
        ))

    # 2. Runway warnings
    low_rw_month, low_rw_value = _first_low_runway_month(timeline, 6)
    if low_rw_month is not None:
        if low_rw_value < 3:
            signals.append(_signal(
                "critical_runway_risk", "critical",
                "Critical Runway Risk",
                f"Runway falls below 3 months in month {low_rw_month}.",
                low_rw_month,
            ))
        else:
            signals.append(_signal(
                "low_runway_warning", "warning",
                "Low Runway Warning",
                f"Runway falls below 6 months in month {low_rw_month}.",
                low_rw_month,
            ))

    # 3. Sustained negative cash flow
    streak_start, streak_len = _longest_negative_cash_flow_streak(timeline)
    if streak_len >= 3:
        level = "critical" if streak_len >= 6 else "warning"
        signals.append(_signal(
            "sustained_negative_cash_flow", level,
            "Sustained Negative Cash Flow",
            f"Net cash flow remains negative for {streak_len} consecutive months "
            f"starting in month {streak_start}.",
            streak_start,
        ))

    # 4. Burn acceleration
    accel = _detect_burn_acceleration(timeline)
    if accel is not None:
        month, pct = accel
        signals.append(_signal(
            "burn_acceleration", "warning",
            "Burn Rate Acceleration",
            f"Monthly burn accelerated by {pct}% vs. prior 3-month average in month {month}.",
            month,
        ))

    # 5. Gross margin erosion
    erosion = _detect_margin_erosion(timeline)
    if erosion is not None:
        month, pct = erosion
        signals.append(_signal(
            "margin_erosion", "warning",
            "Gross Margin Erosion",
            f"Gross margin dropped {pct} percentage points in month {month}.",
            month,
        ))

    # 6. Cash cliff
    cliff = _detect_cash_cliff(timeline)
    if cliff is not None:
        month, pct = cliff
        signals.append(_signal(
            "cash_cliff", "critical",
            "Cash Cliff Detected",
            f"Cash balance fell {pct}% in a single month (month {month}).",
            month,
        ))

    # 7. Revenue stall
    stall_month = _detect_revenue_stall(timeline)
    if stall_month is not None:
        signals.append(_signal(
            "revenue_stall", "warning",
            "Revenue Growth Stall",
            f"Revenue growth flat or declining for 3+ consecutive months from month {stall_month}.",
            stall_month,
        ))

    return sort_risk_signals(signals)


def detect_fragility_signal(
    baseline_resilience: dict,
    target_resilience: dict,
    target_name: str,
) -> Optional[dict]:
    """
    Emit a fragility signal when a scenario or downside case
    drops 2+ grade levels vs. baseline.
    """
    baseline_grade = baseline_resilience.get("grade", "F")
    target_grade = target_resilience.get("grade", "F")
    grade_drop = GRADE_RANK.get(baseline_grade, 0) - GRADE_RANK.get(target_grade, 0)

    if grade_drop < 2:
        return None

    insolvency_month = target_resilience.get("insolvency_month")
    if insolvency_month is not None:
        message = (
            f"{target_name} resilience drops from {baseline_grade} to {target_grade}, "
            f"with insolvency in month {insolvency_month}."
        )
    else:
        message = (
            f"{target_name} resilience drops from {baseline_grade} to {target_grade}, "
            "indicating high downside sensitivity."
        )

    level = "critical" if target_grade in {"D", "F"} else "warning"
    title = "Scenario Fragility" if target_name == "Scenario" else "Downside Fragility"

    return _signal("scenario_fragility", level, title, message, insolvency_month)


def detect_all_scenario_signals(
    scenario_timelines: dict[str, List[dict]],
    scenario_resilience: dict[str, dict],
    baseline_key: str = "EXPECTED",
) -> dict[str, List[dict]]:
    """
    Run full signal detection across all scenario timelines.
    Returns a mapping of scenario_name → signals list.
    Also injects cross-scenario fragility signals into WORST/BEST.
    """
    all_signals: dict[str, List[dict]] = {}
    baseline_resilience = scenario_resilience.get(baseline_key, {})

    for scenario_name, timeline in scenario_timelines.items():
        resilience = scenario_resilience.get(scenario_name, {})
        signals = detect_timeline_risk_signals(timeline, resilience)

        # Cross-scenario fragility check (skip baseline vs itself)
        if scenario_name != baseline_key:
            frag = detect_fragility_signal(baseline_resilience, resilience, scenario_name)
            if frag:
                signals.append(frag)
                signals = sort_risk_signals(signals)

        all_signals[scenario_name] = signals

    return all_signals
