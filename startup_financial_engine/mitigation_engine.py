from risk_signals import GRADE_RANK


def _parse_float(value, default=0.0):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return default


def _parse_duration(value):
    if value in (None, "", "permanent"):
        return None
    try:
        return max(int(value), 1)
    except (TypeError, ValueError):
        return None


def _format_money(value):
    return f"${value:,.0f}"


def _normalize_event_type(event_type):
    normalized = (event_type or "").strip().lower()
    aliases = {
        "hire": "hiring",
        "hiring": "hiring",
        "expand": "expansion",
        "expansion": "expansion",
        "marketing": "marketing",
        "reduce": "cost_reduction",
        "cost_reduction": "cost_reduction",
        "inventory": "inventory",
        "automation": "automation",
    }
    return aliases.get(normalized, normalized)


def _primary_event_type(request, decision_snapshots):
    if request.event_type:
        return _normalize_event_type(request.event_type)
    if decision_snapshots:
        return _normalize_event_type(decision_snapshots[0].get("type"))
    return None


def _signal_types(signals):
    return {signal["type"] for signal in signals}


def _make_suggestion(strategy, impact, trade_off, linked_signal, priority):
    return {
        "strategy": strategy,
        "impact": impact,
        "trade_off": trade_off,
        "linked_signal": linked_signal,
        "priority": priority,
    }


def _add_unique(suggestions, seen, suggestion):
    key = suggestion["strategy"]
    if key in seen:
        return
    seen.add(key)
    suggestions.append(suggestion)


def _largest_fixed_cost_bucket(request):
    buckets = [
        (
            "payroll",
            float(request.payroll or 0),
            "Reduce payroll growth or phase hiring more gradually",
            "Protects cash faster than broad cuts, but may slow team capacity.",
        ),
        (
            "marketing",
            float(request.marketing or 0),
            "Reduce baseline marketing spend by 20%",
            "Preserves cash, but may slow customer acquisition and demand growth.",
        ),
        (
            "rent",
            float(request.rent or 0),
            "Lower recurring occupancy costs where possible",
            "Improves burn, but may constrain workspace or operations.",
        ),
        (
            "utilities",
            float(request.utilities or 0),
            "Reduce utility and overhead spending",
            "Helps cash preservation, but savings may be smaller than payroll or rent changes.",
        ),
    ]
    return max(buckets, key=lambda bucket: bucket[1])


def _monthly_fixed_cost_total(request):
    return sum(
        [
            _parse_float(request.rent),
            _parse_float(request.payroll),
            _parse_float(request.marketing),
            _parse_float(request.utilities),
        ]
    )


def _event_context(request, decision_snapshots, event_type):
    context = {
        "recurring_cost": 0.0,
        "upfront_cost": 0.0,
        "duration_months": None,
        "impact": 0.0,
        "monthly_savings": 0.0,
    }

    if request.event_payload:
        payload = request.event_payload
        context["recurring_cost"] = _parse_float(payload.get("recurring_cost"))
        context["upfront_cost"] = _parse_float(payload.get("upfront_cost"))
        context["impact"] = _parse_float(payload.get("impact"))
        context["duration_months"] = _parse_duration(
            payload.get("duration_months", payload.get("duration"))
        )
        return context

    if not decision_snapshots:
        return context

    primary_decision = decision_snapshots[0]
    context["impact"] = _parse_float(primary_decision.get("impact"))
    context["duration_months"] = _parse_duration(primary_decision.get("duration_months"))

    if event_type == "cost_reduction":
        context["monthly_savings"] = max(context["impact"], 0)
    elif event_type in {"hiring", "expansion"} and context["impact"] < 0:
        context["recurring_cost"] = abs(context["impact"])

    return context


def _build_baseline_suggestions(request, baseline_signals, baseline_resilience):
    suggestions = []
    seen = set()
    signal_types = _signal_types(baseline_signals)
    largest_bucket = _largest_fixed_cost_bucket(request)
    fixed_cost_total = _monthly_fixed_cost_total(request)

    if {
        "critical_insolvency_risk",
        "critical_runway_risk",
        "low_runway_warning",
    } & signal_types:
        _add_unique(
            suggestions,
            seen,
            _make_suggestion(
                "Reduce fixed operating costs by 10-15%",
                (
                    f"Could lower recurring burn by about "
                    f"{_format_money(fixed_cost_total * 0.10)}-"
                    f"{_format_money(fixed_cost_total * 0.15)} per month."
                ),
                "Improves survival odds, but may slow hiring, operations, or growth.",
                "runway_pressure",
                100,
            ),
        )
        if largest_bucket[1] > 0:
            _add_unique(
                suggestions,
                seen,
                _make_suggestion(
                    largest_bucket[2],
                    (
                        f"Targets the largest recurring cost bucket in the plan, "
                        f"currently about {_format_money(largest_bucket[1])} per month."
                    ),
                    largest_bucket[3],
                    "runway_pressure",
                    90,
                ),
            )

    if "sustained_negative_cash_flow" in signal_types and float(request.marketing or 0) > 0:
        _add_unique(
            suggestions,
            seen,
            _make_suggestion(
                "Reduce baseline marketing spend by 20%",
                (
                    f"Cuts about {_format_money(_parse_float(request.marketing) * 0.20)} "
                    "per month from baseline burn."
                ),
                "Improves cash stability, but may reduce near-term demand growth.",
                "sustained_negative_cash_flow",
                80,
            ),
        )

    if baseline_resilience.get("grade") in {"D", "F"}:
        _add_unique(
            suggestions,
            seen,
            _make_suggestion(
                "Pause new discretionary spending until resilience improves",
                "Stabilizes cash before additional growth commitments are added.",
                "Protects survival, but delays expansion speed and upside.",
                "critical_resilience",
                70,
            ),
        )

    return suggestions


