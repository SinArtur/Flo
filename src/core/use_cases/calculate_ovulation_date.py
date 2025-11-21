from datetime import date, datetime, timedelta
from typing import Optional
import hashlib
from src.core.entities.user_request import UserRequest
from src.core.interfaces.request_repository import IRequestRepository


class CalculateOvulationDateUseCase:
    def __init__(self, request_repo: IRequestRepository):
        self.request_repo = request_repo
    
    async def execute(
        self, user_id: int, phone_number: str
    ) -> tuple[date, bool]:
        """
        Calculates ovulation date based on phone number.
        Returns (calculated_date, is_new_calculation)
        
        Algorithm:
        - First request: calculates date in next 2 weeks
        - Subsequent requests: same result until date passes
        - After date passes: calculates next cycle (+28 days)
        """
        # Check if there's an existing request
        existing_request = await self.request_repo.get_by_user_and_phone(
            user_id, phone_number
        )
        
        today = date.today()
        
        if existing_request and existing_request.calculated_date:
            # If date hasn't passed yet, return existing
            if existing_request.calculated_date >= today:
                return existing_request.calculated_date, False
            
            # Date passed, calculate next cycle
            next_date = existing_request.calculated_date + timedelta(days=28)
            existing_request.calculated_date = next_date
            existing_request.cycle_number += 1
            existing_request.updated_at = datetime.utcnow()
            
            await self.request_repo.update(existing_request)
            return next_date, True
        
        # New calculation
        calculated_date = self._calculate_date(phone_number, today)
        
        new_request = UserRequest(
            user_id=user_id,
            phone_number=phone_number,
            calculated_date=calculated_date,
            cycle_number=1,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        await self.request_repo.create(new_request)
        return calculated_date, True
    
    def _calculate_date(self, phone_number: str, base_date: date) -> date:
        """
        Deterministic calculation: hash(phone + month) % 14 + 1
        Returns date between 1-14 days from base_date
        """
        month_key = f"{base_date.year}-{base_date.month:02d}"
        hash_input = f"{phone_number}{month_key}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        days_offset = (hash_value % 14) + 1  # 1-14 days
        
        return base_date + timedelta(days=days_offset)

