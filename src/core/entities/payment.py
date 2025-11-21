from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"


@dataclass
class Payment:
    id: Optional[int] = None
    user_id: Optional[int] = None
    phone_number: Optional[str] = None
    amount: float = 50.0
    status: PaymentStatus = PaymentStatus.PENDING
    yookassa_payment_id: Optional[str] = None
    created_at: Optional[datetime] = None

