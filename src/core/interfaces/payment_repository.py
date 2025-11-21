from abc import ABC, abstractmethod
from typing import Optional, List
from src.core.entities.payment import Payment, PaymentStatus


class IPaymentRepository(ABC):
    @abstractmethod
    async def create(self, payment: Payment) -> Payment:
        pass
    
    @abstractmethod
    async def get_by_id(self, payment_id: int) -> Optional[Payment]:
        pass
    
    @abstractmethod
    async def get_by_yookassa_id(self, yookassa_id: str) -> Optional[Payment]:
        pass
    
    @abstractmethod
    async def get_by_user_and_phone(
        self, user_id: int, phone_number: str, status: PaymentStatus
    ) -> Optional[Payment]:
        pass
    
    @abstractmethod
    async def update(self, payment: Payment) -> Payment:
        pass

