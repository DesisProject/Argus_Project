"""
ai/client.py — Groq API wrapper for the financial simulation AI layer.

Setup:
    pip install groq
    export GROQ_API_KEY=your-key-from-console.groq.com  (free, no credit card)
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from groq import Groq

# ── Groq client setup ────────────────────────────────────────────────────────
_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

# Free tier model fallback chain
MODELS = [
    "llama-3.3-70b-versatile",   # best quality, generous free tier
    "llama3-8b-8192",            # smaller, higher rate limits
    "gemma2-9b-it",              # Google's model via Groq, free
]


# ─────────────────────────────────────────────────────────────────────────────
# Simulation context
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SimulationContext:
    assumptions:         dict
    starting_cash:       float
    timeline_map:        Dict[str, List[dict]]
    scenario_resilience: Dict[str, dict]
    all_signals:         Dict[str, List[dict]]
    audit_reports:       dict
    stress_results:      List[dict]
    monte_carlo:         dict
    events:              List[dict]
    chat_history:        List[dict] = field(default_factory=list)

    def _timeline_summary(self, scenario: str, n: int = 12) -> List[dict]:
        tl = self.timeline_map.get(scenario, [])
        return [
            {k: round(v, 2) if isinstance(v, float) else v
             for k, v in m.items() if k != "runway_months"}
            for m in tl[:n]
        ]

    def to_system_prompt(self) -> str:
        """Compact prompt — keeps tokens low for free tier."""
        mc   = self.monte_carlo
        exp  = self.scenario_resilience.get("EXPECTED", {})
        best = self.scenario_resilience.get("BEST", {})
        wrst = self.scenario_resilience.get("WORST", {})

        key_signals = [
            {"scenario": scen, "level": s["level"], "title": s["title"],
             "message": s["message"], "month": s.get("month")}
            for scen, sigs in self.all_signals.items()
            for s in sigs if s["level"] in ("critical", "warning")
        ]
        key_findings = [
            {"code": f["code"], "severity": f["severity"],
             "title": f["title"], "detail": f["detail"], "month": f.get("month")}
            for r in self.audit_reports.values()
            for f in r.get("findings", [])
            if f["severity"] in ("error", "warning")
        ]

        context = {
            "starting_cash": self.starting_cash,
            "events": [e["name"] for e in self.events],
            "assumptions": {k: v for k, v in self.assumptions.items()
                            if k != "monthly_unit_sales"},
            "resilience": {
                "BEST":     {"grade": best.get("grade"),
                             "runway_months": best.get("runway_months"),
                             "insolvency_month": best.get("insolvency_month"),
                             "ending_cash": best.get("ending_cash_balance")},
                "EXPECTED": {"grade": exp.get("grade"),
                             "runway_months": exp.get("runway_months"),
                             "insolvency_month": exp.get("insolvency_month"),
                             "ending_cash": exp.get("ending_cash_balance"),
                             "avg_burn": exp.get("average_monthly_burn")},
                "WORST":    {"grade": wrst.get("grade"),
                             "runway_months": wrst.get("runway_months"),
                             "insolvency_month": wrst.get("insolvency_month"),
                             "ending_cash": wrst.get("ending_cash_balance")},
            },
            "risk_signals": key_signals,
            "audit_findings": key_findings,
            "stress_tests": [
                {"shock": s["shock_name"], "grade": s["grade"],
                 "ending_cash": s["ending_cash"], "survives": s["survives"]}
                for s in self.stress_results
            ],
            "monte_carlo": {
                "survival_rate": mc.get("survival_rate"),
                "insolvency_probability": mc.get("insolvency_probability"),
                "avg_insolvency_month": mc.get("avg_insolvency_month"),
                "p10_cash": mc.get("p10_ending_cash"),
                "p90_cash": mc.get("p90_ending_cash"),
            },
            "expected_first_12_months": self._timeline_summary("EXPECTED", n=12),
        }

        return (
            "You are a senior startup CFO and financial analyst. "
            "Answer using ONLY the simulation data below. "
            "Be specific with months and dollar amounts. Be concise.\n\n"
            "SIMULATION DATA:\n" + json.dumps(context, indent=2)
        )


# ─────────────────────────────────────────────────────────────────────────────
# Low-level Groq calls — streaming with fallback
# ─────────────────────────────────────────────────────────────────────────────

def _try_stream(model: str, system: str, messages: List[dict], max_tokens: int) -> str:
    """Single streaming attempt with one model."""
    # Groq uses OpenAI-compatible format: role = user/assistant (not model)
    groq_messages = [{"role": "system", "content": system}] + [
        {"role": msg["role"], "content": msg["content"]}
        for msg in messages
    ]

    full_text = ""
    with _client.chat.completions.create(
        model=model,
        messages=groq_messages,
        max_tokens=max_tokens,
        stream=True,
    ) as stream:
        for chunk in stream:
            text = chunk.choices[0].delta.content or ""
            print(text, end="", flush=True)
            full_text += text

    print()
    return full_text


def _stream_response(system: str, messages: List[dict], max_tokens: int = 800) -> str:
    """Stream with automatic model fallback and rate-limit retry."""
    for model in MODELS:
        for attempt in range(2):
            try:
                if model != MODELS[0] or attempt > 0:
                    print(f"\n  [trying {model}] ", end="", flush=True)
                return _try_stream(model, system, messages, max_tokens)

            except Exception as e:
                err = str(e).lower()

                # Rate limit — wait and retry once
                if "rate_limit" in err or "429" in err or "rate limit" in err:
                    wait = 30
                    try:
                        # Extract wait time if present in error
                        if "please try again in" in err:
                            wait_str = err.split("please try again in")[1].split("s")[0].strip()
                            wait = int(float(wait_str)) + 2
                    except Exception:
                        pass
                    if attempt == 0:
                        print(f"\n  ⏳ Rate limit on {model}. Waiting {wait}s...")
                        time.sleep(wait)
                    else:
                        print(f"\n  ⚠️  {model} still limited, trying next...")
                        break
                else:
                    print(f"\n  ❌ {model}: {type(e).__name__}: {e}")
                    break  # non-rate-limit error, try next model

    return "\n[AI unavailable — all models rate limited. Wait 30s and try again.]\n"


def _call(system: str, user_message: str, max_tokens: int = 800) -> str:
    """Single-turn call with no history."""
    return _stream_response(system, [{"role": "user", "content": user_message}], max_tokens)
