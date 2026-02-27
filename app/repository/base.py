from abc import ABC, abstractmethod

from ..models import Message, User


class Repository(ABC):
    @abstractmethod
    async def init_database(self) -> bool:
        ...

    @abstractmethod
    async def get_messages_by_user_id(self, user_id: int) -> list[Message]:
        ...

    @abstractmethod
    async def put_message(self, message: Message) -> bool:
        ...

    @abstractmethod
    async def get_user_by_access_key(self, access_key: str) -> User | None:
        ...

    @abstractmethod
    async def get_users(self) -> list[User]:
        ...

    @abstractmethod
    async def put_user(self, user: User) -> bool:
        ...