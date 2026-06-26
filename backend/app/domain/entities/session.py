from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.domain.entities.user import UserOut
from app.domain.entities.service_type import ServiceTypeOut

class SessionBase(BaseModel):
    tutor_id: int
    service_type_id: int
    scheduled_at: datetime
    status: str = "pendiente" # pendiente | confirmada | completada | cancelada
    title: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[str] = None

class SessionCreate(SessionBase):
    student_id: Optional[int] = None

class SessionUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None # pendiente | confirmada | completada | cancelada
    title: Optional[str] = None
    notes: Optional[str] = None
    location: Optional[str] = None

class SessionOut(BaseModel):
    id: int
    student_id: int
    tutor_id: int
    service_type_id: int
    scheduled_at: datetime
    status: str
    title: Optional[str]
    notes: Optional[str]
    location: Optional[str]
    student: UserOut
    tutor: UserOut
    service_type: ServiceTypeOut

    class Config:
        from_attributes = True
