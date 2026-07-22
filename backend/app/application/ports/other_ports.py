from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime
from app.domain.entities.session import SessionOut, SessionUpdate
from app.domain.entities.streak import StreakOut
from app.domain.entities.notification import NotificationOut
from app.application.dtos.session_dtos import SessionAccessDTO
from app.application.dtos.notification_dtos import NotificationAccessDTO

class StreakRepositoryPort(ABC):
    @abstractmethod
    async def get_student_streak(self, student_id: int) -> Tuple[StreakOut, bool]:
        """Retorna tupla (StreakOut, bool) donde bool indica si la racha fue recién creada en la BD."""
        pass

    @abstractmethod
    async def update_on_session_complete(self, student_id: int) -> StreakOut:
        pass

    @abstractmethod
    async def reset_on_session_absent(self, student_id: int) -> StreakOut:
        pass

class NotificationRepositoryPort(ABC):
    @abstractmethod
    async def get_user_notifications(self, user_id: int, user_role: str) -> List[NotificationOut]:
        pass

    @abstractmethod
    async def get_unread_count(self, user_id: int) -> int:
        pass

    @abstractmethod
    async def get_access_data(self, notification_id: int) -> Optional[NotificationAccessDTO]:
        pass

    @abstractmethod
    async def create_notification(
        self, user_id: int, title: str, body: str, notification_type: str
    ) -> NotificationOut:
        pass

    @abstractmethod
    async def mark_as_read(self, notification_id: int) -> Optional[NotificationOut]:
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
