from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class NotificationBase(BaseModel):
    user_id: int
    title: str
    body: str
    type: str # e.g. "session", "streak", "system"
    is_read: bool = False

class NotificationCreate(NotificationBase):
    pass

class NotificationOut(NotificationBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
