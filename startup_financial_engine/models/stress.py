"""
stress_testing.py — Financial stress testing engine.

Provides:
  - Parametric shocks  (revenue drop, cost spike, churn surge, etc.)
  - Monte Carlo simulation  (randomised uncertainty across all inputs)
  - Sensitivity matrix  (single-variable sweeps)
  - Stress report aggregation
"""

from __future__ import annotations

import copy
import math
import random
import statistics
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from resilience import summarize_resilience, GRADE_RANK


# ---------------------------------------------------------------------------
# Shock definitions
# ---------------------------------------------------------------------------

@dataclass
class Shock:
    """
    Describes a single parametric shock applied to a timeline.

    apply_fn receives (timeline: list[dict]) and mutates it in-place.
    """
    name: str
    description: str
    apply_fn: Callable[[List[dict]], None]

    def apply(self, timeline: List[dict]) -> List[dict]:
        shocked = copy.deepcopy(timeline)
        self.apply_fn(shocked)
        return shocked


def _revenue_drop_shock(pct: float, start_month: int = 1) -> Shock:
    """Reduce revenue by `pct` fraction from `start_month` onward."""
    label = f"Revenue Drop {int(pct * 100)}%"
    def fn(timeline):
        for idx, m in enumerate(timeline):
            if idx + 1 >= start_month:
                drop = m.get("revenue", 0) * pct
                m["revenue"] -= drop
                m["gross_profit"] -= drop
                m["operating_income"] -= drop
                m["net_cash_flow"] -= drop
    return Shock(label, f"Permanent {int(pct * 100)}% revenue reduction from month {start_month}", fn)


def _cost_spike_shock(pct: float, start_month: int = 1) -> Shock:
    """Increase all costs (COGS + opex) by `pct` fraction."""
    label = f"Cost Spike {int(pct * 100)}%"
    def fn(timeline):
        for idx, m in enumerate(timeline):
            if idx + 1 >= start_month:
                cogs_inc = m.get("cogs", 0) * pct
                opex_inc = abs(m.get("operating_income", 0) - m.get("gross_profit", 0)) * pct
                total_inc = cogs_inc + opex_inc
                m["cogs"] += cogs_inc
                m["gross_profit"] -= cogs_inc
                m["operating_income"] -= total_inc
                m["net_cash_flow"] -= total_inc
    return Shock(label, f"All costs increase {int(pct * 100)}% from month {start_month}", fn)


def _customer_churn_shock(churn_pct: float, start_month: int = 1) -> Shock:
    """Model customer churn as a compounding revenue reduction."""
    label = f"Customer Churn {int(churn_pct * 100)}%/mo"
    def fn(timeline):
        retention = 1.0
        for idx, m in enumerate(timeline):
            if idx + 1 >= start_month:
                retention *= (1 - churn_pct)
            rev_loss = m.get("revenue", 0) * (1 - retention)
            m["revenue"] -= rev_loss
            m["gross_profit"] -= rev_loss
            m["operating_income"] -= rev_loss
            m["net_cash_flow"] -= rev_loss
    return Shock(label, f"Compounding {int(churn_pct * 100)}%/month customer churn from month {start_month}", fn)


def _delayed_start_shock(delay_months: int) -> Shock:
    """Shift all revenue forward by N months (simulates launch delay)."""
    label = f"Launch Delay {delay_months}mo"
    def fn(timeline):
        revenues = [m.get("revenue", 0) for m in timeline]
        delayed = [0.0] * min(delay_months, len(revenues)) + revenues
        for idx, m in enumerate(timeline):
            new_rev = delayed[idx]
            old_rev = m.get("revenue", 0)
            loss = old_rev - new_rev
            m["revenue"] = new_rev
            m["gross_profit"] -= loss
            m["operating_income"] -= loss
            m["net_cash_flow"] -= loss
    return Shock(label, f"Revenue delayed by {delay_months} months", fn)


def _interest_rate_shock(rate_increase: float) -> Shock:
    """Increase monthly financing cost by additional annual rate."""
    label = f"Rate Hike +{int(rate_increase * 100)}%"
    def fn(timeline):
        # Rough proxy: add monthly interest on average cash balance
        for m in timeline:
            monthly_cost = m.get("cash_balance", 0) * (rate_increase / 12)
            if monthly_cost > 0:
                m["operating_income"] -= monthly_cost
                m["net_cash_flow"] -= monthly_cost
    return Shock(label, f"Interest rate increases by {int(rate_increase * 100)}% annualised", fn)


