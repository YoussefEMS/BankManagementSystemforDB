from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Transaction:
    transaction_id: int
    account_number: str
    transaction_type: str
    amount: Decimal
    timestamp: datetime
    performed_by: str
    note: Optional[str]
    balance_after: Decimal
    reference_code: Optional[str]
