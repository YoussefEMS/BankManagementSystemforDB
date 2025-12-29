from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Transfer:
    transfer_id: int
    from_account: str
    to_account: str
    amount: Decimal
    timestamp: datetime
    status: str
    note: Optional[str]
