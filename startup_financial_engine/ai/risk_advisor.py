"""
ai/risk_advisor.py — AI-powered risk signal interpreter and action planner.

Takes the detected risk signals + resilience grades + stress test results
and produces a prioritised risk brief with specific mitigation strategies.
"""

from __future__ import annotations

import json
from typing import Optional

from ai.client import SimulationContext, _call

# ─────────────────────────────────────────────────────────────────────────────
# System prompts
# ─────────────────────────────────────────────────────────────────────────────

_RISK_BRIEF_SYSTEM = """
You are a venture-backed startup's Chief Risk Officer and financial advisor.
You have reviewed a 3-year financial simulation with full stress testing and
Monte Carlo analysis. Write a Risk Brief for the board that:

1. RISK SUMMARY (2-3 sentences): Overall risk posture and the single biggest threat.

2. TOP RISKS (ranked by severity):
   For each critical/warning signal:
   - Risk name and the month it manifests
   - Root cause (why is this happening in this business?)
   - Probability of occurrence (use Monte Carlo data if relevant)
   - Financial impact (dollar amounts from the simulation)
   - Specific mitigation strategy with owner and timeline

3. STRESS TEST FINDINGS:
   - Which shocks cause the most damage and why
   - The tipping point: at what revenue reduction does survival become unlikely?

4. MITIGATION ROADMAP:
   A 90-day action plan — 3 concrete steps the team must take,
   each with a target metric and deadline.

Tone: Investor-grade. No fluff. Every claim backed by a number.
Length: 400-550 words.
"""

_SIGNAL_EXPLAIN_SYSTEM = """
You are a startup financial advisor explaining a single risk signal to a founder.
In 120-150 words:
- What this signal means in simple terms
- The exact cause in this business (cite the month and dollar figures)
- What happens if it is ignored
- One specific action to take this week
"""

_STRESS_INTERPRET_SYSTEM = """
You are a startup CFO interpreting stress test results for the board.
Analyse the stress test data and in 200-250 words explain:
1. Which scenarios pose existential risk vs. manageable setbacks
2. The business's key vulnerability (revenue, costs, churn, timing?)
3. The "safe operating envelope" — what conditions must hold for survival
4. Two concrete hedging strategies appropriate to this business stage
"""


# ─────────────────────────────────────────────────────────────────────────────
# Prompt builders
# ─────────────────────────────────────────────────────────────────────────────

def _build_risk_brief_prompt(ctx: SimulationContext) -> str:
    # Flatten signals — prioritise critical ones
    signals_flat = []
    for scen, sigs in ctx.all_signals.items():
        for s in sigs:
            signals_flat.append({
                "scenario": scen,
                "level":    s["level"],
                "title":    s["title"],
                "message":  s["message"],
                "month":    s.get("month"),
            })
    signals_flat.sort(key=lambda s: (0 if s["level"] == "critical" else 1, s.get("month") or 999))

    mc = ctx.monte_carlo

    return (
        "RISK SIGNALS (all scenarios):\n"
        + json.dumps(signals_flat, indent=2)
        + "\n\nRESILIENCE GRADES:\n"
        + json.dumps({
            scen: {
                "grade":            r["grade"],
                "runway_months":    r["runway_months"],
                "insolvency_month": r.get("insolvency_month"),
                "avg_burn":         r.get("average_monthly_burn", 0),
                "ending_cash":      r["ending_cash_balance"],
            }
            for scen, r in ctx.scenario_resilience.items()
        }, indent=2)
        + "\n\nSTRESS TEST RESULTS:\n"
        + json.dumps([
            {"shock": s["shock_name"], "grade": s["grade"],
             "ending_cash": s["ending_cash"], "survives": s["survives"],
             "runway_months": s["runway_months"]}
            for s in ctx.stress_results
        ], indent=2)
        + "\n\nMONTE CARLO:\n"
        + json.dumps({
            "survival_rate":          mc.get("survival_rate"),
            "insolvency_probability": mc.get("insolvency_probability"),
            "avg_insolvency_month":   mc.get("avg_insolvency_month"),
            "p10_ending_cash":        mc.get("p10_ending_cash"),
            "p90_ending_cash":        mc.get("p90_ending_cash"),
            "var_95":                 mc.get("var_95"),
        }, indent=2)
        + "\n\nBUSINESS CONTEXT:\n"
        + json.dumps({
            "starting_cash": ctx.starting_cash,
            "events":        [e["name"] for e in ctx.events],
            "assumptions":   ctx.assumptions,
        }, indent=2)
    )


