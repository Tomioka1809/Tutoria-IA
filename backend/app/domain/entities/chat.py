from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class MessageBase(BaseModel):
    content: str

class MessageCreate(MessageBase):
    pass

class MessageUpdate(MessageBase):
    """Nuevo texto de un mensaje propio que se reescribe."""
    pass

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    role: str # user | assistant
    content: str
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationOut(BaseModel):
    id: int
    student_id: int
    created_at: datetime
    messages: List[MessageOut] = []

    model_config = ConfigDict(from_attributes=True)
