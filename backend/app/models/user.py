from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.tutor_assignment import TutorAssignment
    from app.models.session import Session
    from app.models.event import Event
    from app.models.streak import Streak
    from app.models.notification import Notification
    from app.models.conversation import Conversation

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    student_code: Mapped[str] = mapped_column(String(50), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="estudiante", nullable=False) # estudiante | tutor | admin
    school: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    # As tutor or student assignments
    tutor_assignments_as_student: Mapped[List["TutorAssignment"]] = relationship(
        "TutorAssignment", foreign_keys="[TutorAssignment.student_id]", back_populates="student"
    )
    tutor_assignments_as_tutor: Mapped[List["TutorAssignment"]] = relationship(
        "TutorAssignment", foreign_keys="[TutorAssignment.tutor_id]", back_populates="tutor"
    )
    
    # As student or tutor in sessions
    sessions_as_student: Mapped[List["Session"]] = relationship(
        "Session", foreign_keys="[Session.student_id]", back_populates="student"
    )
    sessions_as_tutor: Mapped[List["Session"]] = relationship(
        "Session", foreign_keys="[Session.tutor_id]", back_populates="tutor"
    )

    # Events created by tutor
    events_created: Mapped[List["Event"]] = relationship(
        "Event", back_populates="creator"
    )

    # Streaks for students
    streaks: Mapped[List["Streak"]] = relationship(
        "Streak", back_populates="student"
    )

    # Notifications
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user"
    )

    # Conversations
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="student"
    )
