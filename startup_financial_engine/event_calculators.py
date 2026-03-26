def _payload_value(payload, *keys, default=0):
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def _normalize_duration(duration_value):
    if duration_value in (None, "", "permanent"):
        return None
    return int(duration_value)


def _is_active_month(current_month, start_month, duration_months):
    if current_month < start_month:
        return False
    if duration_months is None:
        return True
    return current_month < start_month + duration_months


def _scenario_ramp_factor(current_month, effect_start_month, ramp_months):
    if current_month < effect_start_month:
        return 0.0
    ramp_months = max(int(ramp_months), 1)
    months_active = current_month - effect_start_month + 1
    return min(months_active / ramp_months, 1.0)


def calculate_hiring_impact(timeline_map, payload):
    """Specific math for headcount addition."""
    start_month = _payload_value(payload, "start_month", "startMonth", default=1)
    salary = _payload_value(payload, "recurring_cost", default=0)
    if not salary:
        salary = abs(min(_payload_value(payload, "impact", default=0), 0))
    recruiting_fee = _payload_value(payload, "upfront_cost", default=0)

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
            timeline_map["BEST"][month_index]["net_cash_flow"] += (salary * 3)
            # EXPECTED: 2-month ramp-up
            if current_month >= start_month + 2:
                timeline_map["EXPECTED"][month_index]["operating_income"] += (salary * 1.5)
                timeline_map["EXPECTED"][month_index]["net_cash_flow"] += (salary * 1.5)

def calculate_expansion_impact(timeline_map, payload):
    """Specific math for a new location/infrastructure."""
    start_month = _payload_value(payload, "start_month", "startMonth", default=1)
    buildout_cost = _payload_value(payload, "upfront_cost", default=0)
    new_rent = _payload_value(payload, "recurring_cost", default=0)

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
                timeline_map["BEST"][month_index]["net_cash_flow"] += 45000
            if current_month >= start_month + 6:
                timeline_map["EXPECTED"][month_index]["operating_income"] += 20000
                timeline_map["EXPECTED"][month_index]["net_cash_flow"] += 20000

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
    """Marketing creates a temporary, delayed uplift that ramps over time."""
    start_month = int(_payload_value(payload, "startMonth", "start_month", default=1))
    impact_amount = float(_payload_value(payload, "impact", default=0))
    upfront_cost = float(_payload_value(payload, "upfront_cost", default=0))
    recurring_cost = float(_payload_value(payload, "recurring_cost", default=0))
    lag_months = int(_payload_value(payload, "lag", "lag_months", default=0))
    ramp_months = int(_payload_value(payload, "ramp", "ramp_months", default=1))
    duration_months = _normalize_duration(
        _payload_value(payload, "duration", "duration_months", default=None)
    )

    scenario_profiles = {
        "BEST": {"multiplier": 1.25, "lag": max(lag_months - 1, 0), "ramp": max(ramp_months - 1, 1)},
        "EXPECTED": {"multiplier": 1.0, "lag": lag_months, "ramp": max(ramp_months, 1)},
        "WORST": {"multiplier": 0.5, "lag": lag_months + 1, "ramp": max(ramp_months + 1, 1)},
    }

    timeline_length = len(timeline_map["EXPECTED"])

    for month_index in range(timeline_length):
        current_month = month_index + 1

        if not _is_active_month(current_month, start_month, duration_months):
            continue

        for timeline in timeline_map.values():
            if current_month == start_month and upfront_cost:
                timeline[month_index]["operating_income"] -= upfront_cost
                timeline[month_index]["net_cash_flow"] -= upfront_cost

            if recurring_cost:
                timeline[month_index]["operating_income"] -= recurring_cost
                timeline[month_index]["net_cash_flow"] -= recurring_cost

        for scenario_name, scenario_config in scenario_profiles.items():
            effect_start_month = start_month + scenario_config["lag"]
            ramp_factor = _scenario_ramp_factor(
                current_month,
                effect_start_month,
                scenario_config["ramp"],
            )
            if ramp_factor <= 0:
                continue

            active_timeline = timeline_map[scenario_name]
            month_data = active_timeline[month_index]
            revenue_lift = impact_amount * scenario_config["multiplier"] * ramp_factor

            if month_data["revenue"] > 0:
                cogs_ratio = month_data["cogs"] / month_data["revenue"]
            else:
                cogs_ratio = 0.0

            incremental_cogs = revenue_lift * cogs_ratio
            gross_profit_lift = revenue_lift - incremental_cogs

            month_data["revenue"] += revenue_lift
            month_data["cogs"] += incremental_cogs
            month_data["gross_profit"] += gross_profit_lift
            month_data["operating_income"] += gross_profit_lift
            month_data["net_cash_flow"] += gross_profit_lift

def calculate_cost_reduction_impact(timeline_map, payload):
    """Math for reducing fixed costs."""
    start_month = _payload_value(payload, "startMonth", "start_month", default=1)
    savings = abs(_payload_value(payload, "impact", default=0))
    
    for month_index in range(len(timeline_map["EXPECTED"])):
        if month_index + 1 >= start_month:
            for timeline in timeline_map.values():
                timeline[month_index]["operating_income"] += savings
                timeline[month_index]["net_cash_flow"] += savings

def calculate_inventory_impact(timeline_map, payload):
    start_month = _payload_value(payload, "startMonth", "start_month", default=1)
    upfront = _payload_value(payload, "upfront_cost", default=0)
    savings = abs(_payload_value(payload, "impact", default=0))

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
