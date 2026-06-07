from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Shared properties
class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    student_code: Optional[str] = None
    role: str = "estudiante" # estudiante | tutor | admin
    school: Optional[str] = None

# Properties to receive on user creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

# Properties to receive on user update
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    student_code: Optional[str] = None
    role: Optional[str] = None
    school: Optional[str] = None

# Properties to return to client (serialization)
class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True
