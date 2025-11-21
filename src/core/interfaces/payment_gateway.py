from abc import ABC, abstractmethod
from typing import Optional, Tuple


class IPaymentGateway(ABC):
    @abstractmethod
    async def create_payment(
        self, amount: float, description: str, metadata: dict
    ) -> Tuple[str, str]:
        """
        Creates payment in gateway.
        Returns (payment_id, payment_url)
        """
        pass
    
    @abstractmethod
    async def get_payment_url(self, payment_id: str) -> Optional[str]:
        """Returns payment URL if payment exists"""
        pass
    
    @abstractmethod
    async def verify_webhook(
        self, payment_id: str, amount: float, metadata: dict
    ) -> bool:
        """Verifies webhook signature and payment data"""
        pass

