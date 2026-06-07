from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.user import UserOut
from app.schemas.service_type import ServiceTypeOut

class SessionBase(BaseModel):
    student_id: int
    tutor_id: int
    service_type_id: int
    scheduled_at: datetime
    status: str = "pendiente" # pendiente | confirmada | completada | cancelada
    notes: Optional[str] = None

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None # pendiente | confirmada | completada | cancelada
    notes: Optional[str] = None

class SessionOut(BaseModel):
    id: int
    student_id: int
    tutor_id: int
    service_type_id: int
    scheduled_at: datetime
    status: str
    notes: Optional[str]
    student: UserOut
    tutor: UserOut
    service_type: ServiceTypeOut

    class Config:
        from_attributes = True
