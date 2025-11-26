from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Date, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime, date
from src.infrastructure.database.base import Base
from src.core.entities.payment import PaymentStatus


class PaymentModel(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    phone_number = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False, default=50.0)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    yookassa_payment_id = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_entity(self) -> "Payment":
        from src.core.entities.payment import Payment
        return Payment(
            id=self.id,
            user_id=self.user_id,
            phone_number=self.phone_number,
            amount=self.amount,
            status=self.status,
            yookassa_payment_id=self.yookassa_payment_id,
            created_at=self.created_at,
        )
    
    @classmethod
    def from_entity(cls, payment: "Payment") -> "PaymentModel":
        return cls(
            id=payment.id,
            user_id=payment.user_id,
            phone_number=payment.phone_number,
            amount=payment.amount,
            status=payment.status,
            yookassa_payment_id=payment.yookassa_payment_id,
            created_at=payment.created_at or datetime.utcnow(),
        )


class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, unique=True, index=True)  # Telegram user ID
    username = Column(String, nullable=True)
    consent_given_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_entity(self) -> "User":
        from src.core.entities.user import User
        return User(
            id=self.id,
            user_id=self.user_id,
            username=self.username,
            consent_given_at=self.consent_given_at,
            created_at=self.created_at,
        )
    
    @classmethod
    def from_entity(cls, user: "User") -> "UserModel":
        return cls(
            id=user.id,
            user_id=user.user_id,
            username=user.username,
            consent_given_at=user.consent_given_at,
            created_at=user.created_at or datetime.utcnow(),
        )


class UserRequestModel(Base):
    __tablename__ = "user_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    phone_number = Column(String, nullable=False, index=True)
    calculated_date = Column(Date, nullable=True)
    cycle_number = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_entity(self) -> "UserRequest":
        from src.core.entities.user_request import UserRequest
        return UserRequest(
            id=self.id,
            user_id=self.user_id,
            phone_number=self.phone_number,
            calculated_date=self.calculated_date,
            cycle_number=self.cycle_number,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
    
    @classmethod
    def from_entity(cls, request: "UserRequest") -> "UserRequestModel":
        return cls(
            id=request.id,
            user_id=request.user_id,
            phone_number=request.phone_number,
            calculated_date=request.calculated_date,
            cycle_number=request.cycle_number,
            is_active=request.is_active,
            created_at=request.created_at or datetime.utcnow(),
            updated_at=request.updated_at or datetime.utcnow(),
        )

