from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import text
from infra.db import get_engine
from entities import Account


class AccountDAO:
    def __init__(self):
        self.engine = get_engine()

    def _map(self, row) -> Account:
        return Account(
            account_number=row.account_number,
            customer_id=row.customer_id,
            account_type=row.account_type,
            balance=Decimal(row.balance),
            currency=row.currency,
            status=row.status,
            date_opened=row.date_opened,
        )

    def get_by_customer(self, customer_id: int) -> List[Account]:
        sql = text(
            """
            SELECT account_number, customer_id, account_type, balance, currency, status, date_opened
            FROM Accounts
            WHERE customer_id = :customer_id
            ORDER BY date_opened DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(sql, {"customer_id": customer_id}).mappings()
            return [self._map(r) for r in rows]

    def get_one(self, account_number: str) -> Optional[Account]:
        sql = text(
            """
            SELECT account_number, customer_id, account_type, balance, currency, status, date_opened
            FROM Accounts
            WHERE account_number = :account_number
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"account_number": account_number}).mappings().fetchone()
            return self._map(row) if row else None

    def update_balance(self, account_number: str, new_balance: Decimal, conn=None):
        sql = text(
            """
            UPDATE Accounts
            SET balance = :balance
            WHERE account_number = :account_number
            """
        )
        if conn:
            conn.execute(sql, {"balance": new_balance, "account_number": account_number})
        else:
            with self.engine.begin() as tx:
                tx.execute(sql, {"balance": new_balance, "account_number": account_number})

    def update_status(self, account_number: str, status: str):
        sql = text(
            """
            UPDATE Accounts
            SET status = :status
            WHERE account_number = :account_number
            """
        )
        with self.engine.begin() as conn:
            conn.execute(sql, {"status": status, "account_number": account_number})

    def create(
        self,
        account_number: str,
        customer_id: int,
        account_type: str,
        balance: Decimal,
        currency: str,
        status: str,
        date_opened: datetime,
        conn=None,
    ):
        sql = text(
            """
            INSERT INTO Accounts (account_number, customer_id, account_type, balance, currency, status, date_opened)
            VALUES (:account_number, :customer_id, :account_type, :balance, :currency, :status, :date_opened)
            """
        )
        params = {
            "account_number": account_number,
            "customer_id": customer_id,
            "account_type": account_type,
            "balance": balance,
            "currency": currency,
            "status": status,
            "date_opened": date_opened,
        }
        if conn:
            conn.execute(sql, params)
        else:
            with self.engine.begin() as tx:
                tx.execute(sql, params)
