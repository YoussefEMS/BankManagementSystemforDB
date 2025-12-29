from dataclasses import dataclass
from typing import Optional
from daos import AuthDAO, EmployeeDAO, AccountDAO
from entities import Customer, Account, Employee


@dataclass
class SessionContext:
    role: str  # "customer" or "employee"
    customer: Optional[Customer]
    employee: Optional[Employee]
    accounts: list[Account]


class AuthController:
    def __init__(self):
        self.customer_auth = AuthDAO()
        self.employee_auth = EmployeeDAO()
        self.account_dao = AccountDAO()

    def login(self, username: str, pin: str) -> SessionContext | None:
        customer = self.customer_auth.authenticate(username=username, pin=pin)
        if customer:
            accounts = self.account_dao.get_by_customer(customer.customer_id)
            return SessionContext(role="customer", customer=customer, employee=None, accounts=accounts)

        employee = self.employee_auth.authenticate(username=username, pin=pin)
        if employee:
            return SessionContext(role="employee", customer=None, employee=employee, accounts=[])

        return None
