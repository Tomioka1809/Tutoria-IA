from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from app.domain.entities.session import SessionOut, SessionUpdate
from app.application.dtos.session_dtos import SessionAccessDTO

class StreakRepositoryPort(ABC):
    @abstractmethod
    async def get_streak(self, student_id: int):
        pass

    @abstractmethod
    async def save_streak(self, streak):
        pass

class NotificationRepositoryPort(ABC):
    @abstractmethod
    async def get_unread(self, user_id: int) -> List:
        pass

    @abstractmethod
    async def mark_as_read(self, notification_id: int):
        pass

class SessionRepositoryPort(ABC):
    @abstractmethod
    async def get_user_sessions(self, user_id: int, user_role: str) -> List[SessionOut]:
        pass

    @abstractmethod
    async def get_access_data(self, session_id: int) -> Optional[SessionAccessDTO]:
        pass

    @abstractmethod
    async def create_sessions(
        self,
        creator_id: int,
        tutor_id: int,
        student_ids: List[int],
        service_type_id: int,
        scheduled_at: datetime,
        status: str,
        title: Optional[str] = None,
        notes: Optional[str] = None,
        location: Optional[str] = None,
    ) -> SessionOut:
        pass

    @abstractmethod
    async def update_session(
        self,
        session_id: int,
        session_in: SessionUpdate,
        user_id: int,
    ) -> Optional[SessionOut]:
        pass
