"""
Esquemas Pydantic / DTOs de transferencia de datos de la capa de Dominio.
Re-exporta todas las definiciones de contratos de entrada y salida de la API.
"""

from app.domain.entities.auth import LoginRequest, Token, TokenData
from app.domain.entities.chat import MessageBase, MessageCreate, MessageOut, ConversationOut
from app.domain.entities.event import EventBase, EventCreate, EventOut
from app.domain.entities.notification import NotificationBase, NotificationOut
from app.domain.entities.service_type import ServiceTypeOut
from app.domain.entities.session import SessionBase, SessionCreate, SessionOut
from app.domain.entities.streak import StreakOut
from app.domain.entities.tutor_assignment import TutorAssignmentOut
from app.domain.entities.user import (
    UserBase, UserCreate, UserUpdate, PasswordChange, UserOut
)

__all__ = [
    "LoginRequest", "Token", "TokenData",
    "MessageBase", "MessageCreate", "MessageOut", "ConversationOut",
    "EventBase", "EventCreate", "EventOut",
    "NotificationBase", "NotificationOut",
    "ServiceTypeOut",
    "SessionBase", "SessionCreate", "SessionOut",
    "StreakOut",
    "TutorAssignmentOut",
    "UserBase", "UserCreate", "UserUpdate", "PasswordChange", "UserOut"
]
