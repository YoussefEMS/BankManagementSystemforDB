from sqlalchemy import text
from infra.db import get_engine


class ReportingDAO:
    def __init__(self):
        self.engine = get_engine()

    def account_summary(self, account_number: str) -> dict | None:
        sql = text(
            """
            SELECT
              a.account_number,
              c.name AS customer_name,
              SUM(CASE WHEN t.transaction_type IN ('DEPOSIT','TRANSFER_IN') THEN t.amount ELSE 0 END) AS total_in,
              SUM(CASE WHEN t.transaction_type IN ('WITHDRAWAL','TRANSFER_OUT') THEN t.amount ELSE 0 END) AS total_out,
              COUNT(DISTINCT o.event_id) AS overdraft_events
            FROM Accounts a
            JOIN Customers c ON c.customer_id = a.customer_id
            LEFT JOIN Transactions t ON t.account_number = a.account_number
            LEFT JOIN OverDraftEvents o ON o.account_number = a.account_number
            WHERE a.account_number = :account_number
            GROUP BY a.account_number, c.name
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"account_number": account_number}).mappings().fetchone()
            return dict(row) if row else None
