GRADE_DETAILS = {
    "O": {
        "score": 100,
        "label": "Outstanding",
        "description": "Survives the full simulation horizon with a strong cash cushion",
    },
    "A": {
        "score": 90,
        "label": "Excellent",
        "description": "Survives the full simulation horizon with adequate stability",
    },
    "B": {
        "score": 75,
        "label": "Good",
        "description": "Strong survivability, but vulnerable beyond two years",
    },
    "C": {
        "score": 60,
        "label": "Fair",
        "description": "Moderate survivability - fundraising or cost reduction likely needed",
    },
    "D": {
        "score": 40,
        "label": "Poor",
        "description": "Limited survivability - immediate action needed",
    },
    "F": {
        "score": 0,
        "label": "Critical",
        "description": "Cash flow negative - urgent intervention required",
    },
}


def _calculate_average_monthly_burn(timeline):
    burn_values = [
        abs(month.get("net_cash_flow", 0))
        for month in timeline
        if month.get("net_cash_flow", 0) < 0
    ]
    if not burn_values:
        return 0.0
    return sum(burn_values) / len(burn_values)


def calculate_resilience_grade(
    runway_months,
    min_cash_balance,
    horizon_months,
    average_monthly_burn,
    cash_cushion_months,
):
    if runway_months >= horizon_months and min_cash_balance >= 0:
        if average_monthly_burn == 0 or cash_cushion_months >= 12:
            return "O"
        return "A"
    if runway_months >= 24:
        return "B"
    if runway_months >= 12:
        return "C"
    if runway_months > 0:
        return "D"
    return "F"


def summarize_resilience(timeline):
    if not timeline:
        return {
            "grade": "F",
            "score": GRADE_DETAILS["F"]["score"],
            "label": GRADE_DETAILS["F"]["label"],
            "description": "No simulation data available",
            "runway_months": 0,
            "insolvency_month": None,
            "min_cash_balance": 0,
            "ending_cash_balance": 0,
            "survives_horizon": False,
            "simulation_horizon_months": 0,
            "average_monthly_burn": 0,
            "cash_cushion_months": 0,
        }

    cash_balances = [month.get("cash_balance", 0) for month in timeline]
    min_cash_balance = min(cash_balances)
    ending_cash_balance = cash_balances[-1]
    insolvency_month = next(
        (index + 1 for index, cash in enumerate(cash_balances) if cash < 0),
        None,
    )
    survives_horizon = insolvency_month is None
    horizon_months = len(timeline)
    runway_months = horizon_months if survives_horizon else max(insolvency_month - 1, 0)
    average_monthly_burn = _calculate_average_monthly_burn(timeline)
    if average_monthly_burn > 0 and min_cash_balance > 0:
        cash_cushion_months = min_cash_balance / average_monthly_burn
    elif average_monthly_burn == 0 and min_cash_balance >= 0:
        cash_cushion_months = horizon_months
    else:
        cash_cushion_months = 0

    grade = calculate_resilience_grade(
        runway_months,
        min_cash_balance,
        horizon_months,
        average_monthly_burn,
        cash_cushion_months,
    )
    grade_details = GRADE_DETAILS[grade]

    return {
        "grade": grade,
        "score": grade_details["score"],
        "label": grade_details["label"],
        "description": grade_details["description"],
        "runway_months": runway_months,
        "insolvency_month": insolvency_month,
        "min_cash_balance": min_cash_balance,
        "ending_cash_balance": ending_cash_balance,
        "survives_horizon": survives_horizon,
        "simulation_horizon_months": horizon_months,
        "average_monthly_burn": average_monthly_burn,
        "cash_cushion_months": cash_cushion_months,
    }
