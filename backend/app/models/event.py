from sqlalchemy import String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from datetime import datetime
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.session import Session

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. "tutoria", "examen", "tarea"

    # Relationships
    creator: Mapped["User"] = relationship(
        "User", back_populates="events_created"
    )
    session: Mapped["Session"] = relationship(
        "Session", back_populates="events"
    )
