from pydantic import BaseModel, ConfigDict

class SessionAccessDTO(BaseModel):
    id: int
    student_id: int
    tutor_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)
