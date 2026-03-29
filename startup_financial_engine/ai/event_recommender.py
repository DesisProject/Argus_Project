"""
ai/event_recommender.py — AI-powered business event recommendation engine.

Analyses the current simulation state and recommends which events (hire,
market, reduce costs, contract, inventory, expand) would most improve
resilience, runway, and cash position — with specific parameters.
"""

from __future__ import annotations

import json
from typing import Optional

from ai.client import SimulationContext, _call

# ─────────────────────────────────────────────────────────────────────────────
# System prompts
# ─────────────────────────────────────────────────────────────────────────────

_RECOMMENDER_SYSTEM = """
You are a startup CFO and growth advisor. A founder has just run a financial
simulation and needs to know what strategic actions to take.

The available event types and what they do:
- hire:      Add headcount (upfront recruiting fee + monthly salary; generates revenue ROI)
- marketing: Run a campaign (upfront + recurring cost; delayed revenue uplift with ramp)
- reduce:    Cut vendor/operational costs (upfront implementation + savings)
- contract:  Sign an enterprise deal (recurring guaranteed revenue for fixed term)
- inventory: Bulk purchase (upfront; reduces COGS through lower unit cost)
- expand:    Open new location/market (buildout + rent; delayed revenue lift)

Each event needs: start_month, upfront_cost, recurring_cost, impact,
lag_months (delay before benefit starts), ramp_months (months to full effect),
duration_months (optional, "permanent" if ongoing).

Given the simulation results, recommend the TOP 3 events that would most
improve this business's financial resilience. For each:

1. Event type and name
2. WHY this specific event — root cause it addresses
3. Exact parameters to use (start_month, costs, impact amount, lag, ramp)
4. Expected financial impact: projected runway improvement and cash improvement
5. Risk: what could go wrong with this recommendation

Prioritise: survival first, then grade improvement, then cash cushion.
Be specific with dollar amounts. Tie every recommendation to data from the simulation.

Format each recommendation clearly with numbered headers.
Length: 400-500 words total.
"""

_SINGLE_EVENT_SYSTEM = """
You are a startup financial advisor. The founder is considering a specific
business event. Analyse whether it makes sense given their current financial
position, and suggest the optimal parameters.

In 200-250 words:
1. Whether to proceed (yes/conditional/no) and why
2. Optimal timing (which month to start)
3. Recommended budget/impact parameters
4. Expected effect on runway and cash
5. One key risk to watch
"""