# Pre-built standard shock library
STANDARD_SHOCKS: Dict[str, Shock] = {
    "revenue_drop_10": _revenue_drop_shock(0.10),
    "revenue_drop_20": _revenue_drop_shock(0.20),
    "revenue_drop_30": _revenue_drop_shock(0.30),
    "revenue_drop_50": _revenue_drop_shock(0.50),
    "cost_spike_15":   _cost_spike_shock(0.15),
    "cost_spike_30":   _cost_spike_shock(0.30),
    "churn_5pct":      _customer_churn_shock(0.05),
    "churn_10pct":     _customer_churn_shock(0.10),
    "delay_3mo":       _delayed_start_shock(3),
    "delay_6mo":       _delayed_start_shock(6),
    "rate_hike_2pct":  _interest_rate_shock(0.02),
}


# ---------------------------------------------------------------------------
# Stress test runner
# ---------------------------------------------------------------------------

def _recalculate_cash(timeline: List[dict], starting_cash: float) -> List[dict]:
    """Re-derive cash_balance and runway_months after a shock."""
    cash = starting_cash
    for m in timeline:
        cash += m.get("net_cash_flow", 0)
        m["cash_balance"] = cash
        burn = -m.get("net_cash_flow", 0)
        m["runway_months"] = (cash / burn) if burn > 0 else 999.0
    return timeline


@dataclass
class StressResult:
    shock_name: str
    description: str
    grade: str
    score: int
    grade_drop: int          # vs. baseline
    insolvency_month: Optional[int]
    runway_months: float
    ending_cash: float
    survives: bool
    resilience: dict = field(repr=False)


def run_stress_tests(
    baseline_timeline: List[dict],
    starting_cash: float,
    shocks: Optional[Dict[str, Shock]] = None,
) -> List[StressResult]:
    """
    Apply each shock to the baseline timeline and return ranked results.

    Parameters
    ----------
    baseline_timeline : pre-calculated timeline (cash_balance populated)
    starting_cash     : day-0 cash position
    shocks            : dict of Shock objects; defaults to STANDARD_SHOCKS
    """
    if shocks is None:
        shocks = STANDARD_SHOCKS

    baseline_resilience = summarize_resilience(baseline_timeline)
    baseline_grade_rank = GRADE_RANK.get(baseline_resilience["grade"], 0)

    results: List[StressResult] = []

    for shock_key, shock in shocks.items():
        shocked_timeline = shock.apply(baseline_timeline)
        _recalculate_cash(shocked_timeline, starting_cash)
        resilience = summarize_resilience(shocked_timeline)

        grade_rank = GRADE_RANK.get(resilience["grade"], 0)
        grade_drop = baseline_grade_rank - grade_rank

        results.append(StressResult(
            shock_name=shock.name,
            description=shock.description,
            grade=resilience["grade"],
            score=resilience["score"],
            grade_drop=grade_drop,
            insolvency_month=resilience.get("insolvency_month"),
            runway_months=resilience.get("runway_months", 0),
            ending_cash=resilience.get("ending_cash_balance", 0),
            survives=resilience.get("survives_horizon", False),
            resilience=resilience,
        ))

    # Sort: worst outcomes first
    results.sort(key=lambda r: (r.grade_drop, -r.runway_months), reverse=True)
    return results


# ---------------------------------------------------------------------------
# Monte Carlo simulation
# ---------------------------------------------------------------------------

@dataclass
class MonteCarloConfig:
    iterations: int = 1000
    revenue_std_pct: float = 0.15      # ±15% monthly revenue volatility
    cost_std_pct: float = 0.08         # ±8%  monthly cost volatility
    seed: Optional[int] = None


@dataclass
class MonteCarloResult:
    iterations: int
    survival_rate: float               # fraction that survive horizon
    median_ending_cash: float
    p10_ending_cash: float             # 10th percentile (pessimistic)
    p90_ending_cash: float             # 90th percentile (optimistic)
    median_runway_months: float
    insolvency_probability: float
    avg_insolvency_month: Optional[float]
    grade_distribution: Dict[str, float]  # grade → fraction
    var_95: float                         # Value-at-Risk: 5th pct ending cash


