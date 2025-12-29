from datetime import datetime
from decimal import Decimal
from typing import List
from sqlalchemy import text
from infra.db import get_engine
from entities import Transfer


class TransferDAO:
    def __init__(self):
        self.engine = get_engine()

    def _map(self, row) -> Transfer:
        return Transfer(
            transfer_id=row.transfer_id,
            from_account=row.from_account,
            to_account=row.to_account,
            amount=Decimal(row.amount),
            timestamp=row.timestamp,
            status=row.status,
            note=row.note,
        )

    def list_for_account(self, account_number: str) -> List[Transfer]:
        sql = text(
            """
            SELECT transfer_id, from_account, to_account, amount, timestamp, status, note
            FROM Transfers
            WHERE from_account = :acct OR to_account = :acct
            ORDER BY timestamp DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(sql, {"acct": account_number}).mappings()
            return [self._map(r) for r in rows]

    def add(
        self,
        from_account: str,
        to_account: str,
        amount: Decimal,
        status: str,
        note: str | None,
        conn=None,
    ) -> int:
        sql = text(
            """
            INSERT INTO Transfers (from_account, to_account, amount, timestamp, status, note)
            OUTPUT INSERTED.transfer_id
            VALUES (:from_account, :to_account, :amount, SYSUTCDATETIME(), :status, :note)
            """
        )
        params = {
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "status": status,
            "note": note,
        }
        if conn:
            result = conn.execute(sql, params)
        else:
            with self.engine.begin() as tx:
                result = tx.execute(sql, params)
        row = result.fetchone()
        return int(row[0]) if row else 0
