from dataclasses import dataclass

@dataclass
class ForecastAssumptions:
    revenue_growth_rate: float
    cost_growth_rate: float
    fixed_expense_growth_rate: float
