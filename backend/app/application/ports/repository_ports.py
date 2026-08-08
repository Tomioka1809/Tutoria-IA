from abc import ABC, abstractmethod
from typing import List, Optional, Any
from datetime import datetime
from app.domain.entities.user import UserCreate, UserSelfUpdate
from app.application.dtos.chat_tool_dtos import (
    AssignedTutorDTO,
    AssignedStudentDTO,
    CalendarDataDTO,
)

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

    @abstractmethod
    async def update(self, user_id: int, user_in: UserSelfUpdate) -> Optional[Any]:
        pass

    @abstractmethod
    async def update_password(self, user_id: int, new_password_hash: str) -> bool:
        pass

class PasswordResetTokenRepositoryPort(ABC):
    """Almacen compartido de los codigos de recuperacion.

    Es un puerto y no un diccionario en memoria porque el contador de intentos solo
    limita algo si sobrevive al reinicio del proceso y es el mismo para todos los
    workers.
    """

    @abstractmethod
    async def replace_for_email(self, email: str, code_hash: str, expires_at: datetime) -> Any:
        """Invalida los codigos vigentes de ese correo y guarda el nuevo.

        Pedir un codigo nuevo tiene que anular el anterior: si convivieran, cada
        solicitud sumaria una ventana de intentos mas sobre la misma cuenta.
        """
        pass

    @abstractmethod
    async def get_active(self, email: str) -> Optional[Any]:
        """Codigo vigente de ese correo, o None si no hay ninguno."""
        pass

    @abstractmethod
    async def register_failed_attempt(self, token_id: int) -> int:
        """Suma un intento fallido y devuelve el total acumulado."""
        pass

    @abstractmethod
    async def invalidate(self, token_id: int) -> None:
        """Marca el codigo como inservible (consumido, expirado o sin intentos)."""
        pass


class ChatRepositoryPort(ABC):
    @abstractmethod
    async def get_or_create_conversation(self, user_id: int) -> Any:
        pass

    @abstractmethod
    async def reset_conversation(self, user_id: int) -> None:
        pass

    @abstractmethod
    async def save_message(self, conversation_id: int, role: str, content: str) -> Any:
        pass

    @abstractmethod
    async def get_history(self, conversation_id: int, limit: int | None = None) -> List[Any]:
        """Historial en orden cronologico. Con limit devuelve solo los ultimos N mensajes."""
        pass

    @abstractmethod
    async def get_message(self, message_id: int) -> Any | None:
        """Un mensaje por id, o None si no existe."""
        pass

    @abstractmethod
    async def edit_message_and_truncate(self, message_id: int, content: str) -> Any:
        """Reescribe un mensaje y borra todo lo que vino despues en su conversacion.

        Editar una pregunta invalida la respuesta que le siguio y lo que se
        construyo sobre ella, asi que el corte es parte de la edicion y no un
        paso aparte: dejar la respuesta vieja colgando produciria un historial
        que se contradice a si mismo, y ese historial alimenta la reescritura de
        consulta del RAG.
        """
        pass

from app.application.dtos.rag_dtos import RetrievedChunkDTO

class CorpusRepositoryPort(ABC):
    @abstractmethod
    async def search_similar(
        self,
        query_embedding: List[float],
        *,
        limit: int,
        query_text: str | None,
        max_cosine_distance: float,
        keyword_fallback_limit: int,
        candidatos_por_rama: int = 20,
        rrf_k: int = 60,
        min_ts_rank: float = 0.05,
        peso_autoridad: float = 0.5,
    ) -> List[RetrievedChunkDTO]:
        """Recupera fragmentos combinando busqueda vectorial y de texto completo.

        Los tres ultimos parametros tienen valor por defecto para no romper a los
        dobles de prueba que ya implementan este puerto.
        """
        pass

    @abstractmethod
    async def insert_chunk(self, text: str, embedding: List[float]):
        pass

class TutorAssignmentRepositoryPort(ABC):
    @abstractmethod
    async def get_assigned_tutors_data(self, student_id: int) -> List[AssignedTutorDTO]:
        pass

    @abstractmethod
    async def get_assigned_students_data(self, tutor_id: int) -> List[AssignedStudentDTO]:
        pass

    @abstractmethod
    async def get_assigned_student_ids(self, tutor_id: int) -> List[int]:
        pass

class CalendarRepositoryPort(ABC):
    @abstractmethod
    async def get_calendar_events_data(
        self, user_id: int, role: str, start_dt: datetime, end_dt: datetime
    ) -> CalendarDataDTO:
        pass
