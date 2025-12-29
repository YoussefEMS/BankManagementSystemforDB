from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import text
from infra.db import get_engine
from entities import Transaction


class TransactionDAO:
    def __init__(self):
        self.engine = get_engine()

    def _map(self, row) -> Transaction:
        return Transaction(
            transaction_id=row.transaction_id,
            account_number=row.account_number,
            transaction_type=row.transaction_type,
            amount=Decimal(row.amount),
            timestamp=row.timestamp,
            performed_by=row.performed_by,
            note=row.note,
            balance_after=Decimal(row.balance_after),
            reference_code=row.reference_code,
        )

    def list_for_account(
        self,
        account_number: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
    ) -> List[Transaction]:
        filters = ["account_number = :account_number"]
        params = {"account_number": account_number}
        if start_date:
            filters.append("timestamp >= :start_date")
            params["start_date"] = start_date
        if end_date:
            filters.append("timestamp <= :end_date")
            params["end_date"] = end_date
        if transaction_type and transaction_type.lower() != "all":
            filters.append("transaction_type = :transaction_type")
            params["transaction_type"] = transaction_type
        where_clause = " AND ".join(filters)

        sql = text(
            f"""
            SELECT transaction_id, account_number, transaction_type, amount, timestamp, performed_by, note, balance_after, reference_code
            FROM Transactions
            WHERE {where_clause}
            ORDER BY timestamp DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(sql, params).mappings()
            return [self._map(r) for r in rows]

    def add(
        self,
        account_number: str,
        transaction_type: str,
        amount: Decimal,
        performed_by: str,
        note: str | None,
        balance_after: Decimal,
        reference_code: str | None = None,
        conn=None,
    ) -> int:
        sql = text(
            """
            INSERT INTO Transactions (account_number, transaction_type, amount, timestamp, performed_by, note, balance_after, reference_code)
            OUTPUT INSERTED.transaction_id
            VALUES (:account_number, :transaction_type, :amount, SYSUTCDATETIME(), :performed_by, :note, :balance_after, :reference_code)
            """
        )
        params = {
            "account_number": account_number,
            "transaction_type": transaction_type,
            "amount": amount,
            "performed_by": performed_by,
            "note": note,
            "balance_after": balance_after,
            "reference_code": reference_code,
        }
        if conn:
            result = conn.execute(sql, params)
        else:
            with self.engine.begin() as tx:
                result = tx.execute(sql, params)
        row = result.fetchone()
        return int(row[0]) if row else 0

    def get_by_id(self, transaction_id: int) -> Transaction | None:
        sql = text(
            """
            SELECT transaction_id, account_number, transaction_type, amount, timestamp, performed_by, note, balance_after, reference_code
            FROM Transactions
            WHERE transaction_id = :transaction_id
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"transaction_id": transaction_id}).mappings().fetchone()
            return self._map(row) if row else None
