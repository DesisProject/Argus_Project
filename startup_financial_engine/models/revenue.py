class RevenueModel:
    def __init__(self, assumptions):
        self.assumptions = assumptions

    def monthly_revenue(self):
        revenue = []
        for units in self.assumptions.monthly_unit_sales: #looping through 12 values
            revenue.append(units * self.assumptions.price_per_unit) #revenue=Units Sold×Price Per Unit
        return revenue #list of revenue generated per month