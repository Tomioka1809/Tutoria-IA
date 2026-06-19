from pydantic import BaseModel
from typing import Optional

class ServiceTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None

class ServiceTypeCreate(ServiceTypeBase):
    pass

class ServiceTypeOut(ServiceTypeBase):
    id: int

    class Config:
        from_attributes = True
