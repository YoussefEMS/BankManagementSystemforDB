from daos import AuthDAO, AccountDAO, LoanDAO, OverDraftEventDAO
from entities import Customer


class EmployeeController:
    """
    Employee-facing operations: create customers, view accounts, review/update loans, update account status.
    """

    def __init__(self):
        self.customer_dao = AuthDAO()
        self.account_dao = AccountDAO()
        self.loan_dao = LoanDAO()
        self.overdraft_dao = OverDraftEventDAO()

    def create_customer(
        self,
        username: str,
        pin: str,
        name: str,
        email: str,
        phone: str | None,
        address: str | None,
        national_id: str,
    ) -> Customer:
        self.customer_dao.create_customer(
            username=username,
            pin=pin,
            name=name,
            email=email,
            phone=phone,
            address=address,
            national_id=national_id,
        )
        return self.customer_dao.authenticate(username=username, pin=pin)  # return the newly created record

    def list_accounts_for_customer(self, customer_id: int):
        return self.account_dao.get_by_customer(customer_id)

    def list_all_loans(self):
        return self.loan_dao.list_all()

    def update_loan_status(self, loan_id: int, status: str):
        self.loan_dao.update_status(loan_id, status)

    def update_account_status(self, account_number: str, status: str):
        self.account_dao.update_status(account_number, status)

    def delete_pending_loan(self, loan_id: int):
        self.loan_dao.delete_pending(loan_id)

    def delete_overdraft_events(self, days: int):
        self.overdraft_dao.delete_older_than_days(days)
