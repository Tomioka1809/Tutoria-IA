from sqlalchemy import ForeignKey, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from datetime import date
from app.infrastructure.database.base_class import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.user import User

class Streak(Base):
    __tablename__ = "streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_session_date: Mapped[date] = mapped_column(Date, nullable=True)

    # Relationships
    student: Mapped["User"] = relationship(
        "User", back_populates="streaks"
    )
