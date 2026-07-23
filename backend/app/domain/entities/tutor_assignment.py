from pydantic import BaseModel, ConfigDict
from app.domain.entities.user import UserOut
from app.domain.entities.service_type import ServiceTypeOut

class TutorAssignmentBase(BaseModel):
    student_id: int
    tutor_id: int
    service_type_id: int

class TutorAssignmentCreate(TutorAssignmentBase):
    pass

class TutorAssignmentOut(BaseModel):
    id: int
    student_id: int
    tutor_id: int
    service_type_id: int
    student: UserOut
    tutor: UserOut
    service_type: ServiceTypeOut

    model_config = ConfigDict(from_attributes=True)
