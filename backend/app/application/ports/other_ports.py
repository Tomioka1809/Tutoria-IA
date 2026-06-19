from abc import ABC, abstractmethod
from typing import List, Optional, Any
from datetime import date

class StreakRepositoryPort(ABC):
    @abstractmethod
    async def get_streak(self, student_id: int) -> Any:
        pass

    @abstractmethod
    async def save_streak(self, streak: Any) -> Any:
        pass

class NotificationRepositoryPort(ABC):
    @abstractmethod
    async def get_unread(self, user_id: int) -> List[Any]:
        pass
    
    @abstractmethod
    async def mark_as_read(self, notification_id: int) -> Any:
        pass

class SessionRepositoryPort(ABC):
    @abstractmethod
    async def get_by_student(self, student_id: int) -> List[Any]:
        pass
        
    @abstractmethod
    async def get_by_tutor(self, tutor_id: int) -> List[Any]:
        pass
