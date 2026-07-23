from pydantic import BaseModel, ConfigDict

class NotificationAccessDTO(BaseModel):
    id: int
    user_id: int
    is_read: bool

    model_config = ConfigDict(from_attributes=True)
