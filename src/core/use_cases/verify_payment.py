from datetime import datetime, date
from typing import Optional
from src.core.entities.payment import PaymentStatus
from src.core.interfaces.payment_repository import IPaymentRepository
from src.core.interfaces.payment_gateway import IPaymentGateway
from src.core.use_cases.calculate_ovulation_date import CalculateOvulationDateUseCase


class VerifyPaymentUseCase:
    def __init__(
        self,
        payment_repo: IPaymentRepository,
        payment_gateway: IPaymentGateway,
        calculate_date_use_case: CalculateOvulationDateUseCase,
    ):
        self.payment_repo = payment_repo
        self.payment_gateway = payment_gateway
        self.calculate_date_use_case = calculate_date_use_case
    
    async def execute(
        self, payment_id: str, amount: float, metadata: dict
    ) -> tuple[bool, Optional[date]]:
        """
        Verifies payment and calculates ovulation date if successful.
        Returns (is_verified, calculated_date_str or None)
        """
        # Verify webhook signature
        is_valid = await self.payment_gateway.verify_webhook(
            payment_id, amount, metadata
        )
        
        if not is_valid:
            return False, None
        
        # Get payment from database
        payment = await self.payment_repo.get_by_yookassa_id(payment_id)
        
        if not payment:
            return False, None
        
        # Update payment status
        payment.status = PaymentStatus.SUCCEEDED
        payment = await self.payment_repo.update(payment)
        
        # Calculate ovulation date
        if payment.user_id and payment.phone_number:
            calculated_date, _ = await self.calculate_date_use_case.execute(
                payment.user_id, payment.phone_number
            )
            # Return date object, formatting will be done in presentation layer
            return True, calculated_date
        
        return True, None

