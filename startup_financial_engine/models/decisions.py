from dataclasses import dataclass
from typing import List

@dataclass
class DecisionImpact:
    scenario_type: str  # "BEST", "EXPECTED", or "WORST"
    revenue_boost: float  
    cost_change: float    
    delay_months: int = 0  # <--- NEW: Defaults to 0 if no delay is provided

@dataclass
class InternalDecision:
    name: str
    start_month: int      
    upfront_cost: float   
    recurring_cost: float 
    impacts: List[DecisionImpact]