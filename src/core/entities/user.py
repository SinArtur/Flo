from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: Optional[int] = None
    user_id: Optional[int] = None  # Telegram user ID
    username: Optional[str] = None
    consent_given_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

