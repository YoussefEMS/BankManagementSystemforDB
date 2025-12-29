from datetime import datetime
from decimal import Decimal
from infra.db import get_engine
from daos import LoanDAO, AccountDAO
from entities import Loan


class LoanController:
    def __init__(self):
        self.loan_dao = LoanDAO()
        self.account_dao = AccountDAO()
        self.engine = get_engine()

    def request_loan(self, account_number: str, principal: Decimal, rate: Decimal, term_months: int) -> Loan:
        if principal <= 0:
            raise ValueError("Principal must be greater than zero")
        if term_months <= 0:
            raise ValueError("Term must be greater than zero")

        account = self.account_dao.get_one(account_number)
        if not account:
            raise ValueError("Account not found")
        if account.status.upper() != "ACTIVE":
            raise ValueError("Account is not active")

        start_date = datetime.utcnow()
        with self.engine.begin() as conn:
            loan_id = self.loan_dao.request(
                account_number=account_number,
                principal=principal,
                rate=rate,
                term_months=term_months,
                start_date=start_date,
                status="PENDING",
                conn=conn,
            )
        loan = self.loan_dao.get_by_id(loan_id)
        if not loan:
            raise RuntimeError("Loan not found after creation")
        return loan

    def list_loans(self, account_number: str) -> list[Loan]:
        return self.loan_dao.list_for_account(account_number)

    def update_status(self, loan_id: int, status: str):
        self.loan_dao.update_status(loan_id, status)