def _event_strategy_templates(event_type, event_context):
    recurring_cost = event_context["recurring_cost"]
    upfront_cost = event_context["upfront_cost"]
    duration_months = event_context["duration_months"]
    monthly_savings = event_context["monthly_savings"]
    delay_cash_relief = upfront_cost + (recurring_cost * 2)
    reduced_monthly_cost = recurring_cost * 0.20
    shortened_window_relief = recurring_cost * min(duration_months or 0, 2)

    templates = {
        "marketing": [
            (
                "Delay the marketing campaign by 2 months",
                (
                    f"Defers about {_format_money(delay_cash_relief)} of near-term campaign cash outflow."
                    if delay_cash_relief > 0
                    else "Buys time to build a stronger cash buffer before the campaign starts."
                ),
                "Reduces short-term risk, but delays the upside from the campaign.",
            ),
            (
                "Reduce campaign spend by 20%",
                (
                    f"Could lower campaign burn by about {_format_money(reduced_monthly_cost)} per month."
                    if reduced_monthly_cost > 0
                    else "Lowers the monthly cash commitment of the campaign."
                ),
                "Protects runway, but may reduce campaign reach and upside.",
            ),
            (
                "Shorten the campaign duration",
                (
                    f"Could avoid about {_format_money(shortened_window_relief)} of campaign spend "
                    "from the final months."
                    if shortened_window_relief > 0
                    else "Limits downside exposure if the campaign underperforms."
                ),
                "Improves cash preservation, but reduces the total upside window.",
            ),
        ],
        "hiring": [
            (
                "Delay hiring by 2 months",
                (
                    f"Defers about {_format_money(delay_cash_relief)} of early payroll pressure."
                    if delay_cash_relief > 0
                    else "Reduces short-term payroll pressure while keeping the option open."
                ),
                "Improves runway, but slows team expansion and execution capacity.",
            ),
            (
                "Phase hiring instead of adding the full cost immediately",
                (
                    f"Could trim the initial monthly payroll jump by about {_format_money(reduced_monthly_cost)}."
                    if reduced_monthly_cost > 0
                    else "Spreads the payroll impact across time instead of taking the full burn at once."
                ),
                "Protects cash, but delays the full productivity benefit.",
            ),
            (
                "Lower the initial hiring cost or start with contractors",
                (
                    f"Creates room to cut or defer roughly {_format_money(reduced_monthly_cost)} "
                    "of recurring hiring cost."
                    if reduced_monthly_cost > 0
                    else "Cuts the upfront and recurring burn tied to the hiring decision."
                ),
                "Improves survivability, but may reduce long-term team stability.",
            ),
        ],
        "expansion": [
            (
                "Phase the expansion instead of rolling it out at full scale",
                (
                    f"Could soften the early cash shock by about {_format_money(reduced_monthly_cost)} per month."
                    if reduced_monthly_cost > 0
                    else "Reduces the cash shock from expansion while preserving some upside."
                ),
                "Protects runway, but delays the full growth impact.",
            ),
            (
                "Delay expansion until the cash cushion is stronger",
                (
                    f"Defers about {_format_money(delay_cash_relief)} of near-term expansion outflow."
                    if delay_cash_relief > 0
                    else "Avoids taking on the riskiest part of the expansion during a fragile period."
                ),
                "Improves stability, but pushes revenue growth later.",
            ),
            (
                "Shorten the expansion rollout window",
                (
                    f"Could remove about {_format_money(shortened_window_relief)} of recurring expansion cost."
                    if shortened_window_relief > 0
                    else "Limits downside exposure if the expansion takes longer to pay off."
                ),
                "Preserves cash, but reduces the time available to capture upside.",
            ),
        ],
        "inventory": [
            (
                "Start with a smaller inventory commitment",
                (
                    f"Could reduce the upfront inventory commitment by about {_format_money(upfront_cost * 0.20)}."
                    if upfront_cost > 0
                    else "Reduces the immediate capital tied up in inventory decisions."
                ),
                "Protects cash, but may limit capacity or stock availability.",
            ),
            (
                "Delay the inventory decision until cash is stronger",
                (
                    f"Defers roughly {_format_money(delay_cash_relief)} of inventory-related cash use."
                    if delay_cash_relief > 0
                    else "Avoids locking cash into inventory during a fragile period."
                ),
                "Improves runway, but may slow operational readiness.",
            ),
            (
                "Phase the inventory build-up gradually",
                (
                    f"Spreads about {_format_money(upfront_cost)} of inventory commitment across a longer window."
                    if upfront_cost > 0
                    else "Spreads the cost impact across time instead of concentrating it early."
                ),
                "Preserves cash, but may reduce scale efficiency.",
            ),
        ],
        "cost_reduction": [
            (
                "Apply the cost reduction earlier in the timeline",
                (
                    f"Moves forward savings of about {_format_money(monthly_savings)} per month."
                    if monthly_savings > 0
                    else "Brings the savings forward to relieve runway pressure sooner."
                ),
                "Improves cash protection, but may require faster operational adjustments.",
            ),
            (
                "Increase the cost reduction modestly",
                (
                    f"A 10-15% larger reduction would add roughly "
                    f"{_format_money(monthly_savings * 0.10)}-"
                    f"{_format_money(monthly_savings * 0.15)} of extra monthly savings."
                    if monthly_savings > 0
                    else "Strengthens the savings effect if the current reduction is not enough."
                ),
                "Improves survivability, but may affect operating capacity.",
            ),
        ],
    }
    return templates.get(
        event_type,
        [
            (
                "Delay the planned decision by 2 months",
                "Buys time to strengthen the cash position before the decision starts.",
                "Improves short-term stability, but pushes upside later.",
            ),
            (
                "Roll out the decision in smaller phases",
                "Reduces the downside of taking the full decision all at once.",
                "Protects cash, but delays the full benefit.",
            ),
        ],
    )


