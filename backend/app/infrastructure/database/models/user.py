from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING, Optional
from app.infrastructure.database.base_class import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.tutor_assignment import TutorAssignment
    from app.infrastructure.database.models.session import Session
    from app.infrastructure.database.models.event import Event
    from app.infrastructure.database.models.streak import Streak
    from app.infrastructure.database.models.notification import Notification
    from app.infrastructure.database.models.conversation import Conversation
    from app.infrastructure.database.models.profiles import StudentProfile, TutorProfile, AdminProfile

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="estudiante", nullable=False) # estudiante | tutor | admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Profile Relationships
    student_profile: Mapped[Optional["StudentProfile"]] = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tutor_profile: Mapped[Optional["TutorProfile"]] = relationship("TutorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    admin_profile: Mapped[Optional["AdminProfile"]] = relationship("AdminProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        if self.student_profile: return self.student_profile.full_name
        if self.tutor_profile: return self.tutor_profile.full_name
        if self.admin_profile: return self.admin_profile.full_name
        return ""

    @property
    def student_code(self) -> Optional[str]:
        if self.student_profile: return self.student_profile.student_code
        return None

    @property
    def tutor_code(self) -> Optional[str]:
        if self.tutor_profile: return self.tutor_profile.tutor_code
        return None

    @property
    def expertise_areas(self) -> Optional[str]:
        if self.tutor_profile: return self.tutor_profile.expertise_areas
        return None

    @property
    def office_location(self) -> Optional[str]:
        if self.tutor_profile: return self.tutor_profile.office_location
        return None

    @property
    def current_semester(self) -> Optional[int]:
        if self.student_profile: return self.student_profile.current_semester
        return None

    @property
    def academic_status(self) -> Optional[str]:
        if self.student_profile: return self.student_profile.academic_status
        return None

    @property
    def phone_number(self) -> Optional[str]:
        if self.student_profile: return self.student_profile.phone_number
        if self.tutor_profile: return self.tutor_profile.phone_number
        return None

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
