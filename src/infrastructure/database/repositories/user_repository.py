from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.entities.user import User
from src.core.interfaces.user_repository import IUserRepository
from src.infrastructure.database.models import UserModel


class UserRepository(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_user_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()
        return model.to_entity() if model else None
    
    async def create(self, user: User) -> User:
        model = UserModel.from_entity(user)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()
    
    async def update(self, user: User) -> User:
        if not user.id:
            raise ValueError("User ID is required for update")
        
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        model = result.scalar_one()
        
        model.username = user.username
        model.consent_given_at = user.consent_given_at
        
        await self.session.commit()
        await self.session.refresh(model)
        return model.to_entity()

