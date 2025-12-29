from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class OverDraftEvent:
    event_id: int
    account_number: str
    amount: Decimal
    occurred_at: datetime
    note: Optional[str]
    balance_after: Decimal
