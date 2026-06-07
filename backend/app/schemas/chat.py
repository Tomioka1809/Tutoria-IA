from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    role: str # user | assistant
    content: str
    sent_at: datetime

    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    id: int
    student_id: int
    created_at: datetime
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True
