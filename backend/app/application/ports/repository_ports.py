from abc import ABC, abstractmethod
from typing import List, Optional, Any
from app.domain.entities.user import UserCreate, UserUpdate
# We'll import actual models locally or use generic Any to avoid cyclic imports if needed,
# but ideally we use domain entities. For ORM models, they should be mapped or we use them as return types.

class UserRepositoryPort(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    async def create(self, user_in: UserCreate, hashed_password: str) -> Any:
        pass

class ChatRepositoryPort(ABC):
    @abstractmethod
    async def get_or_create_conversation(self, student_id: int) -> Any:
        pass

    @abstractmethod
    async def save_message(self, conversation_id: int, role: str, content: str) -> Any:
        pass

    @abstractmethod
    async def get_history(self, conversation_id: int) -> List[Any]:
        pass

class CorpusRepositoryPort(ABC):
    @abstractmethod
    async def search_similar(self, query_embedding: List[float], limit: int = 5) -> List[str]:
        pass

    @abstractmethod
    async def insert_chunk(self, text: str, embedding: List[float]):
        pass
