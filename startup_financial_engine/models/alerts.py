def generate_alerts(timeline):
    alerts = []
    seen = set() 

    for month in timeline:
        m = month["month"]

        if month.get("runway_months", 999) < 6:
            msg = f"Low runway (<6 months) at month {m}"
            if msg not in seen:
                alerts.append({"type": "warning", "message": msg})
                seen.add(msg)

        if month.get("cash_balance", 0) < 0:
            msg = f"Insolvency at month {m}"
            if msg not in seen:
                alerts.append({"type": "critical", "message": msg})
                seen.add(msg)

        if month["net_cash_flow"] < 0:
            msg = f"Negative cash flow at month {m}"
            if msg not in seen:
                alerts.append({"type": "info", "message": msg})
                seen.add(msg)

    return alerts