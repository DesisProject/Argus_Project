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

    # Normalize the event type to match the frontend 'type' strings
    event = event_type.lower()
    
    # Map 'hire' from frontend to hiring calculator
    if event in ["hiring", "hire"]:
        calculate_hiring_impact(timeline_map, event_payload)
    
    # Map 'expand' from frontend to expansion calculator
    elif event in ["expansion", "expand"]:
        calculate_expansion_impact(timeline_map, event_payload)
        
    # Add handlers for other frontend types to ensure they affect the graph
    elif event == "marketing":
        calculate_marketing_impact(timeline_map, event_payload)
        
    elif event == "reduce":
        calculate_cost_reduction_impact(timeline_map, event_payload)

    elif event == "inventory":
        calculate_inventory_impact(timeline_map, event_payload)

def calculate_marketing_impact(timeline_map, payload):
    """Simple math for marketing campaigns."""
    start_month = payload.get("startMonth", 1)
    cost = payload.get("impact", 0) # Negative value from frontend
    
    for month_index in range(len(timeline_map["EXPECTED"])):
        if month_index + 1 >= start_month:
            for timeline in timeline_map.values():
                # Apply the cost (which is negative in the library)
                timeline[month_index]["operating_income"] += cost
                timeline[month_index]["net_cash_flow"] += cost

def calculate_cost_reduction_impact(timeline_map, payload):
    """Math for reducing fixed costs."""
    start_month = payload.get("startMonth", 1)
    savings = abs(payload.get("impact", 0))
    
    for month_index in range(len(timeline_map["EXPECTED"])):
        if month_index + 1 >= start_month:
            for timeline in timeline_map.values():
                timeline[month_index]["operating_income"] += savings
                timeline[month_index]["net_cash_flow"] += savings

def calculate_inventory_impact(timeline_map, payload):
    start_month = payload.get("startMonth", 1)
    upfront = payload.get("upfront_cost", 0)
    savings = abs(payload.get("impact", 0))

    for month_index in range(len(timeline_map["EXPECTED"])):
        current_month = month_index + 1

        for timeline in timeline_map.values():

            # Apply upfront cost only once
            if current_month == start_month:
                timeline[month_index]["operating_income"] -= upfront
                timeline[month_index]["net_cash_flow"] -= upfront

            # Apply savings AFTER purchase
            if current_month > start_month:
                timeline[month_index]["operating_income"] += savings
                timeline[month_index]["net_cash_flow"] += savings
