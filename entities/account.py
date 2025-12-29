from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Account:
    account_number: str
    customer_id: int
    account_type: str
    balance: Decimal
    currency: str
    status: str
    date_opened: datetime
