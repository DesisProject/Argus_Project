"""
assumptions.py — Validated startup financial assumptions.
Includes field-level validation and serialization helpers.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class StartupAssumptions:
    # Revenue
    price_per_unit: float
    monthly_unit_sales: List[float]

    # Direct costs
    cost_per_unit: float

    # Fixed monthly expenses
    rent: float
    payroll: float
    marketing: float
    utilities: float

    # One-time startup costs
    equipment_cost: float
    buildout_cost: float

    # Funding
    owner_equity: float
    loan_amount: float
    loan_interest_rate: float

    # Depreciation
    equipment_life_years: int

    def __post_init__(self):
        self._validate()

    def _validate(self):
        errors = []
        if self.price_per_unit <= 0:
            errors.append("price_per_unit must be > 0")
        if self.cost_per_unit < 0:
            errors.append("cost_per_unit must be >= 0")
        if self.cost_per_unit >= self.price_per_unit:
            errors.append("cost_per_unit must be < price_per_unit (negative margin)")
        if len(self.monthly_unit_sales) != 12:
            errors.append(f"monthly_unit_sales must have 12 values, got {len(self.monthly_unit_sales)}")
        if any(u < 0 for u in self.monthly_unit_sales):
            errors.append("monthly_unit_sales values must be >= 0")
        if self.equipment_life_years <= 0:
            errors.append("equipment_life_years must be > 0")
        if self.owner_equity < 0 or self.loan_amount < 0:
            errors.append("Funding amounts must be >= 0")
        if errors:
            raise ValueError("StartupAssumptions validation failed:\n  " + "\n  ".join(errors))

    @property
    def starting_cash(self) -> float:
        return (
            self.owner_equity
            + self.loan_amount
            - self.equipment_cost
            - self.buildout_cost
        )

    def to_dict(self) -> dict:
        return {
            "price_per_unit": self.price_per_unit,
            "monthly_unit_sales": self.monthly_unit_sales,
            "cost_per_unit": self.cost_per_unit,
            "rent": self.rent,
            "payroll": self.payroll,
            "marketing": self.marketing,
            "utilities": self.utilities,
            "equipment_cost": self.equipment_cost,
            "buildout_cost": self.buildout_cost,
            "owner_equity": self.owner_equity,
            "loan_amount": self.loan_amount,
            "loan_interest_rate": self.loan_interest_rate,
            "equipment_life_years": self.equipment_life_years,
            "starting_cash": self.starting_cash,
        }