def run_monte_carlo(
    baseline_timeline: List[dict],
    starting_cash: float,
    config: Optional[MonteCarloConfig] = None,
) -> MonteCarloResult:
    """
    Run Monte Carlo simulation on the baseline timeline.
    Each iteration randomly perturbs revenue and costs, then re-calculates
    cash and resilience.
    """
    if config is None:
        config = MonteCarloConfig()

    rng = random.Random(config.seed)
    ending_cashes: List[float] = []
    runways: List[float] = []
    insolvent_months: List[int] = []
    grade_counts: Dict[str, int] = {}
    survivors = 0

    for _ in range(config.iterations):
        trial = copy.deepcopy(baseline_timeline)

        for m in trial:
            rev_shock = rng.gauss(1.0, config.revenue_std_pct)
            cost_shock = rng.gauss(1.0, config.cost_std_pct)

            old_rev = m.get("revenue", 0)
            old_cogs = m.get("cogs", 0)

            new_rev = max(old_rev * rev_shock, 0)
            new_cogs = min(max(old_cogs * cost_shock, 0), new_rev)

            delta_rev = new_rev - old_rev
            delta_cogs = new_cogs - old_cogs
            delta_gp = delta_rev - delta_cogs

            m["revenue"] = new_rev
            m["cogs"] = new_cogs
            m["gross_profit"] = m.get("gross_profit", 0) + delta_gp
            m["operating_income"] = m.get("operating_income", 0) + delta_gp
            m["net_cash_flow"] = m.get("net_cash_flow", 0) + delta_gp

        _recalculate_cash(trial, starting_cash)
        res = summarize_resilience(trial)

        ending_cashes.append(res["ending_cash_balance"])
        runways.append(res["runway_months"])
        grade_counts[res["grade"]] = grade_counts.get(res["grade"], 0) + 1

        if res["survives_horizon"]:
            survivors += 1
        else:
            insolvent_months.append(res["insolvency_month"] or 0)

    n = config.iterations
    ending_cashes.sort()

    return MonteCarloResult(
        iterations=n,
        survival_rate=survivors / n,
        median_ending_cash=statistics.median(ending_cashes),
        p10_ending_cash=ending_cashes[int(n * 0.10)],
        p90_ending_cash=ending_cashes[int(n * 0.90)],
        median_runway_months=statistics.median(runways),
        insolvency_probability=(n - survivors) / n,
        avg_insolvency_month=statistics.mean(insolvent_months) if insolvent_months else None,
        grade_distribution={g: c / n for g, c in grade_counts.items()},
        var_95=ending_cashes[int(n * 0.05)],
    )


# ---------------------------------------------------------------------------
# Sensitivity matrix
# ---------------------------------------------------------------------------

@dataclass
class SensitivityPoint:
    variable: str
    value: float
    grade: str
    ending_cash: float
    runway_months: float
    insolvency_month: Optional[int]


def run_sensitivity_sweep(
    baseline_timeline: List[dict],
    starting_cash: float,
    variable: str = "revenue",
    sweep_range: Tuple[float, float] = (-0.40, 0.40),
    steps: int = 9,
) -> List[SensitivityPoint]:
    """
    Sweep a single variable (revenue or cost multiplier) across a range
    and record resilience at each point.

    variable: "revenue" | "cost"
    """
    results: List[SensitivityPoint] = []
    step_size = (sweep_range[1] - sweep_range[0]) / (steps - 1)

    for i in range(steps):
        multiplier = sweep_range[0] + i * step_size
        trial = copy.deepcopy(baseline_timeline)

        for m in trial:
            if variable == "revenue":
                old_rev = m.get("revenue", 0)
                delta = old_rev * multiplier
                m["revenue"] += delta
                m["gross_profit"] += delta
                m["operating_income"] += delta
                m["net_cash_flow"] += delta
            elif variable == "cost":
                old_cogs = m.get("cogs", 0)
                delta = old_cogs * multiplier
                m["cogs"] += delta
                m["gross_profit"] -= delta
                m["operating_income"] -= delta
                m["net_cash_flow"] -= delta

        _recalculate_cash(trial, starting_cash)
        res = summarize_resilience(trial)

        results.append(SensitivityPoint(
            variable=variable,
            value=round(multiplier * 100, 1),  # as percentage
            grade=res["grade"],
            ending_cash=res["ending_cash_balance"],
            runway_months=res["runway_months"],
            insolvency_month=res.get("insolvency_month"),
        ))

    return results
