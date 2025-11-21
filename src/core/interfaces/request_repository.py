from abc import ABC, abstractmethod
from typing import Optional
from src.core.entities.user_request import UserRequest


class IRequestRepository(ABC):
    @abstractmethod
    async def create(self, request: UserRequest) -> UserRequest:
        pass
    
    @abstractmethod
    async def get_by_user_and_phone(
        self, user_id: int, phone_number: str
    ) -> Optional[UserRequest]:
        pass
    
    @abstractmethod
    async def update(self, request: UserRequest) -> UserRequest:
        pass

