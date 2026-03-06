from dataclasses import dataclass

@dataclass
class StartupAssumptions:
    # Revenue assumptions
    price_per_unit: float #selling price of 1 unit of the product
    monthly_unit_sales: list  # a list containing 12 values, each value = units sold in that month
    
    # Direct costs
    cost_per_unit: float #cost to produce 1 unit of the product
    
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
