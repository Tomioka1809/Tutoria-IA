import unittest
import os
import ast
import inspect
from datetime import datetime

from app.application.use_cases.session_service import SessionUseCase
from app.application.ports.other_ports import SessionRepositoryPort
from app.application.ports.repository_ports import TutorAssignmentRepositoryPort
from app.application.dtos.session_dtos import SessionAccessDTO
from app.domain.entities.session import SessionCreate, SessionUpdate, SessionOut
from app.domain.entities.user import UserOut
from app.domain.entities.service_type import ServiceTypeOut
from app.domain.exceptions import (
    NotAuthorizedError,
    ResourceNotFoundError,
    TutorAssignmentRequiredError,
)


def create_fake_user_out(id: int, full_name: str, role: str) -> UserOut:
    return UserOut(
        id=id,
        email=f"user{id}@unsaac.edu.pe",
        full_name=full_name,
        role=role,
        is_active=True,
    )


def create_fake_session_out(
    id: int,
    student_id: int,
    tutor_id: int,
    service_type_id: int = 1,
    scheduled_at: datetime = None,
    status: str = "programada",
    title: str = "Tutoría",
    notes: str = "",
    location: str = "Virtual",
) -> SessionOut:
    if scheduled_at is None:
        scheduled_at = datetime(2026, 8, 10, 10, 0)
    return SessionOut(
        id=id,
        student_id=student_id,
        tutor_id=tutor_id,
        service_type_id=service_type_id,
        scheduled_at=scheduled_at,
        status=status,
        title=title,
        notes=notes,
        location=location,
        student=create_fake_user_out(student_id, f"Estudiante {student_id}", "estudiante"),
        tutor=create_fake_user_out(tutor_id, f"Tutor {tutor_id}", "tutor"),
        service_type=ServiceTypeOut(id=service_type_id, name="Tutoría Individual"),
    )


class FakeSessionRepository(SessionRepositoryPort):
    def __init__(self):
        self.sessions = {}
        self.counter = 1

    async def get_user_sessions(self, user_id: int, user_role: str) -> list[SessionOut]:
        if user_role == "estudiante":
            return [s for s in self.sessions.values() if s.student_id == user_id]
        elif user_role == "tutor":
            return [s for s in self.sessions.values() if s.tutor_id == user_id]
        return list(self.sessions.values())

    async def get_access_data(self, session_id: int) -> SessionAccessDTO | None:
        sess = self.sessions.get(session_id)
        if not sess:
            return None
        return SessionAccessDTO(
            id=sess.id,
            student_id=sess.student_id,
            tutor_id=sess.tutor_id,
            status=sess.status,
        )

    async def create_sessions(
        self,
        creator_id: int,
        tutor_id: int,
        student_ids: list[int],
        service_type_id: int,
        scheduled_at: datetime,
        status: str,
        title: str | None = None,
        notes: str | None = None,
        location: str | None = None,
    ) -> SessionOut:
        first_session = None
        for s_id in student_ids:
            sess = create_fake_session_out(
                id=self.counter,
                student_id=s_id,
                tutor_id=tutor_id,
                service_type_id=service_type_id,
                scheduled_at=scheduled_at,
                status=status,
                title=title or "Tutoría Programada",
                notes=notes or "",
                location=location or "Virtual",
            )
            self.sessions[self.counter] = sess
            if first_session is None:
                first_session = sess
            self.counter += 1
        return first_session

    async def update_session(
        self, session_id: int, session_in: SessionUpdate, user_id: int
    ) -> SessionOut | None:
        sess = self.sessions.get(session_id)
        if not sess:
            return None

        new_scheduled_at = session_in.scheduled_at or sess.scheduled_at
        new_status = session_in.status or sess.status
        new_title = session_in.title or sess.title
        new_notes = session_in.notes or sess.notes
        new_location = session_in.location or sess.location

        updated = create_fake_session_out(
            id=sess.id,
            student_id=sess.student_id,
            tutor_id=sess.tutor_id,
            service_type_id=sess.service_type_id,
            scheduled_at=new_scheduled_at,
            status=new_status,
            title=new_title,
            notes=new_notes,
            location=new_location,
        )
        self.sessions[session_id] = updated
        return updated


class FakeTutorAssignmentRepository(TutorAssignmentRepositoryPort):
    def __init__(self, assigned_students_map=None):
        self.assigned_students_map = assigned_students_map or {}

    async def get_assigned_tutors_data(self, student_id: int):
        return []

    async def get_assigned_students_data(self, tutor_id: int):
        return []

    async def get_assigned_student_ids(self, tutor_id: int) -> list[int]:
        return self.assigned_students_map.get(tutor_id, [])


