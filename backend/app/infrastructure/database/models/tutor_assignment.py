from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.infrastructure.database.base_class import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.user import User
    from app.infrastructure.database.models.service_type import ServiceType

class TutorAssignment(Base):
    __tablename__ = "tutor_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    service_type_id: Mapped[int] = mapped_column(ForeignKey("service_types.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    student: Mapped["User"] = relationship(
        "User", foreign_keys=[student_id], back_populates="tutor_assignments_as_student"
    )
    tutor: Mapped["User"] = relationship(
        "User", foreign_keys=[tutor_id], back_populates="tutor_assignments_as_tutor"
    )
    service_type: Mapped["ServiceType"] = relationship(
        "ServiceType", back_populates="tutor_assignments"
    )
