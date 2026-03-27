"""
event_calculator.py — Financial event impact engine.

Applies business events (hire, expand, market, reduce costs, inventory,
contract) to a multi-scenario timeline map.

All calculator functions are pure with respect to the timeline_map:
they mutate copies implicitly through the caller's timeline_map references.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Payload helpers
# ---------------------------------------------------------------------------

def _val(payload: dict, *keys: str, default: float = 0) -> Any:
    for k in keys:
        if k in payload and payload[k] is not None:
            return payload[k]
    return default


def _normalize_duration(v) -> Optional[int]:
    if v in (None, "", "permanent"):
        return None
    return int(v)


def _is_active(current: int, start: int, duration: Optional[int]) -> bool:
    if current < start:
        return False
    if duration is None:
        return True
    return current < start + duration


def _ramp_factor(current: int, effect_start: int, ramp: int) -> float:
    if current < effect_start:
        return 0.0
    ramp = max(int(ramp), 1)
    return min((current - effect_start + 1) / ramp, 1.0)


def _build_profiles(
    lag: int,
    ramp: int,
    *,
    best_mult: float = 1.5,      
    expected_mult: float = 1.0,
    worst_mult: float = 0.3,     
) -> Dict[str, dict]:
    return {
        "BEST":     {"mult": best_mult,     "lag": max(lag - 1, 0), "ramp": max(ramp - 1, 1)},
        "EXPECTED": {"mult": expected_mult, "lag": lag,             "ramp": max(ramp, 1)},
        "WORST":    {"mult": worst_mult,    "lag": lag + 1,         "ramp": max(ramp + 1, 1)},
    }


# ---------------------------------------------------------------------------
# Primitive mutations
# ---------------------------------------------------------------------------

def _apply_delta(m: dict, delta: float) -> None:
    """Add `delta` to operating_income and net_cash_flow."""
    m["operating_income"] = m.get("operating_income", 0) + delta
    m["net_cash_flow"]    = m.get("net_cash_flow", 0)    + delta


def _apply_revenue_lift(m: dict, lift: float) -> None:
    if lift <= 0:
        return
    rev = m.get("revenue", 0)
    cogs_ratio = min(max(m.get("cogs", 0) / rev, 0.0), 1.0) if rev > 0 else 0.0
    inc_cogs = lift * cogs_ratio
    gp_lift  = lift - inc_cogs
    m["revenue"]          = rev + lift
    m["cogs"]             = m.get("cogs", 0) + inc_cogs
    m["gross_profit"]     = m.get("gross_profit", 0) + gp_lift
    _apply_delta(m, gp_lift)


def _apply_cogs_savings(m: dict, savings: float) -> None:
    if savings <= 0:
        return
    realized = min(savings, max(m.get("cogs", 0), 0))
    m["cogs"]         = m.get("cogs", 0) - realized
    m["gross_profit"] = m.get("gross_profit", 0) + realized
    _apply_delta(m, realized)


def _apply_guaranteed_costs(
    timeline_map: Dict[str, List[dict]],
    month_index: int,
    current: int,
    start: int,
    upfront: float,
    recurring: float,
) -> None:
    for timeline in timeline_map.values():
        m = timeline[month_index]
        if current == start and upfront:
            _apply_delta(m, -upfront)
        if recurring:
            _apply_delta(m, -recurring)


# ---------------------------------------------------------------------------
# Event calculators
# ---------------------------------------------------------------------------

def calculate_hiring_impact(timeline_map: Dict[str, List[dict]], payload: dict) -> None:
    """
    Headcount addition.
    Costs: recruiting fee (upfront) + salary (recurring).
    Benefit: revenue contribution that ramps per scenario.

    BEST:     immediate 3× salary ROI (high performer, hits ground running)
    EXPECTED: 2-month ramp, then 1.5× salary contribution
    WORST:    no revenue contribution (bad hire / slow ramp)
    """
    start      = int(_val(payload, "start_month", "startMonth", default=1))
    salary     = float(_val(payload, "recurring_cost", default=0))
    if not salary:
        salary = abs(min(float(_val(payload, "impact", default=0)), 0))
    recruiting = float(_val(payload, "upfront_cost", default=0))
    horizon    = len(next(iter(timeline_map.values())))

    for idx in range(horizon):
        current = idx + 1
        if current < start:
            continue

        # Cost is guaranteed across all scenarios
        for tl in timeline_map.values():
            _apply_delta(tl[idx], -salary)
            if current == start:
                _apply_delta(tl[idx], -recruiting)

        # Scenario-specific ROI
        timeline_map["BEST"][idx]["operating_income"] += salary * 3
        timeline_map["BEST"][idx]["net_cash_flow"]    += salary * 3

        if current >= start + 2:
            timeline_map["EXPECTED"][idx]["operating_income"] += salary * 1.5
            timeline_map["EXPECTED"][idx]["net_cash_flow"]    += salary * 1.5
        # WORST: zero contribution (already absorbed the cost above)


def calculate_expansion_impact(timeline_map: Dict[str, List[dict]], payload: dict) -> None:
    """
    Physical / market expansion.
    Costs: buildout (upfront) + new rent (recurring).
    Benefit: delayed, ramping revenue lift.
    """
    start    = int(_val(payload, "start_month", "startMonth", default=1))
    impact   = max(float(_val(payload, "impact", default=0)), 0.0)
    buildout = max(float(_val(payload, "upfront_cost", default=0)), 0.0)
    new_rent = max(float(_val(payload, "recurring_cost", default=0)), 0.0)
    lag      = int(_val(payload, "lag", "lag_months", default=0))
    ramp     = int(_val(payload, "ramp", "ramp_months", default=1))
    duration = _normalize_duration(_val(payload, "duration", "duration_months", default=None))
    profiles = _build_profiles(lag, ramp)
    horizon  = len(timeline_map["EXPECTED"])

    for idx in range(horizon):
        current = idx + 1
        if not _is_active(current, start, duration):
            continue
        _apply_guaranteed_costs(timeline_map, idx, current, start, buildout, new_rent)
        for scenario, cfg in profiles.items():
            lift = impact * cfg["mult"] * _ramp_factor(current, start + cfg["lag"], cfg["ramp"])
            _apply_revenue_lift(timeline_map[scenario][idx], lift)


def calculate_marketing_impact(timeline_map: Dict[str, List[dict]], payload: dict) -> None:
    """
    Marketing spend with delayed, ramping revenue uplift.
    """
    start     = int(_val(payload, "startMonth", "start_month", default=1))
    impact    = max(float(_val(payload, "impact", default=0)), 0.0)
    upfront   = max(float(_val(payload, "upfront_cost", default=0)), 0.0)
    recurring = max(float(_val(payload, "recurring_cost", default=0)), 0.0)
    lag       = int(_val(payload, "lag", "lag_months", default=0))
    ramp      = int(_val(payload, "ramp", "ramp_months", default=1))
    duration  = _normalize_duration(_val(payload, "duration", "duration_months", default=None))
    profiles  = _build_profiles(lag, ramp)
    horizon   = len(timeline_map["EXPECTED"])

    for idx in range(horizon):
        current = idx + 1
        if not _is_active(current, start, duration):
            continue
        _apply_guaranteed_costs(timeline_map, idx, current, start, upfront, recurring)
        for scenario, cfg in profiles.items():
            factor = _ramp_factor(current, start + cfg["lag"], cfg["ramp"])
            if factor <= 0:
                continue
            lift = impact * cfg["mult"] * factor
            _apply_revenue_lift(timeline_map[scenario][idx], lift)


def calculate_cost_reduction_impact(timeline_map: Dict[str, List[dict]], payload: dict) -> None:
    """
    Cost reduction / operational efficiency improvement.
    """
    start     = int(_val(payload, "startMonth", "start_month", default=1))
    savings   = abs(float(_val(payload, "impact", default=0)))
    upfront   = max(float(_val(payload, "upfront_cost", default=0)), 0.0)
    recurring = max(float(_val(payload, "recurring_cost", default=0)), 0.0)
    lag       = int(_val(payload, "lag", "lag_months", default=0))
    ramp      = int(_val(payload, "ramp", "ramp_months", default=1))
    duration  = _normalize_duration(_val(payload, "duration", "duration_months", default=None))
    profiles  = _build_profiles(lag, ramp)
    horizon   = len(timeline_map["EXPECTED"])

    for idx in range(horizon):
        current = idx + 1
        if not _is_active(current, start, duration):
            continue
        _apply_guaranteed_costs(timeline_map, idx, current, start, upfront, recurring)
        for scenario, cfg in profiles.items():
            lift = savings * cfg["mult"] * _ramp_factor(current, start + cfg["lag"], cfg["ramp"])
            _apply_delta(timeline_map[scenario][idx], lift)


def calculate_inventory_impact(timeline_map: Dict[str, List[dict]], payload: dict) -> None:
    """
    Bulk inventory purchase — reduces COGS via lower unit cost.
    """
    start     = int(_val(payload, "startMonth", "start_month", default=1))
    upfront   = max(float(_val(payload, "upfront_cost", default=0)), 0.0)
    recurring = max(float(_val(payload, "recurring_cost", default=0)), 0.0)
    savings   = abs(float(_val(payload, "impact", default=0)))
    lag       = int(_val(payload, "lag", "lag_months", default=0))
    ramp      = int(_val(payload, "ramp", "ramp_months", default=1))
    duration  = _normalize_duration(_val(payload, "duration", "duration_months", default=None))
    profiles  = _build_profiles(lag, ramp)
    horizon   = len(timeline_map["EXPECTED"])

    for idx in range(horizon):
        current = idx + 1
        if not _is_active(current, start, duration):
            continue
        _apply_guaranteed_costs(timeline_map, idx, current, start, upfront, recurring)
        for scenario, cfg in profiles.items():
            lift = savings * cfg["mult"] * _ramp_factor(current, start + cfg["lag"], cfg["ramp"])
            _apply_cogs_savings(timeline_map[scenario][idx], lift)


def calculate_contract_impact(timeline_map: Dict[str, List[dict]], payload: dict) -> None:
    """
    New contract / enterprise deal — guaranteed recurring revenue for a fixed term.

    Unlike marketing (probabilistic), contract revenue is treated as committed:
    all scenarios receive full revenue, but WORST discounts for possible early
    termination (50% of months active).
    """
    start    = int(_val(payload, "startMonth", "start_month", default=1))
    monthly  = max(float(_val(payload, "impact", "recurring_revenue", default=0)), 0.0)
    duration = _normalize_duration(_val(payload, "duration", "duration_months", default=None))
    horizon  = len(timeline_map["EXPECTED"])

    for idx in range(horizon):
        current = idx + 1
        if not _is_active(current, start, duration):
            continue
        for scenario, tl in timeline_map.items():
            # WORST: 50% chance each month that contract is cancelled
            mult = 0.5 if scenario == "WORST" else 1.0
            _apply_revenue_lift(tl[idx], monthly * mult)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_DISPATCH: Dict[str, Any] = {
    "hiring":    calculate_hiring_impact,
    "hire":      calculate_hiring_impact,
    "expansion": calculate_expansion_impact,
    "expand":    calculate_expansion_impact,
    "marketing": calculate_marketing_impact,
    "reduce":    calculate_cost_reduction_impact,
    "cost":      calculate_cost_reduction_impact,
    "inventory": calculate_inventory_impact,
    "contract":  calculate_contract_impact,
}


def apply_event(
    timeline_map: Dict[str, List[dict]],
    event_type: str,
    event_payload: dict,
) -> bool:
    """
    Route an event to the correct calculator.

    Returns True if the event was handled, False if unknown type.
    """
    if not event_type or not event_payload:
        return False

    handler = _DISPATCH.get(event_type.lower().strip())
    if handler is None:
        return False

    handler(timeline_map, event_payload)
    return True


def apply_events_batch(
    timeline_map: Dict[str, List[dict]],
    events: List[dict],
) -> Dict[str, List[str]]:

    applied, skipped = [], []

    for event in events:
        etype   = event.get("type", "")
        payload = event.get("payload", {})
        name    = event.get("name", etype)

        # 🔥 CLEAN PRINT (once per event)
        print(f"\n=== Applying Decision: {name} ===")

        if apply_event(timeline_map, etype, payload):
            applied.append(name)
        else:
            skipped.append(name)

    return {"applied": applied, "skipped": skipped}
