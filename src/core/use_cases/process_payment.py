from typing import Optional
from src.core.entities.payment import Payment, PaymentStatus
from src.core.interfaces.payment_repository import IPaymentRepository
from src.core.interfaces.payment_gateway import IPaymentGateway


class ProcessPaymentUseCase:
    def __init__(
        self,
        payment_repo: IPaymentRepository,
        payment_gateway: IPaymentGateway,
    ):
        self.payment_repo = payment_repo
        self.payment_gateway = payment_gateway
    
    async def execute(
        self, user_id: int, phone_number: str, amount: float = 50.0
    ) -> tuple[Payment, str]:
        """
        Creates payment and returns payment URL.
        Returns (Payment, payment_url)
        """
        # Check if there's already a successful payment for this user+phone
        existing_payment = await self.payment_repo.get_by_user_and_phone(
            user_id, phone_number, PaymentStatus.SUCCEEDED
        )
        
        if existing_payment:
            # Return existing payment URL if still valid
            payment_url = await self.payment_gateway.get_payment_url(
                existing_payment.yookassa_payment_id
            )
            if payment_url:
                return existing_payment, payment_url
        
        # Create new payment
        payment = Payment(
            user_id=user_id,
            phone_number=phone_number,
            amount=amount,
            status=PaymentStatus.PENDING,
        )
        
        # Create payment in gateway
        payment_id, payment_url = await self.payment_gateway.create_payment(
            amount=amount,
            description=f"Запрос данных для {phone_number}",
            metadata={"user_id": user_id, "phone_number": phone_number},
        )
        
        payment.yookassa_payment_id = payment_id
        payment = await self.payment_repo.create(payment)
        
        return payment, payment_url

