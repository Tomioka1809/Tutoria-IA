from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.tutor_assignment import TutorAssignment
    from app.models.session import Session

class ServiceType(Base):
    __tablename__ = "service_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    icon: Mapped[str] = mapped_column(String(100), nullable=True) # Icon symbol name e.g. "book", "code"

    # Relationships
    tutor_assignments: Mapped[List["TutorAssignment"]] = relationship(
        "TutorAssignment", back_populates="service_type"
    )
    sessions: Mapped[List["Session"]] = relationship(
        "Session", back_populates="service_type"
    )
