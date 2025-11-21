from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.entities.user_request import UserRequest
from src.core.interfaces.request_repository import IRequestRepository
from src.infrastructure.database.models import UserRequestModel


class RequestRepository(IRequestRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, request: UserRequest) -> UserRequest:
        model = UserRequestModel.from_entity(request)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()
    
    async def get_by_user_and_phone(
        self, user_id: int, phone_number: str
    ) -> Optional[UserRequest]:
        result = await self.session.execute(
            select(UserRequestModel).where(
                UserRequestModel.user_id == user_id,
                UserRequestModel.phone_number == phone_number,
                UserRequestModel.is_active == True,
            )
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None
    
    async def update(self, request: UserRequest) -> UserRequest:
        if not request.id:
            raise ValueError("Request ID is required for update")
        
        result = await self.session.execute(
            select(UserRequestModel).where(UserRequestModel.id == request.id)
        )
        model = result.scalar_one()
        
        model.calculated_date = request.calculated_date
        model.cycle_number = request.cycle_number
        model.is_active = request.is_active
        model.updated_at = request.updated_at
        
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()

