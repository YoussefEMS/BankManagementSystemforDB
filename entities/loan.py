from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Loan:
    loan_id: int
    account_number: str
    principal: Decimal
    balance_remaining: Decimal
    rate: Decimal
    term_months: int
    start_date: datetime
    status: str
    next_due_date: Optional[datetime]
