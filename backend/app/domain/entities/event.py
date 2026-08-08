from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class EventBase(BaseModel):
    title: str
    starts_at: datetime
    ends_at: datetime
    type: str # e.g. "tutoria", "examen", "tarea"
    session_id: Optional[int] = None

class EventCreate(EventBase):
    pass

class EventOut(EventBase):
    id: int
    created_by: int

    model_config = ConfigDict(from_attributes=True)
