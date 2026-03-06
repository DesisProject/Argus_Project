class IncomeStatement:
    def __init__(self, revenue, cogs, fixed_expenses):
        self.revenue = revenue
        self.cogs = cogs
        self.fixed_expenses = fixed_expenses

    def compute(self):
        statement = []

        for i in range(12):
            gross_profit = self.revenue[i] - self.cogs[i]
            operating_income = gross_profit - self.fixed_expenses

            statement.append({
                "month": i + 1,
                "revenue": self.revenue[i],
                "cogs": self.cogs[i],
                "gross_profit": gross_profit,
                "operating_income": operating_income
            })

        return statement