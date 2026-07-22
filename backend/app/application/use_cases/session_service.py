from typing import List
from app.application.ports.other_ports import SessionRepositoryPort
from app.application.ports.repository_ports import TutorAssignmentRepositoryPort
from app.domain.entities.session import SessionCreate, SessionUpdate, SessionOut
from app.domain.exceptions import (
    NotAuthorizedError,
    ResourceNotFoundError,
    TutorAssignmentRequiredError,
)

class SessionUseCase:
    def __init__(
        self,
        session_repo: SessionRepositoryPort,
        tutor_assignment_repo: TutorAssignmentRepositoryPort,
    ):
        self.session_repo = session_repo
        self.tutor_assignment_repo = tutor_assignment_repo

    async def get_user_sessions(self, user_id: int, user_role: str) -> List[SessionOut]:
        return await self.session_repo.get_user_sessions(user_id=user_id, user_role=user_role)

    async def create_session(
        self, creator_id: int, creator_role: str, session_in: SessionCreate
    ) -> SessionOut:
        if creator_role not in ["tutor", "admin"]:
            raise NotAuthorizedError("Only tutors or admins can schedule tutoring sessions.")

        student_ids_to_schedule: List[int] = []
        if session_in.student_id is None:
            student_ids_to_schedule = await self.tutor_assignment_repo.get_assigned_student_ids(
                session_in.tutor_id
            )
            if not student_ids_to_schedule:
                raise TutorAssignmentRequiredError(
                    "No students assigned to this tutor to schedule a group session."
                )
        else:
            student_ids_to_schedule = [session_in.student_id]

        return await self.session_repo.create_sessions(
            creator_id=creator_id,
            tutor_id=session_in.tutor_id,
            student_ids=student_ids_to_schedule,
            service_type_id=session_in.service_type_id,
            scheduled_at=session_in.scheduled_at,
            status=session_in.status,
            title=session_in.title,
            notes=session_in.notes,
            location=session_in.location,
        )

    async def update_session(
        self, session_id: int, user_id: int, user_role: str, session_in: SessionUpdate
    ) -> SessionOut:
        session_access = await self.session_repo.get_access_data(session_id)
        if not session_access:
            raise ResourceNotFoundError("Session not found")

        if user_role == "estudiante" and user_id != session_access.student_id:
            raise NotAuthorizedError("Not enough permissions")
        if user_role == "tutor" and user_id != session_access.tutor_id:
            raise NotAuthorizedError("Not enough permissions")

        updated_session = await self.session_repo.update_session(
            session_id=session_id, session_in=session_in, user_id=user_id
        )
        if not updated_session:
            raise ResourceNotFoundError("Session not found")
        return updated_session
