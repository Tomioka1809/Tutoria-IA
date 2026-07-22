from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.application.ports.repository_ports import TutorAssignmentRepositoryPort
from app.application.dtos.chat_tool_dtos import AssignedTutorDTO, AssignedStudentDTO
from app.infrastructure.database.models.tutor_assignment import TutorAssignment
from app.infrastructure.database.models.user import User

class TutorAssignmentRepository(TutorAssignmentRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_assigned_tutors_data(self, student_id: int) -> List[AssignedTutorDTO]:
        result = await self.db.execute(
            select(TutorAssignment)
            .where(TutorAssignment.student_id == student_id)
            .options(
                selectinload(TutorAssignment.tutor).selectinload(User.tutor_profile),
                selectinload(TutorAssignment.service_type)
            )
        )
        assignments = result.scalars().all()
        if not assignments:
            return []

        data: List[AssignedTutorDTO] = []
        for a in assignments:
            t = a.tutor
            t_profile = t.tutor_profile if t else None
            data.append({
                "tutor_name": t.full_name if t else "No definido",
                "email": t.email if t else "No definido",
                "office_location": t_profile.office_location if t_profile else "No definido",
                "expertise_areas": t_profile.expertise_areas if t_profile else "No definido",
                "service_type": a.service_type.name if a.service_type else "Tutoría",
                "academic_period": a.academic_period
            })
        return data

    async def get_assigned_students_data(self, tutor_id: int) -> List[AssignedStudentDTO]:
        result = await self.db.execute(
            select(TutorAssignment)
            .where(TutorAssignment.tutor_id == tutor_id)
            .options(
                selectinload(TutorAssignment.student).selectinload(User.student_profile),
                selectinload(TutorAssignment.service_type)
            )
        )
        assignments = result.scalars().all()
        if not assignments:
            return []

        data: List[AssignedStudentDTO] = []
        for a in assignments:
            s = a.student
            if not s:
                continue
            s_profile = s.student_profile
            data.append({
                "student_name": s.full_name,
                "email": s.email,
                "student_code": s_profile.student_code if s_profile else "No definido",
                "current_semester": s_profile.current_semester if s_profile else "No definido",
                "academic_status": s_profile.academic_status if s_profile else "No definido",
                "phone_number": s_profile.phone_number if s_profile else "No definido",
                "academic_period": a.academic_period,
                "service_type": a.service_type.name if a.service_type else "Tutoría"
            })
        return data

    async def get_assigned_student_ids(self, tutor_id: int) -> List[int]:
        result = await self.db.execute(
            select(TutorAssignment.student_id).where(TutorAssignment.tutor_id == tutor_id)
        )
        return list(result.scalars().all())
