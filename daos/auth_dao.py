from sqlalchemy import text
from infra.db import get_engine
from entities import Customer


class AuthDAO:
    def __init__(self):
        self.engine = get_engine()

    def _map(self, row) -> Customer:
        return Customer(
            customer_id=row.customer_id,
            name=row.name,
            national_id=row.national_id,
            email=row.email,
            phone=row.phone,
            address=row.address,
            status=row.status,
            pin=row.pin,
        )

    def authenticate(self, username: str, pin: str) -> Customer | None:
        sql = text(
            """
            SELECT customer_id, name, national_id, email, phone, address, status, pin
            FROM Customers
            WHERE username = :username AND pin = :pin AND status = 'ACTIVE'
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(sql, {"username": username, "pin": pin}).mappings().fetchone()
            return self._map(row) if row else None

    def create_customer(
        self,
        username: str,
        pin: str,
        name: str,
        email: str,
        phone: str | None,
        address: str | None,
        national_id: str,
    ):
        sql = text(
            """
            INSERT INTO Customers (username, pin, name, email, phone, address, status, national_id)
            VALUES (:username, :pin, :name, :email, :phone, :address, 'ACTIVE', :national_id)
            """
        )
        with self.engine.begin() as conn:
            conn.execute(
                sql,
                {
                    "username": username,
                    "pin": pin,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "address": address,
                    "national_id": national_id,
                },
            )

    def list_all(self) -> list[Customer]:
        sql = text(
            """
            SELECT customer_id, name, national_id, email, phone, address, status, pin
            FROM Customers
            ORDER BY customer_id ASC
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(sql).mappings()
            return [self._map(r) for r in rows]
