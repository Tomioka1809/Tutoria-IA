from pydantic import BaseModel, ConfigDict, EmailStr, Field
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
class UserSelfUpdate(BaseModel):
    """Campos que un usuario puede cambiar sobre su propia cuenta.

    No declara ``role`` ni ``is_active`` a proposito: los recibia y el repositorio
    los escribia, asi que un estudiante se ascendia a administrador con un solo
    PUT /auth/profile. La proteccion es que el campo no exista en el contrato de
    entrada, no un filtro en el endpoint. Si alguna vez hace falta que un admin
    cambie el rol de otro, va por una ruta de admin con su propio DTO.
    """

    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    student_code: Optional[str] = None
    tutor_code: Optional[str] = None
    phone_number: Optional[str] = None
    expertise_areas: Optional[str] = None
    office_location: Optional[str] = None
    current_semester: Optional[int] = None
    academic_status: Optional[str] = None

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

    model_config = ConfigDict(from_attributes=True)
