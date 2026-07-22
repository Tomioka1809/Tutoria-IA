from pydantic import BaseModel

class NotificationAccessDTO(BaseModel):
    id: int
    user_id: int
    is_read: bool

    class Config:
        from_attributes = True
