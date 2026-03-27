def generate_alerts(timeline):
    alerts = []

    for month in timeline:
        m = month["month"]

        if month.get("runway_months", 999) < 6:
            alerts.append({
                "type": "warning",
                "message": f"Low runway (<6 months) at month {m}"
            })

        if month.get("cash_balance", 0) < 0:
            alerts.append({
                "type": "critical",
                "message": f"Insolvency at month {m}"
            })

        if month["net_cash_flow"] < 0:
            alerts.append({
                "type": "info",
                "message": f"Negative cash flow at month {m}"
            })

    return alerts
