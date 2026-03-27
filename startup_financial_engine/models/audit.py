class AuditEngine:
    def run_audit(self, timeline):
        issues = []

        for month in timeline:
            m = month["month"]

            # 1. Negative revenue
            if month["revenue"] < 0:
                issues.append(f"[Month {m}] Negative revenue detected")

            # 2. COGS > Revenue
            if month["cogs"] > month["revenue"]:
                issues.append(f"[Month {m}] COGS exceeds revenue")

            # 3. Extreme burn
            if month["net_cash_flow"] < -100000:
                issues.append(f"[Month {m}] Extreme burn rate")

            # 4. Unrealistic margin
            if month["revenue"] > 0:
                margin = (month["revenue"] - month["cogs"]) / month["revenue"]
                if margin < 0:
                    issues.append(f"[Month {m}] Negative gross margin")

        return issues
