from abc import ABC, abstractmethod
from typing import Optional
from src.core.entities.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    async def create(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        pass

