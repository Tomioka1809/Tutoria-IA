from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    role: str = "estudiante" # estudiante | tutor | admin
    is_active: bool = True

# Properties to receive on user creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    full_name: str
    
    # Profile fields
    student_code: Optional[str] = None
    current_semester: Optional[int] = None
    phone_number: Optional[str] = None
    academic_status: Optional[str] = None
    
    tutor_code: Optional[str] = None
    max_capacity: Optional[int] = 15
    expertise_areas: Optional[str] = None
    office_location: Optional[str] = None
    
    administrative_position: Optional[str] = None

# Properties to receive on user update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    full_name: Optional[str] = None
    student_code: Optional[str] = None
    tutor_code: Optional[str] = None
    phone_number: Optional[str] = None
    expertise_areas: Optional[str] = None
    office_location: Optional[str] = None
    current_semester: Optional[int] = None
    academic_status: Optional[str] = None
    is_active: Optional[bool] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

# Properties to return to client (serialization)
class UserOut(UserBase):
    id: int
    full_name: str
    student_code: Optional[str] = None
    tutor_code: Optional[str] = None
    phone_number: Optional[str] = None
    expertise_areas: Optional[str] = None
    office_location: Optional[str] = None
    current_semester: Optional[int] = None
    academic_status: Optional[str] = None

    class Config:
        from_attributes = True
