class ExpenseModel:
    def __init__(self, assumptions):
        self.assumptions = assumptions

    def monthly_cogs(self):
        cogs = []
        for units in self.assumptions.monthly_unit_sales:
            cogs.append(units * self.assumptions.cost_per_unit)
        return cogs

    def monthly_fixed_expenses(self):
        return (
            self.assumptions.rent +
            self.assumptions.payroll +
            self.assumptions.marketing +
            self.assumptions.utilities
        )