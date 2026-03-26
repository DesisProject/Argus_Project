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


def _build_scenario_profiles(
    lag_months,
    ramp_months,
    *,
    best_multiplier=1.25,
    expected_multiplier=1.0,
    worst_multiplier=0.5,
):
    return {
        "BEST": {
            "multiplier": best_multiplier,
            "lag": max(lag_months - 1, 0),
            "ramp": max(ramp_months - 1, 1),
        },
        "EXPECTED": {
            "multiplier": expected_multiplier,
            "lag": lag_months,
            "ramp": max(ramp_months, 1),
        },
        "WORST": {
            "multiplier": worst_multiplier,
            "lag": lag_months + 1,
            "ramp": max(ramp_months + 1, 1),
        },
    }


def _apply_operating_delta(month_data, delta):
    month_data["operating_income"] += delta
    month_data["net_cash_flow"] += delta


def _apply_revenue_lift(month_data, revenue_lift):
    if revenue_lift <= 0:
        return

    if month_data["revenue"] > 0:
        cogs_ratio = month_data["cogs"] / month_data["revenue"]
        cogs_ratio = min(max(cogs_ratio, 0.0), 1.0)
    else:
        cogs_ratio = 0.0

    incremental_cogs = revenue_lift * cogs_ratio
    gross_profit_lift = revenue_lift - incremental_cogs

    month_data["revenue"] += revenue_lift
    month_data["cogs"] += incremental_cogs
    month_data["gross_profit"] += gross_profit_lift
    _apply_operating_delta(month_data, gross_profit_lift)


def _apply_cogs_savings(month_data, savings_amount):
    if savings_amount <= 0:
        return

    realized_savings = min(savings_amount, max(month_data["cogs"], 0))
    month_data["cogs"] -= realized_savings
    month_data["gross_profit"] += realized_savings
    _apply_operating_delta(month_data, realized_savings)


def _apply_guaranteed_costs(
    timeline_map,
    month_index,
    current_month,
    start_month,
    upfront_cost,
    recurring_cost,
):
    for timeline in timeline_map.values():
        month_data = timeline[month_index]
        if current_month == start_month and upfront_cost:
            _apply_operating_delta(month_data, -upfront_cost)
        if recurring_cost:
            _apply_operating_delta(month_data, -recurring_cost)


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
    """Expansion adds optional new costs and a delayed revenue lift."""
    start_month = int(_payload_value(payload, "start_month", "startMonth", default=1))
    impact_amount = max(float(_payload_value(payload, "impact", default=0)), 0.0)
    buildout_cost = max(float(_payload_value(payload, "upfront_cost", default=0)), 0.0)
    new_rent = max(float(_payload_value(payload, "recurring_cost", default=0)), 0.0)
    lag_months = int(_payload_value(payload, "lag", "lag_months", default=0))
    ramp_months = int(_payload_value(payload, "ramp", "ramp_months", default=1))
    duration_months = _normalize_duration(
        _payload_value(payload, "duration", "duration_months", default=None)
    )
    scenario_profiles = _build_scenario_profiles(lag_months, ramp_months)

    for month_index in range(len(timeline_map["EXPECTED"])):
        current_month = month_index + 1
        if not _is_active_month(current_month, start_month, duration_months):
            continue

        _apply_guaranteed_costs(
            timeline_map,
            month_index,
            current_month,
            start_month,
            buildout_cost,
            new_rent,
        )

        for scenario_name, scenario_config in scenario_profiles.items():
            effect_start_month = start_month + scenario_config["lag"]
            ramp_factor = _scenario_ramp_factor(
                current_month,
                effect_start_month,
                scenario_config["ramp"],
            )
            revenue_lift = impact_amount * scenario_config["multiplier"] * ramp_factor
            _apply_revenue_lift(timeline_map[scenario_name][month_index], revenue_lift)

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
    impact_amount = max(float(_payload_value(payload, "impact", default=0)), 0.0)
    upfront_cost = max(float(_payload_value(payload, "upfront_cost", default=0)), 0.0)
    recurring_cost = max(float(_payload_value(payload, "recurring_cost", default=0)), 0.0)
    lag_months = int(_payload_value(payload, "lag", "lag_months", default=0))
    ramp_months = int(_payload_value(payload, "ramp", "ramp_months", default=1))
    duration_months = _normalize_duration(
        _payload_value(payload, "duration", "duration_months", default=None)
    )
    scenario_profiles = _build_scenario_profiles(lag_months, ramp_months)

    timeline_length = len(timeline_map["EXPECTED"])

    for month_index in range(timeline_length):
        current_month = month_index + 1

        if not _is_active_month(current_month, start_month, duration_months):
            continue

        _apply_guaranteed_costs(
            timeline_map,
            month_index,
            current_month,
            start_month,
            upfront_cost,
            recurring_cost,
        )

        for scenario_name, scenario_config in scenario_profiles.items():
            effect_start_month = start_month + scenario_config["lag"]
            ramp_factor = _scenario_ramp_factor(
                current_month,
                effect_start_month,
                scenario_config["ramp"],
            )
            if ramp_factor <= 0:
                continue

            revenue_lift = impact_amount * scenario_config["multiplier"] * ramp_factor
            _apply_revenue_lift(timeline_map[scenario_name][month_index], revenue_lift)

