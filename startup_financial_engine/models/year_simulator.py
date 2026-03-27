class YearSimulator:
    def __init__(self, assumptions):
        self.assumptions = assumptions

    def run_year(self):
        from models.revenue import RevenueModel
        from models.expenses import ExpenseModel
        from models.income_statement import IncomeStatement

        revenue_model = RevenueModel(self.assumptions)
        revenue = revenue_model.monthly_revenue()

        expense_model = ExpenseModel(self.assumptions)
        cogs = expense_model.monthly_cogs()
        fixed_exp = expense_model.monthly_fixed_expenses()

        income = IncomeStatement(revenue, cogs, fixed_exp)
        statement = income.compute()

        for month_data in statement:
            month_data["net_cash_flow"] = (
                month_data["revenue"] - month_data["cogs"] - fixed_exp
            )

        return statement
    
def apply_growth(base_assumptions, forecast_assumptions):
        from copy import deepcopy

        new_assumptions = deepcopy(base_assumptions)

        # Increase price (proxy for revenue growth)
        new_assumptions.price_per_unit *= (1 + forecast_assumptions.revenue_growth_rate)

        # Increase direct cost
        new_assumptions.cost_per_unit *= (1 + forecast_assumptions.cost_growth_rate)

        # Increase fixed expenses
        new_assumptions.rent *= (1 + forecast_assumptions.fixed_expense_growth_rate)
        new_assumptions.payroll *= (1 + forecast_assumptions.fixed_expense_growth_rate)
        new_assumptions.marketing *= (1 + forecast_assumptions.fixed_expense_growth_rate)
        new_assumptions.utilities *= (1 + forecast_assumptions.fixed_expense_growth_rate)

        return new_assumptions
