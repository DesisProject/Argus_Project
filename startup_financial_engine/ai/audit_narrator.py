"""
ai/audit_narrator.py — AI-powered audit narrative generator.

Takes the structured AuditReport output and produces a CFO-quality memo
that explains findings in plain English, identifies root causes,
and suggests specific, actionable remediation steps.
"""

from __future__ import annotations

import json
from typing import Dict, Optional

from ai.client import SimulationContext, _call

# ─────────────────────────────────────────────────────────────────────────────
# Prompt builders
# ─────────────────────────────────────────────────────────────────────────────

_NARRATOR_SYSTEM = """
You are a Big-4 accounting partner reviewing a startup's financial model audit.
Your job is to write a clear, professional CFO-style memo that:

1. Summarises the overall audit health in 2-3 sentences.
2. For each significant finding (errors first, then warnings), explains:
   - What it means in plain English (not accounting jargon)
   - WHY it is happening given the business context
   - A specific, actionable remediation step with timeline
3. Ends with a 3-bullet "Immediate Actions" list — the top 3 things
   the founding team must do in the next 30 days.

Tone: Direct, professional, no fluff. Use dollar amounts and month references.
Format: Use section headers, bullet points where appropriate.
Length: 350-500 words.
"""


def _build_audit_prompt(ctx: SimulationContext, scenario: Optional[str] = None) -> str:
    targets = [scenario] if scenario else list(ctx.audit_reports.keys())

    findings_block = {}
    for scen in targets:
        report = ctx.audit_reports.get(scen)
        if report is None:
            continue
        findings_block[scen] = {
            "passed":   report["passed"],
            "errors":   report["errors"],
            "warnings": report["warnings"],
            "findings": report["findings"],
        }

    resilience_block = {
        scen: {
            "grade":            ctx.scenario_resilience[scen]["grade"],
            "runway_months":    ctx.scenario_resilience[scen]["runway_months"],
            "insolvency_month": ctx.scenario_resilience[scen].get("insolvency_month"),
        }
        for scen in ctx.scenario_resilience
    }

    prompt = (
        "Below is the output of an automated financial model audit for a startup. "
        "Write a CFO-style audit narrative memo.\n\n"
        "AUDIT FINDINGS:\n"
        + json.dumps(findings_block, indent=2)
        + "\n\nRESILIENCE CONTEXT:\n"
        + json.dumps(resilience_block, indent=2)
        + "\n\nBUSINESS CONTEXT:\n"
        + json.dumps({
            "starting_cash":   ctx.starting_cash,
            "events_applied":  [e["name"] for e in ctx.events],
            "assumptions":     ctx.assumptions,
        }, indent=2)
    )
    return prompt


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_audit_narrative(
    ctx: SimulationContext,
    scenario: Optional[str] = None,
) -> str:
    """
    Generate a full CFO-style audit narrative memo.

    Parameters
    ----------
    ctx      : SimulationContext from a completed simulation run
    scenario : If given, narrate only that scenario's audit. Otherwise all.

    Returns the narrative as a string (also streamed to stdout).
    """
    _print_header(scenario)
    prompt = _build_audit_prompt(ctx, scenario)
    return _call(_NARRATOR_SYSTEM, prompt, max_tokens=500)


def generate_finding_explanation(
    ctx: SimulationContext,
    finding_code: str,
) -> str:
    """
    Explain a single audit finding code in plain English with root-cause
    analysis and a concrete fix recommendation.
    """
    # Find the finding across all reports
    target_finding = None
    for report in ctx.audit_reports.values():
        for f in report.get("findings", []):
            if f.get("code") == finding_code:
                target_finding = f
                break
        if target_finding:
            break

    if target_finding is None:
        return f"Finding '{finding_code}' not found in audit reports."

    system = (
        "You are a CFO explaining a financial model audit finding to a non-accountant founder. "
        "Be clear, specific, and practical. In 150-200 words: explain what it means, "
        "why it happened in this specific business context, and what to do about it."
    )

    prompt = (
        f"Explain this audit finding in plain English:\n\n"
        f"{json.dumps(target_finding, indent=2)}\n\n"
        f"Business context:\n"
        f"Starting cash: ${ctx.starting_cash:,.0f}\n"
        f"Events applied: {[e['name'] for e in ctx.events]}\n"
        f"EXPECTED resilience grade: {ctx.scenario_resilience.get('EXPECTED', {}).get('grade', 'N/A')}"
    )

    print(f"\n📋 Explaining finding [{finding_code}]:\n")
    return _call(system, prompt, max_tokens=250)


def _print_header(scenario: Optional[str]) -> None:
    scope = f"Scenario: {scenario}" if scenario else "All Scenarios"
    print(f"\n{'═' * 70}")
    print(f"  🤖 AI AUDIT NARRATIVE — {scope}")
    print(f"{'═' * 70}\n")
