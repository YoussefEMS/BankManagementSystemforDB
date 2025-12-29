from daos import ReportingDAO


class ReportController:
    def __init__(self):
        self.dao = ReportingDAO()

    def account_summary(self, account_number: str) -> dict | None:
        return self.dao.account_summary(account_number)
