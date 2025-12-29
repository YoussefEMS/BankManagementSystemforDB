from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import text
from infra.db import get_engine
from entities import Loan


class LoanDAO:
    def __init__(self):
        self.engine = get_engine()

    def _map(self, row) -> Loan:
        return Loan(
            loan_id=row.loan_id,
            account_number=row.account_number,
            principal=Decimal(row.principal),
            balance_remaining=Decimal(row.balance_remaining),
            rate=Decimal(row.rate),
            term_months=row.term_months,
            start_date=row.start_date,
            status=row.status,
            next_due_date=row.next_due_date,
        )

    def list_for_account(self, account_number: str) -> List[Loan]:
        sql = text(
            """
            SELECT loan_id, account_number, principal, balance_remaining, rate, term_months, start_date, status, next_due_date
            FROM Loans
            WHERE account_number = :account_number
            ORDER BY start_date DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(sql, {"account_number": account_number}).mappings()
            return [self._map(r) for r in rows]

    def list_all(self) -> List[Loan]:
        sql = text(
            """
            SELECT loan_id, account_number, principal, balance_remaining, rate, term_months, start_date, status, next_due_date
            FROM Loans
            ORDER BY start_date DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(sql).mappings()
            return [self._map(r) for r in rows]

    def get_by_id(self, loan_id: int) -> Loan | None:
        sql = text(
            """
            SELECT loan_id, account_number, principal, balance_remaining, rate, term_months, start_date, status, next_due_date
            FROM Loans
            WHERE loan_id = :loan_id
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"loan_id": loan_id}).mappings().fetchone()
            return self._map(row) if row else None

    def request(
        self,
        account_number: str,
        principal: Decimal,
        rate: Decimal,
        term_months: int,
        start_date: datetime,
        status: str,
        conn=None,
    ) -> int:
        sql = text(
            """
            INSERT INTO Loans (account_number, principal, balance_remaining, rate, term_months, start_date, status)
            OUTPUT INSERTED.loan_id
            VALUES (:account_number, :principal, :principal, :rate, :term_months, :start_date, :status)
            """
        )
        params = {
            "account_number": account_number,
            "principal": principal,
            "rate": rate,
            "term_months": term_months,
            "start_date": start_date,
            "status": status,
        }
        if conn:
            result = conn.execute(sql, params)
        else:
            with self.engine.begin() as tx:
                result = tx.execute(sql, params)
        row = result.fetchone()
        return int(row[0]) if row else 0

    def update_status(self, loan_id: int, status: str):
        sql = text("UPDATE Loans SET status = :status WHERE loan_id = :loan_id")
        with self.engine.begin() as conn:
            conn.execute(sql, {"status": status, "loan_id": loan_id})

    def delete_pending(self, loan_id: int):
        sql = text("DELETE FROM Loans WHERE loan_id = :loan_id AND status = 'PENDING'")
        with self.engine.begin() as conn:
            conn.execute(sql, {"loan_id": loan_id})
