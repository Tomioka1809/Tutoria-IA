from sqlalchemy import String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, List
from datetime import datetime
from app.infrastructure.database.base_class import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.user import User
    from app.infrastructure.database.models.service_type import ServiceType
    from app.infrastructure.database.models.event import Event

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service_type_id: Mapped[int] = mapped_column(ForeignKey("service_types.id", ondelete="CASCADE"), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pendiente", nullable=False) # pendiente | confirmada | completada | cancelada
    notes: Mapped[str] = mapped_column(String(1000), nullable=True)

    # Relationships
    student: Mapped["User"] = relationship(
        "User", foreign_keys=[student_id], back_populates="sessions_as_student"
    )
    tutor: Mapped["User"] = relationship(
        "User", foreign_keys=[tutor_id], back_populates="sessions_as_tutor"
    )
    service_type: Mapped["ServiceType"] = relationship(
        "ServiceType", back_populates="sessions"
    )
    events: Mapped[List["Event"]] = relationship(
        "Event", back_populates="session"
    )
