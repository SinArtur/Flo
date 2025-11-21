from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.entities.payment import Payment, PaymentStatus
from src.core.interfaces.payment_repository import IPaymentRepository
from src.infrastructure.database.models import PaymentModel


class PaymentRepository(IPaymentRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, payment: Payment) -> Payment:
        model = PaymentModel.from_entity(payment)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()
    
    async def get_by_id(self, payment_id: int) -> Optional[Payment]:
        result = await self.session.execute(
            select(PaymentModel).where(PaymentModel.id == payment_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None
    
    async def get_by_yookassa_id(self, yookassa_id: str) -> Optional[Payment]:
        result = await self.session.execute(
            select(PaymentModel).where(
                PaymentModel.yookassa_payment_id == yookassa_id
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None
    
    async def get_by_user_and_phone(
        self, user_id: int, phone_number: str, status: PaymentStatus
    ) -> Optional[Payment]:
        result = await self.session.execute(
            select(PaymentModel).where(
                PaymentModel.user_id == user_id,
                PaymentModel.phone_number == phone_number,
                PaymentModel.status == status,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None
    
    async def update(self, payment: Payment) -> Payment:
        if not payment.id:
            raise ValueError("Payment ID is required for update")
        
        result = await self.session.execute(
            select(PaymentModel).where(PaymentModel.id == payment.id)
        )
        model = result.scalar_one()
        
        model.user_id = payment.user_id
        model.phone_number = payment.phone_number
        model.amount = payment.amount
        model.status = payment.status
        model.yookassa_payment_id = payment.yookassa_payment_id
        
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()

