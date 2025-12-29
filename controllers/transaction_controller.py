from datetime import datetime
from decimal import Decimal
from typing import Optional
from infra.db import get_engine
from daos import AccountDAO, TransactionDAO, OverDraftEventDAO
from entities import Transaction


class TransactionController:
    def __init__(self):
        self.account_dao = AccountDAO()
        self.transaction_dao = TransactionDAO()
        self.overdraft_dao = OverDraftEventDAO()
        self.engine = get_engine()

    def _ensure_account_active(self, account_number: str):
        account = self.account_dao.get_one(account_number)
        if not account:
            raise ValueError("Account not found")
        if account.status.upper() != "ACTIVE":
            raise ValueError("Account is not active")
        return account

    def deposit(self, account_number: str, amount: Decimal, performed_by: str, note: Optional[str] = None) -> Transaction:
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        account = self._ensure_account_active(account_number)
        new_balance = account.balance + amount
        with self.engine.begin() as conn:
            self.account_dao.update_balance(account_number, new_balance, conn=conn)
            txn_id = self.transaction_dao.add(
                account_number=account_number,
                transaction_type="DEPOSIT",
                amount=amount,
                performed_by=performed_by,
                note=note,
                balance_after=new_balance,
                reference_code=None,
                conn=conn,
            )
        return self._get_transaction(txn_id)

    def withdraw(self, account_number: str, amount: Decimal, performed_by: str, note: Optional[str] = None) -> Transaction:
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        account = self._ensure_account_active(account_number)
        if account.balance < amount:
            # Record overdraft attempt
            self.overdraft_dao.add_event(
                account_number=account_number,
                amount=amount,
                balance_after=account.balance,
                note="Overdraft attempt",
            )
            raise ValueError("Insufficient funds (overdraft recorded)")
        new_balance = account.balance - amount
        with self.engine.begin() as conn:
            self.account_dao.update_balance(account_number, new_balance, conn=conn)
            txn_id = self.transaction_dao.add(
                account_number=account_number,
                transaction_type="WITHDRAWAL",
                amount=amount,
                performed_by=performed_by,
                note=note,
                balance_after=new_balance,
                reference_code=None,
                conn=conn,
            )
        return self._get_transaction(txn_id)

    def history(
        self,
        account_number: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
    ) -> list[Transaction]:
        return self.transaction_dao.list_for_account(
            account_number=account_number,
            start_date=start_date,
            end_date=end_date,
            transaction_type=transaction_type,
        )

    def _get_transaction(self, txn_id: int) -> Transaction:
        txn = self.transaction_dao.get_by_id(txn_id)
        if not txn:
            raise RuntimeError("Transaction not found after creation")
        return txn
