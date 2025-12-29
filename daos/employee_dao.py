from sqlalchemy import text
from infra.db import get_engine
from entities import Employee


class EmployeeDAO:
    def __init__(self):
        self.engine = get_engine()

    def _map(self, row) -> Employee:
        return Employee(
            employee_id=row.employee_id,
            username=row.username,
            name=row.name,
            email=row.email,
            phone=row.phone,
            role=row.role,
            status=row.status,
        )

    def authenticate(self, username: str, pin: str) -> Employee | None:
        sql = text(
            """
            SELECT employee_id, username, name, email, phone, role, status
            FROM Employees
            WHERE username = :username AND pin = :pin AND status = 'ACTIVE'
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"username": username, "pin": pin}).mappings().fetchone()
            return self._map(row) if row else None
