from dataclasses import dataclass
from typing import Optional


@dataclass
class Employee:
    employee_id: int
    username: str
    name: str
    email: str
    phone: Optional[str]
    role: str
    status: str
