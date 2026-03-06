from dataclasses import dataclass

@dataclass
class ForecastAssumptions:
    revenue_growth_rate: float      # e.g. 0.08 for 8%
    cost_growth_rate: float         # inflation
    fixed_expense_growth_rate: float