_WHAT_IF_SYSTEM = """
You are a startup CFO doing scenario analysis. The founder is asking a
"what if" question about a potential business decision.

Use the simulation data to reason through the financial impact step by step:
1. What changes in the model (which line items, which months)
2. Estimated dollar impact (derive from existing numbers)
3. Effect on runway and resilience grade
4. Recommendation: do it, don't do it, or do it differently

Be concrete. Show your reasoning. 150-200 words.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Prompt builders
# ─────────────────────────────────────────────────────────────────────────────

def _build_recommender_prompt(ctx: SimulationContext, goal: str) -> str:
    exp_res = ctx.scenario_resilience.get("EXPECTED", {})
    worst_res = ctx.scenario_resilience.get("WORST", {})

    # Find months with worst cash positions
    exp_tl = ctx.timeline_map.get("EXPECTED", [])
    low_cash_months = sorted(
        [m for m in exp_tl if m.get("cash_balance", 0) < 0],
        key=lambda m: m.get("cash_balance", 0)
    )[:3]

    return (
        f"Founder's goal: {goal}\n\n"
        "Current simulation state:\n"
        + json.dumps({
            "EXPECTED_grade":          exp_res.get("grade"),
            "EXPECTED_runway_months":  exp_res.get("runway_months"),
            "EXPECTED_insolvency_month": exp_res.get("insolvency_month"),
            "EXPECTED_ending_cash":    exp_res.get("ending_cash_balance"),
            "EXPECTED_avg_burn":       exp_res.get("average_monthly_burn"),
            "WORST_grade":             worst_res.get("grade"),
            "WORST_insolvency_month":  worst_res.get("insolvency_month"),
            "starting_cash":           ctx.starting_cash,
            "events_already_applied":  [e["name"] for e in ctx.events],
            "months_with_negative_cash": [
                {"month": m.get("month"), "cash_balance": m.get("cash_balance"),
                 "net_cash_flow": m.get("net_cash_flow")}
                for m in low_cash_months
            ],
            "critical_signals": [
                {"title": s["title"], "month": s.get("month"), "message": s["message"]}
                for sigs in ctx.all_signals.values()
                for s in sigs if s["level"] == "critical"
            ],
        }, indent=2)
        + "\n\nKey assumptions:\n"
        + json.dumps({
            "price_per_unit":    ctx.assumptions.get("price_per_unit"),
            "cost_per_unit":     ctx.assumptions.get("cost_per_unit"),
            "rent":              ctx.assumptions.get("rent"),
            "payroll":           ctx.assumptions.get("payroll"),
            "monthly_unit_sales_range": [
                min(ctx.assumptions.get("monthly_unit_sales", [0])),
                max(ctx.assumptions.get("monthly_unit_sales", [0])),
            ],
        }, indent=2)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def recommend_events(
    ctx: SimulationContext,
    goal: str = "Maximise runway and achieve at least a B resilience grade",
) -> str:
    """
    Generate top 3 event recommendations with specific parameters.

    Parameters
    ----------
    ctx  : SimulationContext
    goal : The founder's stated objective (free text)
    """
    print(f"\n{'═' * 70}")
    print("  🤖 AI EVENT RECOMMENDATIONS")
    print(f"{'═' * 70}")
    print(f"  Goal: {goal}\n")
    prompt = _build_recommender_prompt(ctx, goal)
    return _call(_RECOMMENDER_SYSTEM, prompt, max_tokens=500)


def evaluate_event(
    ctx: SimulationContext,
    event_type: str,
    description: str,
) -> str:
    """
    Evaluate a specific event the founder is considering.

    Parameters
    ----------
    event_type  : e.g. "hire", "marketing", "contract"
    description : Free-text description of what they're considering
    """
    print(f"\n🔍 Evaluating event: [{event_type}] {description}\n")

    exp_res = ctx.scenario_resilience.get("EXPECTED", {})
    prompt = (
        f"Event under consideration: [{event_type}] {description}\n\n"
        f"Current financial state:\n"
        f"  Grade: {exp_res.get('grade')} ({exp_res.get('label')})\n"
        f"  Runway: {exp_res.get('runway_months')} months\n"
        f"  Insolvency month: {exp_res.get('insolvency_month')}\n"
        f"  Avg monthly burn: ${exp_res.get('average_monthly_burn', 0):,.0f}\n"
        f"  Ending cash: ${exp_res.get('ending_cash_balance', 0):,.0f}\n"
        f"  Starting cash: ${ctx.starting_cash:,.0f}\n\n"
        f"Events already applied: {[e['name'] for e in ctx.events]}\n\n"
        f"Critical signals: {[s['title'] for sigs in ctx.all_signals.values() for s in sigs if s['level'] == 'critical']}"
    )
    return _call(_SINGLE_EVENT_SYSTEM, prompt, max_tokens=300)


def what_if(ctx: SimulationContext, question: str) -> str:
    """
    Answer a "what if" question about a business decision.

    Example: "What if we delayed hiring until month 9?"
    """
    print(f"\n💭 What-if analysis: {question}\n")

    exp_res = ctx.scenario_resilience.get("EXPECTED", {})
    # Include first 12 months for context
    tl_summary = [
        {k: round(v, 2) if isinstance(v, float) else v
         for k, v in m.items()}
        for m in ctx.timeline_map.get("EXPECTED", [])[:12]
    ]

    prompt = (
        f"What-if question: {question}\n\n"
        f"Current EXPECTED state:\n"
        f"  Grade: {exp_res.get('grade')}, Runway: {exp_res.get('runway_months')} months\n"
        f"  Insolvency month: {exp_res.get('insolvency_month')}\n"
        f"  Avg burn: ${exp_res.get('average_monthly_burn', 0):,.0f}/month\n"
        f"  Starting cash: ${ctx.starting_cash:,.0f}\n\n"
        f"Events applied: {[e['name'] for e in ctx.events]}\n\n"
        f"First 12 months (EXPECTED):\n"
        + json.dumps(tl_summary, indent=2)
    )
    return _call(_WHAT_IF_SYSTEM, prompt, max_tokens=250)
