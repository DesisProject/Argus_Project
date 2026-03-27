"""
year_simulator.py — Produces a 12-month income statement timeline
from a StartupAssumptions object.
"""

from __future__ import annotations
import copy
from typing import List

from models.assumptions import StartupAssumptions
from models.forecast import ForecastAssumptions


def monthly_depreciation(asset_cost: float, life_years: int) -> float:
    return asset_cost / (life_years * 12)


class YearSimulator:
    def __init__(self, assumptions: StartupAssumptions):
        self.a = assumptions

    def run_year(self) -> List[dict]:
        depr = monthly_depreciation(self.a.equipment_cost, self.a.equipment_life_years)
        fixed = self.a.rent + self.a.payroll + self.a.marketing + self.a.utilities

        timeline = []
        for i, units in enumerate(self.a.monthly_unit_sales):
            revenue = units * self.a.price_per_unit
            cogs = units * self.a.cost_per_unit
            gross_profit = revenue - cogs
            operating_income = gross_profit - fixed - depr
            timeline.append({
                "month": i + 1,
                "revenue": revenue,
                "cogs": cogs,
                "gross_profit": gross_profit,
                "operating_income": operating_income,
                "net_cash_flow": operating_income,  # simplified: no separate capex
                "cash_balance": 0.0,    # filled in by recalculate_cash
                "runway_months": 0.0,   # filled in by recalculate_cash
            })
        return timeline


def apply_growth(
    assumptions: StartupAssumptions,
    forecast: ForecastAssumptions,
) -> StartupAssumptions:
    """Return a new assumptions object with growth rates applied for the next year."""
    new = copy.deepcopy(assumptions)
    new.price_per_unit  *= (1 + forecast.revenue_growth_rate)
    new.cost_per_unit   *= (1 + forecast.cost_growth_rate)
    new.monthly_unit_sales = [
        u * (1 + forecast.revenue_growth_rate) for u in assumptions.monthly_unit_sales
    ]
    new.rent       *= (1 + forecast.fixed_expense_growth_rate)
    new.payroll    *= (1 + forecast.fixed_expense_growth_rate)
    new.marketing  *= (1 + forecast.fixed_expense_growth_rate)
    new.utilities  *= (1 + forecast.fixed_expense_growth_rate)
    return new
