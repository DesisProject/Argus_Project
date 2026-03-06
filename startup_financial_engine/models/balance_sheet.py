class BalanceSheet:
    def __init__(self, assumptions, income_statement):
        self.assumptions = assumptions
        self.income_statement = income_statement

        self.cash = assumptions.owner_equity + assumptions.loan_amount \
                    - assumptions.equipment_cost \
                    - assumptions.buildout_cost

        self.loan_balance = assumptions.loan_amount
        self.equipment_value = assumptions.equipment_cost
        self.retained_earnings = 0

    def update_month(self, month_data, depreciation):
        # Update cash
        self.cash += month_data["operating_income"]

        # Apply depreciation
        self.equipment_value -= depreciation

        # Update retained earnings
        self.retained_earnings += month_data["operating_income"]

    def snapshot(self):
        return {
            "cash": self.cash,
            "equipment_value": self.equipment_value,
            "loan_balance": self.loan_balance,
            "equity": self.assumptions.owner_equity + self.retained_earnings
        }