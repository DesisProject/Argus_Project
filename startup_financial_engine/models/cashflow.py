class CashFlow:
    def __init__(self):
        self.operating = []
        self.investing = []
        self.financing = []

    def record_operating(self, amount):
        self.operating.append(amount)

    def record_investing(self, amount):
        self.investing.append(amount)

    def record_financing(self, amount):
        self.financing.append(amount)

    def summary(self):
        return {
            "operating": sum(self.operating),
            "investing": sum(self.investing),
            "financing": sum(self.financing)
        }