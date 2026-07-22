from pydantic import BaseModel

class SessionAccessDTO(BaseModel):
    id: int
    student_id: int
    tutor_id: int
    status: str

    class Config:
        from_attributes = True
