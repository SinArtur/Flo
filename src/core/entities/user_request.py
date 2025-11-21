from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class UserRequest:
    id: Optional[int] = None
    user_id: Optional[int] = None
    phone_number: Optional[str] = None
    calculated_date: Optional[date] = None
    cycle_number: int = 1
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