def calculate_cost_reduction_impact(timeline_map, payload):
    """Cost reduction lowers operating expenses over the active event window."""
    start_month = int(_payload_value(payload, "startMonth", "start_month", default=1))
    savings = abs(float(_payload_value(payload, "impact", default=0)))
    upfront_cost = max(float(_payload_value(payload, "upfront_cost", default=0)), 0.0)
    recurring_cost = max(float(_payload_value(payload, "recurring_cost", default=0)), 0.0)
    lag_months = int(_payload_value(payload, "lag", "lag_months", default=0))
    ramp_months = int(_payload_value(payload, "ramp", "ramp_months", default=1))
    duration_months = _normalize_duration(
        _payload_value(payload, "duration", "duration_months", default=None)
    )
    scenario_profiles = _build_scenario_profiles(lag_months, ramp_months)

    for month_index in range(len(timeline_map["EXPECTED"])):
        current_month = month_index + 1
        if not _is_active_month(current_month, start_month, duration_months):
            continue

        _apply_guaranteed_costs(
            timeline_map,
            month_index,
            current_month,
            start_month,
            upfront_cost,
            recurring_cost,
        )

        for scenario_name, scenario_config in scenario_profiles.items():
            effect_start_month = start_month + scenario_config["lag"]
            ramp_factor = _scenario_ramp_factor(
                current_month,
                effect_start_month,
                scenario_config["ramp"],
            )
            savings_lift = savings * scenario_config["multiplier"] * ramp_factor
            _apply_operating_delta(
                timeline_map[scenario_name][month_index],
                savings_lift,
            )

def calculate_inventory_impact(timeline_map, payload):
    """Inventory spend improves margins through lower product cost."""
    start_month = int(_payload_value(payload, "startMonth", "start_month", default=1))
    upfront = max(float(_payload_value(payload, "upfront_cost", default=0)), 0.0)
    recurring_cost = max(float(_payload_value(payload, "recurring_cost", default=0)), 0.0)
    savings = abs(float(_payload_value(payload, "impact", default=0)))
    lag_months = int(_payload_value(payload, "lag", "lag_months", default=0))
    ramp_months = int(_payload_value(payload, "ramp", "ramp_months", default=1))
    duration_months = _normalize_duration(
        _payload_value(payload, "duration", "duration_months", default=None)
    )
    scenario_profiles = _build_scenario_profiles(lag_months, ramp_months)

    for month_index in range(len(timeline_map["EXPECTED"])):
        current_month = month_index + 1
        if not _is_active_month(current_month, start_month, duration_months):
            continue

        _apply_guaranteed_costs(
            timeline_map,
            month_index,
            current_month,
            start_month,
            upfront,
            recurring_cost,
        )

        for scenario_name, scenario_config in scenario_profiles.items():
            effect_start_month = start_month + scenario_config["lag"]
            ramp_factor = _scenario_ramp_factor(
                current_month,
                effect_start_month,
                scenario_config["ramp"],
            )
            savings_lift = savings * scenario_config["multiplier"] * ramp_factor
            _apply_cogs_savings(
                timeline_map[scenario_name][month_index],
                savings_lift,
            )
