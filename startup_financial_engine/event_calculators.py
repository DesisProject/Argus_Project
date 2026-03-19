def calculate_hiring_impact(timeline_map, payload):
    """Specific math for headcount addition."""
    start_month = payload.get("start_month", 1)
    salary = payload.get("recurring_cost", 0)
    recruiting_fee = payload.get("upfront_cost", 0)

    for month_index in range(36):
        current_month = month_index + 1
        if current_month >= start_month:
            for timeline in timeline_map.values():
                timeline[month_index]["operating_income"] -= salary
                timeline[month_index]["net_cash_flow"] -= salary
                if current_month == start_month:
                    timeline[month_index]["operating_income"] -= recruiting_fee
                    timeline[month_index]["net_cash_flow"] -= recruiting_fee

            # BEST: Immediate high ROI
            timeline_map["BEST"][month_index]["operating_income"] += (salary * 3) 
            # EXPECTED: 2-month ramp-up
            if current_month >= start_month + 2:
                timeline_map["EXPECTED"][month_index]["operating_income"] += (salary * 1.5)

def calculate_expansion_impact(timeline_map, payload):
    """Specific math for a new location/infrastructure."""
    start_month = payload.get("start_month", 1)
    buildout_cost = payload.get("upfront_cost", 0)
    new_rent = payload.get("recurring_cost", 0)

    for month_index in range(36):
        current_month = month_index + 1
        if current_month >= start_month:
            for timeline in timeline_map.values():
                timeline[month_index]["operating_income"] -= new_rent
                timeline[month_index]["net_cash_flow"] -= new_rent
                if current_month == start_month:
                    timeline[month_index]["operating_income"] -= buildout_cost
                    timeline[month_index]["net_cash_flow"] -= buildout_cost

            # High delay for Expansion returns
            if current_month >= start_month + 4:
                timeline_map["BEST"][month_index]["operating_income"] += 45000
            if current_month >= start_month + 6:
                timeline_map["EXPECTED"][month_index]["operating_income"] += 20000

def apply_event_wrapper(timeline_map, event_type, event_payload):
    """Main Dispatcher: Routes the event to the correct math function."""
    if not event_type or not event_payload:
        return

    event = event_type.lower()
    if event == "hiring":
        calculate_hiring_impact(timeline_map, event_payload)
    elif event == "expansion":
        calculate_expansion_impact(timeline_map, event_payload)