class TestSessionApplication(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session_repo = FakeSessionRepository()
        self.tutor_assignment_repo = FakeTutorAssignmentRepository(
            assigned_students_map={10: [101, 102, 103]}
        )
        self.use_case = SessionUseCase(
            session_repo=self.session_repo,
            tutor_assignment_repo=self.tutor_assignment_repo,
        )

    async def test_create_session_success_individual(self):
        session_in = SessionCreate(
            student_id=101,
            tutor_id=10,
            service_type_id=1,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
            title="Tutoría Individual",
            notes="Revisión de tema",
            location="Cubículo A",
        )
        created = await self.use_case.create_session(
            creator_id=10, creator_role="tutor", session_in=session_in
        )
        self.assertIsInstance(created, SessionOut)
        self.assertEqual(created.student_id, 101)
        self.assertEqual(created.tutor_id, 10)
        self.assertEqual(created.title, "Tutoría Individual")

    async def test_create_session_success_group(self):
        session_in = SessionCreate(
            student_id=None,
            tutor_id=10,
            service_type_id=1,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
            title="Tutoría Grupal",
        )
        created = await self.use_case.create_session(
            creator_id=10, creator_role="tutor", session_in=session_in
        )
        self.assertIsInstance(created, SessionOut)
        self.assertEqual(len(self.session_repo.sessions), 3)

    async def test_create_session_unauthorized_creator(self):
        session_in = SessionCreate(
            student_id=101,
            tutor_id=10,
            service_type_id=1,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
        )
        with self.assertRaises(NotAuthorizedError):
            await self.use_case.create_session(
                creator_id=101, creator_role="estudiante", session_in=session_in
            )

    async def test_create_group_session_no_assigned_students(self):
        session_in = SessionCreate(
            student_id=None,
            tutor_id=999,
            service_type_id=1,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
        )
        with self.assertRaises(TutorAssignmentRequiredError):
            await self.use_case.create_session(
                creator_id=999, creator_role="tutor", session_in=session_in
            )

    async def test_get_user_sessions_student(self):
        session_in = SessionCreate(
            student_id=101,
            tutor_id=10,
            service_type_id=1,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
        )
        await self.use_case.create_session(creator_id=10, creator_role="tutor", session_in=session_in)

        student_sessions = await self.use_case.get_user_sessions(user_id=101, user_role="estudiante")
        self.assertEqual(len(student_sessions), 1)
        self.assertIsInstance(student_sessions[0], SessionOut)

    async def test_get_user_sessions_tutor(self):
        session_in = SessionCreate(
            student_id=101,
            tutor_id=10,
            service_type_id=1,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
        )
        await self.use_case.create_session(creator_id=10, creator_role="tutor", session_in=session_in)

        tutor_sessions = await self.use_case.get_user_sessions(user_id=10, user_role="tutor")
        self.assertEqual(len(tutor_sessions), 1)
        self.assertIsInstance(tutor_sessions[0], SessionOut)

    async def test_update_session_success_tutor(self):
        session_in = SessionCreate(
            student_id=101,
            tutor_id=10,
            service_type_id=1,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
        )
        created = await self.use_case.create_session(creator_id=10, creator_role="tutor", session_in=session_in)

        update_in = SessionUpdate(status="completada", notes="Sesión exitosa")
        updated = await self.use_case.update_session(
            session_id=created.id, user_id=10, user_role="tutor", session_in=update_in
        )
        self.assertIsInstance(updated, SessionOut)
        self.assertEqual(updated.status, "completada")
        self.assertEqual(updated.notes, "Sesión exitosa")

    async def test_update_session_unauthorized_student(self):
        session_in = SessionCreate(
            student_id=101,
            tutor_id=10,
            service_type_id=1,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
        )
        created = await self.use_case.create_session(creator_id=10, creator_role="tutor", session_in=session_in)

        update_in = SessionUpdate(status="cancelada")
        with self.assertRaises(NotAuthorizedError):
            await self.use_case.update_session(
                session_id=created.id, user_id=999, user_role="estudiante", session_in=update_in
            )

    async def test_update_session_nonexistent(self):
        update_in = SessionUpdate(status="cancelada")
        with self.assertRaises(ResourceNotFoundError):
            await self.use_case.update_session(
                session_id=9999, user_id=10, user_role="tutor", session_in=update_in
            )

    def test_architectural_purity_no_any_no_getattr_no_cycle(self):
        use_case_path = os.path.join(
            os.path.dirname(__file__),
            "../../app/application/use_cases/session_service.py"
        )
        with open(use_case_path, "r", encoding="utf-8") as f:
            code_text = f.read()

        # AST Inspection
        parsed = ast.parse(code_text)
        imported_modules = []
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.append(node.module)

        forbidden_prefixes = ["fastapi", "sqlalchemy", "app.infrastructure"]
        for mod in imported_modules:
            for prefix in forbidden_prefixes:
                self.assertFalse(
                    mod.startswith(prefix),
                    f"Forbidden import '{mod}' found in session_service.py"
                )

        self.assertNotIn("Any", code_text, "SessionUseCase must not use 'Any'")
        self.assertNotIn("getattr(", code_text, "SessionUseCase must not use 'getattr'")

        # Verify SessionRepository has no architectural cycle (no app.application.use_cases import)
        repo_path = os.path.join(
            os.path.dirname(__file__),
            "../../app/infrastructure/database/repositories/session_repository.py"
        )
        with open(repo_path, "r", encoding="utf-8") as f:
            repo_text = f.read()

        self.assertNotIn(
            "app.application.use_cases",
            repo_text,
            "SessionRepository must not import from app.application.use_cases"
        )


if __name__ == "__main__":
    unittest.main()
