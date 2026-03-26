from risk_signals import GRADE_RANK


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


def _build_baseline_suggestions(request, baseline_signals, baseline_resilience):
    suggestions = []
    seen = set()
    signal_types = _signal_types(baseline_signals)
    largest_bucket = _largest_fixed_cost_bucket(request)

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
                "Targets the recurring monthly burn that is pressuring runway.",
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
                    "Focuses on the largest recurring cost bucket in the current plan.",
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
                "Cuts monthly burn immediately while preserving the rest of the plan.",
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


def _event_strategy_templates(event_type):
    templates = {
        "marketing": [
            (
                "Delay the marketing campaign by 2 months",
                "Buys time to build a stronger cash buffer before the campaign starts.",
                "Reduces short-term risk, but delays the upside from the campaign.",
            ),
            (
                "Reduce campaign spend by 20%",
                "Lowers the monthly cash commitment of the campaign.",
                "Protects runway, but may reduce campaign reach and upside.",
            ),
            (
                "Shorten the campaign duration",
                "Limits downside exposure if the campaign underperforms.",
                "Improves cash preservation, but reduces the total upside window.",
            ),
        ],
        "hiring": [
            (
                "Delay hiring by 2 months",
                "Reduces short-term payroll pressure while keeping the option open.",
                "Improves runway, but slows team expansion and execution capacity.",
            ),
            (
                "Phase hiring instead of adding the full cost immediately",
                "Spreads the payroll impact across time instead of taking the full burn at once.",
                "Protects cash, but delays the full productivity benefit.",
            ),
            (
                "Lower the initial hiring cost or start with contractors",
                "Cuts the upfront and recurring burn tied to the hiring decision.",
                "Improves survivability, but may reduce long-term team stability.",
            ),
        ],
        "expansion": [
            (
                "Phase the expansion instead of rolling it out at full scale",
                "Reduces the cash shock from expansion while preserving some upside.",
                "Protects runway, but delays the full growth impact.",
            ),
            (
                "Delay expansion until the cash cushion is stronger",
                "Avoids taking on the riskiest part of the expansion during a fragile period.",
                "Improves stability, but pushes revenue growth later.",
            ),
            (
                "Shorten the expansion rollout window",
                "Limits downside exposure if the expansion takes longer to pay off.",
                "Preserves cash, but reduces the time available to capture upside.",
            ),
        ],
        "inventory": [
            (
                "Start with a smaller inventory commitment",
                "Reduces the immediate capital tied up in inventory decisions.",
                "Protects cash, but may limit capacity or stock availability.",
            ),
            (
                "Delay the inventory decision until cash is stronger",
                "Avoids locking cash into inventory during a fragile period.",
                "Improves runway, but may slow operational readiness.",
            ),
            (
                "Phase the inventory build-up gradually",
                "Spreads the cost impact across time instead of concentrating it early.",
                "Preserves cash, but may reduce scale efficiency.",
            ),
        ],
        "cost_reduction": [
            (
                "Apply the cost reduction earlier in the timeline",
                "Brings the savings forward to relieve runway pressure sooner.",
                "Improves cash protection, but may require faster operational adjustments.",
            ),
            (
                "Increase the cost reduction modestly",
                "Strengthens the savings effect if the current reduction is not enough.",
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

    for index, template in enumerate(_event_strategy_templates(event_type)):
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
                )
            )

    return suggestions