def _build_target_suggestions(
    event_type,
    target_name,
    target_signals,
    baseline_resilience,
    target_resilience,
    event_context,
):
    suggestions = []
    seen = set()
    signal_types = _signal_types(target_signals)
    grade_drop = (
        GRADE_RANK.get(baseline_resilience.get("grade", "F"), 0)
        - GRADE_RANK.get(target_resilience.get("grade", "F"), 0)
    )

    priority_boost = 0
    if "scenario_fragility" in signal_types:
        priority_boost += 20
    if "critical_insolvency_risk" in signal_types:
        priority_boost += 30

    for index, template in enumerate(_event_strategy_templates(event_type, event_context)):
        strategy, impact, trade_off = template
        linked_signal = "scenario_fragility" if "scenario_fragility" in signal_types else target_name
        _add_unique(
            suggestions,
            seen,
            _make_suggestion(
                strategy,
                impact,
                trade_off,
                linked_signal,
                100 - (index * 10) + priority_boost,
            ),
        )

    if grade_drop >= 2:
        _add_unique(
            suggestions,
            seen,
            _make_suggestion(
                "Keep the baseline plan and defer this decision until cash resilience improves",
                "The current plan stays materially safer than the stressed decision path.",
                "Avoids downside risk, but also delays the potential upside of the decision.",
                "scenario_fragility",
                120,
            ),
        )

    return suggestions


def _finalize(suggestions):
    suggestions.sort(
        key=lambda suggestion: (-suggestion["priority"], suggestion["strategy"])
    )
    return [
        {key: value for key, value in suggestion.items() if key != "priority"}
        for suggestion in suggestions[:3]
    ]


def generate_mitigation_suggestions(
    request,
    decision_snapshots,
    current_projection,
    risk_signals,
    has_direct_event,
):
    suggestions = {"baseline": [], "scenario": [], "worst": []}
    if not any(risk_signals.values()):
        return suggestions

    resilience = current_projection.get("resilience", {})
    baseline_resilience = resilience.get("baseline", {})
    event_type = _primary_event_type(request, decision_snapshots)
    event_context = _event_context(request, decision_snapshots, event_type)

    suggestions["baseline"] = _finalize(
        _build_baseline_suggestions(
            request,
            risk_signals.get("baseline", []),
            baseline_resilience,
        )
    )

    if event_type and (has_direct_event or decision_snapshots):
        for target_name in ("scenario", "worst"):
            target_signals = risk_signals.get(target_name, [])
            if not target_signals:
                continue

            target_key = "expected" if target_name == "scenario" and has_direct_event else target_name
            target_resilience = resilience.get(target_key, {})
            suggestions[target_name] = _finalize(
                _build_target_suggestions(
                    event_type,
                    target_name,
                    target_signals,
                    baseline_resilience,
                    target_resilience,
                    event_context,
                )
            )

    return suggestions
