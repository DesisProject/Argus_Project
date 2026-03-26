GRADE_RANK = {
    "F": 0,
    "D": 1,
    "C": 2,
    "B": 3,
    "A": 4,
    "O": 5,
}


def _signal(signal_type, level, title, message, month=None):
    payload = {
        "type": signal_type,
        "level": level,
        "title": title,
        "message": message,
    }
    if month is not None:
        payload["month"] = month
    return payload


def sort_risk_signals(signals):
    signals.sort(
        key=lambda signal: (
            0 if signal["level"] == "critical" else 1,
            signal.get("month", 999),
            signal["title"],
        )
    )
    return signals


def _month_number(month_data, month_index):
    return int(month_data.get("month", month_index + 1))


def _first_low_runway_month(timeline, threshold_months):
    for month_index, month_data in enumerate(timeline):
        runway_months = month_data.get("runway_months")
        if runway_months is not None and runway_months < threshold_months:
            return _month_number(month_data, month_index), runway_months
    return None, None


def _longest_negative_cash_flow_streak(timeline):
    longest_start = None
    longest_length = 0
    current_start = None
    current_length = 0

    for month_index, month_data in enumerate(timeline):
        if month_data.get("net_cash_flow", 0) < 0:
            if current_start is None:
                current_start = _month_number(month_data, month_index)
            current_length += 1
            if current_length > longest_length:
                longest_start = current_start
                longest_length = current_length
        else:
            current_start = None
            current_length = 0

    return longest_start, longest_length


def detect_timeline_risk_signals(timeline, resilience_summary):
    signals = []
    insolvency_month = resilience_summary.get("insolvency_month")

    if insolvency_month is not None:
        signals.append(
            _signal(
                "critical_insolvency_risk",
                "critical",
                "Critical Insolvency Risk",
                f"Cash balance turns negative in month {insolvency_month}.",
                insolvency_month,
            )
        )

    low_runway_month, low_runway_value = _first_low_runway_month(timeline, 6)
    if low_runway_month is not None:
        if low_runway_value < 3:
            signals.append(
                _signal(
                    "critical_runway_risk",
                    "critical",
                    "Critical Runway Risk",
                    f"Runway falls below 3 months in month {low_runway_month}.",
                    low_runway_month,
                )
            )
        else:
            signals.append(
                _signal(
                    "low_runway_warning",
                    "warning",
                    "Low Runway Warning",
                    f"Runway falls below 6 months in month {low_runway_month}.",
                    low_runway_month,
                )
            )

    streak_start, streak_length = _longest_negative_cash_flow_streak(timeline)
    if streak_length >= 3:
        level = "critical" if streak_length >= 6 else "warning"
        signals.append(
            _signal(
                "sustained_negative_cash_flow",
                level,
                "Sustained Negative Cash Flow",
                (
                    f"Net cash flow remains negative for {streak_length} consecutive "
                    f"months starting in month {streak_start}."
                ),
                streak_start,
            )
        )

    return sort_risk_signals(signals)


def detect_fragility_signal(baseline_resilience, target_resilience, target_name):
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

    return _signal(
        "scenario_fragility",
        level,
        title,
        message,
        insolvency_month,
    )