def _build_signal_explain_prompt(ctx: SimulationContext, signal_title: str) -> str:
    # Find the signal
    target = None
    for scen, sigs in ctx.all_signals.items():
        for s in sigs:
            if signal_title.lower() in s["title"].lower():
                target = {**s, "scenario": scen}
                break
        if target:
            break

    if target is None:
        return f"Signal '{signal_title}' not found."

    exp_res = ctx.scenario_resilience.get("EXPECTED", {})

    return (
        f"Explain this risk signal:\n{json.dumps(target, indent=2)}\n\n"
        f"Business context:\n"
        f"Starting cash: ${ctx.starting_cash:,.0f}\n"
        f"EXPECTED grade: {exp_res.get('grade')} — runway {exp_res.get('runway_months')} months\n"
        f"Insolvency month: {exp_res.get('insolvency_month')}\n"
        f"Events active: {[e['name'] for e in ctx.events]}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_risk_brief(ctx: SimulationContext) -> str:
    """
    Generate a full board-level risk brief covering all signals,
    stress test findings, and a 90-day mitigation roadmap.
    """
    print(f"\n{'═' * 70}")
    print("  🤖 AI RISK BRIEF")
    print(f"{'═' * 70}\n")
    prompt = _build_risk_brief_prompt(ctx)
    return _call(_RISK_BRIEF_SYSTEM, prompt, max_tokens=500)


def explain_signal(ctx: SimulationContext, signal_title: str) -> str:
    """
    Explain a specific risk signal in plain English with a weekly action item.
    `signal_title` is a partial match (case-insensitive).
    """
    print(f"\n📡 Explaining signal: '{signal_title}'\n")
    prompt = _build_signal_explain_prompt(ctx, signal_title)
    return _call(_SIGNAL_EXPLAIN_SYSTEM, prompt, max_tokens=200)


def interpret_stress_tests(ctx: SimulationContext) -> str:
    """
    Deep interpretation of stress test results — which shocks are existential,
    what is the safe operating envelope, and how to hedge.
    """
    print(f"\n{'═' * 70}")
    print("  🤖 AI STRESS TEST INTERPRETATION")
    print(f"{'═' * 70}\n")

    mc = ctx.monte_carlo
    prompt = (
        "Stress test results:\n"
        + json.dumps([
            {"shock": s["shock_name"], "description": s.get("description", ""),
             "grade": s["grade"], "grade_drop": s["grade_drop"],
             "ending_cash": s["ending_cash"], "survives": s["survives"],
             "runway_months": s["runway_months"]}
            for s in ctx.stress_results
        ], indent=2)
        + "\n\nMonte Carlo:\n"
        + json.dumps({
            "survival_rate":    mc.get("survival_rate"),
            "insolvency_prob":  mc.get("insolvency_probability"),
            "p10":              mc.get("p10_ending_cash"),
            "p90":              mc.get("p90_ending_cash"),
            "var_95":           mc.get("var_95"),
        }, indent=2)
        + f"\n\nStarting cash: ${ctx.starting_cash:,.0f}"
        + f"\nEXPECTED baseline grade: {ctx.scenario_resilience.get('EXPECTED', {}).get('grade')}"
        + f"\nEXPECTED runway: {ctx.scenario_resilience.get('EXPECTED', {}).get('runway_months')} months"
    )
    return _call(_STRESS_INTERPRET_SYSTEM, prompt, max_tokens=300)
