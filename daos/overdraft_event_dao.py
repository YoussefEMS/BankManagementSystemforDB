from decimal import Decimal
from sqlalchemy import text
from infra.db import get_engine
from entities import OverDraftEvent


class OverDraftEventDAO:
    def __init__(self):
        self.engine = get_engine()

    def _map(self, row) -> OverDraftEvent:
        return OverDraftEvent(
            event_id=row.event_id,
            account_number=row.account_number,
            amount=Decimal(row.amount),
            occurred_at=row.occurred_at,
            note=row.note,
            balance_after=Decimal(row.balance_after),
        )

    def list_for_account(self, account_number: str) -> list[OverDraftEvent]:
        sql = text(
            """
            SELECT event_id, account_number, amount, occurred_at, note, balance_after
            FROM OverDraftEvents
            WHERE account_number = :account_number
            ORDER BY occurred_at DESC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(sql, {"account_number": account_number}).mappings()
            return [self._map(r) for r in rows]

    def add_event(self, account_number: str, amount: Decimal, balance_after: Decimal, note: str | None, conn=None):
        sql = text(
            """
            INSERT INTO OverDraftEvents (account_number, amount, occurred_at, note, balance_after)
            VALUES (:account_number, :amount, SYSUTCDATETIME(), :note, :balance_after)
            """
        )
        params = {
            "account_number": account_number,
            "amount": amount,
            "note": note,
            "balance_after": balance_after,
        }
        if conn:
            conn.execute(sql, params)
        else:
            with self.engine.begin() as tx:
                tx.execute(sql, params)

    def delete_older_than_days(self, days: int):
        sql = text(
            """
            DELETE FROM OverDraftEvents
            WHERE occurred_at < DATEADD(day, -:days, SYSUTCDATETIME())
            """
        )
        with self.engine.begin() as conn:
            conn.execute(sql, {"days": days})
