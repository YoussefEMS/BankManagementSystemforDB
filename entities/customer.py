from dataclasses import dataclass
from typing import Optional


@dataclass
class Customer:
    customer_id: int
    name: str
    national_id: str
    email: str
    phone: Optional[str]
    address: Optional[str]
    status: str
    pin: str
