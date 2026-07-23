from pydantic import BaseModel, ConfigDict
from typing import Optional

class ServiceTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None

class ServiceTypeCreate(ServiceTypeBase):
    pass

class ServiceTypeOut(ServiceTypeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
