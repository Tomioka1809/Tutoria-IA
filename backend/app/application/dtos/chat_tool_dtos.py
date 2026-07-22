from typing import TypedDict, List, Union

class AssignedTutorDTO(TypedDict):
    tutor_name: str
    email: str
    office_location: str
    expertise_areas: str
    service_type: str
    academic_period: str

class AssignedStudentDTO(TypedDict):
    student_name: str
    email: str
    student_code: str
    current_semester: Union[str, int]
    academic_status: str
    phone_number: str
    academic_period: str
    service_type: str

class CalendarSessionDTO(TypedDict):
    session_id: int
    title: str
    scheduled_at: str
    status: str
    location: str
    notes: str
    other_participant: str

class CalendarEventDTO(TypedDict):
    event_id: int
    title: str
    starts_at: str
    ends_at: str
    type: str

class CalendarDataDTO(TypedDict):
    sessions: List[CalendarSessionDTO]
    events: List[CalendarEventDTO]
