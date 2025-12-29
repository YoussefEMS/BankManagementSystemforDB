from decimal import Decimal
from daos import AccountDAO
from entities import Account


class AccountController:
    def __init__(self):
        self.dao = AccountDAO()

    def list_customer_accounts(self, customer_id: int) -> list[Account]:
        return self.dao.get_by_customer(customer_id)

    def get_balance(self, account_number: str) -> Decimal | None:
        acct = self.dao.get_one(account_number)
        return acct.balance if acct else None

    def set_status(self, account_number: str, status: str):
        self.dao.update_status(account_number, status)
