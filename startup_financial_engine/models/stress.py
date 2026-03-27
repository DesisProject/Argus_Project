from copy import deepcopy
import random
from models.year_simulator import YearSimulator


class StressTester:

    def apply_shock(self, assumptions, shock_type):
        shocked = deepcopy(assumptions)

        if shock_type == "demand_crash":
            shocked.monthly_unit_sales = [
                int(x * 0.5) for x in shocked.monthly_unit_sales
            ]

        elif shock_type == "cost_spike":
            shocked.cost_per_unit *= 1.5

        elif shock_type == "expense_inflation":
            shocked.rent *= 1.3
            shocked.payroll *= 1.3
            shocked.marketing *= 1.2

        return shocked
    
    def _calculate_cash_metrics_local(self, timeline, starting_cash):
        current_cash = starting_cash
        for m in timeline:
            current_cash += m["net_cash_flow"]
            m["cash_balance"] = current_cash

    def monte_carlo(self, base_assumptions, starting_cash, simulations=50):
        results = []

        for _ in range(simulations):
            sim_assumptions = deepcopy(base_assumptions)

            # random variations
            sim_assumptions.price_per_unit *= random.uniform(0.8, 1.2)
            sim_assumptions.cost_per_unit *= random.uniform(0.9, 1.3)

            timeline = YearSimulator(sim_assumptions).run_year()

            # compute cash properly
            self._calculate_cash_metrics_local(timeline, starting_cash)

            final_cash = timeline[-1]["cash_balance"]

            results.append(final_cash)

        return results
