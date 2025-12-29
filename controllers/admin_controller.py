from daos import AuthDAO, AccountDAO, LoanDAO


class AdminController:
    def __init__(self):
        self.auth_dao = AuthDAO()
        self.account_dao = AccountDAO()
        self.loan_dao = LoanDAO()

    def list_customers(self):
        return self.auth_dao.list_all()

    def list_accounts_for_customer(self, customer_id: int):
        return self.account_dao.get_by_customer(customer_id)

    def update_account_status(self, account_number: str, status: str):
        self.account_dao.update_status(account_number, status)

    def update_loan_status(self, loan_id: int, status: str):
        self.loan_dao.update_status(loan_id, status)

    def list_loans(self, account_number: str):
        return self.loan_dao.list_for_account(account_number)
