import unittest
import os
import ast
import inspect
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.infrastructure.database.models import (
    service_type, user, streak, notification, session, event, tutor_assignment, profiles, conversation, message
)
from app.application.use_cases.session_service import SessionUseCase
from app.application.ports.other_ports import (
    SessionRepositoryPort,
    StreakRepositoryPort,
    NotificationRepositoryPort,
)
from app.application.ports.repository_ports import TutorAssignmentRepositoryPort
from app.application.ports.transaction_port import TransactionPort
from app.application.dtos.session_dtos import SessionAccessDTO
from app.domain.entities.session import SessionCreate, SessionUpdate, SessionOut
from app.domain.entities.user import UserOut
from app.domain.entities.service_type import ServiceTypeOut
from app.domain.entities.streak import StreakOut
from app.domain.entities.notification import NotificationOut
from app.domain.exceptions import (
    NotAuthorizedError,
    ResourceNotFoundError,
    TutorAssignmentRequiredError,
)
from app.infrastructure.database.repositories.session_repository import SessionRepository


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
        updated_scheduled_at = (
            session_in.scheduled_at if session_in.scheduled_at is not None else sess.scheduled_at
        )
        updated_status = session_in.status if session_in.status is not None else sess.status
        updated_title = session_in.title if session_in.title is not None else sess.title
        updated_notes = session_in.notes if session_in.notes is not None else sess.notes
        updated_location = session_in.location if session_in.location is not None else sess.location

        new_sess = create_fake_session_out(
            id=sess.id,
            student_id=sess.student_id,
            tutor_id=sess.tutor_id,
            service_type_id=sess.service_type_id,
            scheduled_at=updated_scheduled_at,
            status=updated_status,
            title=updated_title,
            notes=updated_notes,
            location=updated_location,
        )
        self.sessions[session_id] = new_sess
        return new_sess


class FakeTutorAssignmentRepository(TutorAssignmentRepositoryPort):
    def __init__(self, assigned_students_map=None):
        self.assigned_students_map = assigned_students_map or {10: [101, 102]}

    async def get_assigned_tutors_data(self, student_id: int):
        return []

    async def get_assigned_students_data(self, tutor_id: int):
        return []

    async def get_assigned_student_ids(self, tutor_id: int) -> list[int]:
        return self.assigned_students_map.get(tutor_id, [])


class TestSessionApplication(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session_repo = FakeSessionRepository()
        self.tutor_assignment_repo = FakeTutorAssignmentRepository()
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
            title="Individual Test",
        )
        result = await self.use_case.create_session(
            creator_id=10, creator_role="tutor", session_in=session_in
        )

        self.assertIsInstance(result, SessionOut)
        self.assertEqual(result.student_id, 101)
        self.assertEqual(result.tutor_id, 10)
        self.assertEqual(len(self.session_repo.sessions), 1)

    async def test_create_session_success_group(self):
        session_in = SessionCreate(
            student_id=None,
            tutor_id=10,
            service_type_id=2,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
            title="Group Test",
        )
        result = await self.use_case.create_session(
            creator_id=10, creator_role="tutor", session_in=session_in
        )

        self.assertIsInstance(result, SessionOut)
        self.assertEqual(result.tutor_id, 10)
        self.assertEqual(len(self.session_repo.sessions), 2)

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

    async def test_update_session_success_tutor(self):
        session_in = SessionCreate(
            student_id=101,
            tutor_id=10,
            service_type_id=1,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
        )
        created = await self.use_case.create_session(
            creator_id=10, creator_role="tutor", session_in=session_in
        )

        update_in = SessionUpdate(status="completada", notes="Todo bien")
        updated = await self.use_case.update_session(
            session_id=created.id, user_id=10, user_role="tutor", session_in=update_in
        )

        self.assertEqual(updated.status, "completada")
        self.assertEqual(updated.notes, "Todo bien")

    async def test_update_session_unauthorized_student(self):
        session_in = SessionCreate(
            student_id=101,
            tutor_id=10,
            service_type_id=1,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
        )
        created = await self.use_case.create_session(
            creator_id=10, creator_role="tutor", session_in=session_in
        )

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
        self.assertNotIn(
            "database.models.streak",
            repo_text,
            "SessionRepository must not import Streak model directly"
        )
        self.assertNotIn(
            "database.models.notification",
            repo_text,
            "SessionRepository must not import Notification model directly"
        )
        self.assertNotIn(
            "StreakRepository(",
            repo_text,
            "SessionRepository must not instantiate StreakRepository internally"
        )
        self.assertNotIn(
            "NotificationRepository(",
            repo_text,
            "SessionRepository must not instantiate NotificationRepository internally"
        )


class TestSessionRepositoryIsolated(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.streak_repo = AsyncMock(spec=StreakRepositoryPort)
        self.notification_repo = AsyncMock(spec=NotificationRepositoryPort)
        self.transaction = AsyncMock(spec=TransactionPort)
        self.db = MagicMock()
        self.db.flush = AsyncMock()
        self.db.execute = AsyncMock()

        # Default streak return value
        self.streak_repo.update_on_session_complete.return_value = StreakOut(
            id=1, student_id=101, current_streak=1, max_streak=1, last_session_date=None
        )
        self.streak_repo.reset_on_session_absent.return_value = StreakOut(
            id=1, student_id=101, current_streak=0, max_streak=1, last_session_date=None
        )
        self.notification_repo.create_notification.return_value = NotificationOut(
            id=1, user_id=101, title="N", body="B", type="s", is_read=False, created_at=datetime.now()
        )

        self.repo = SessionRepository(
            db=self.db,
            streak_repo=self.streak_repo,
            notification_repo=self.notification_repo,
            transaction=self.transaction,
        )

    def test_constructor_requires_mandatory_dependencies(self):
        sig = inspect.signature(SessionRepository.__init__)
        for param_name in ["db", "streak_repo", "notification_repo", "transaction"]:
            self.assertIn(param_name, sig.parameters)
            self.assertEqual(
                sig.parameters[param_name].default,
                inspect.Parameter.empty,
                f"Parameter {param_name} must not have a default value",
            )

    async def test_create_sessions_delegates_notification_and_commits_once(self):
        # Mock scalars().first() for reloading session
        mock_session_orm = MagicMock()
        mock_session_orm.id = 1
        mock_session_orm.student_id = 101
        mock_session_orm.tutor_id = 10
        mock_session_orm.service_type_id = 1
        mock_session_orm.scheduled_at = datetime(2026, 8, 10, 10, 0)
        mock_session_orm.status = "programada"
        mock_session_orm.title = "Tutoría Programada"
        mock_session_orm.notes = ""
        mock_session_orm.location = "Virtual"

        # Setup student, tutor, service_type mocks
        mock_session_orm.student = create_fake_user_out(101, "S", "estudiante")
        mock_session_orm.tutor = create_fake_user_out(10, "T", "tutor")
        mock_session_orm.service_type = ServiceTypeOut(id=1, name="Individual")

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_session_orm
        self.db.execute.return_value = mock_result

        out = await self.repo.create_sessions(
            creator_id=10,
            tutor_id=10,
            student_ids=[101],
            service_type_id=1,
            scheduled_at=datetime(2026, 8, 10, 10, 0),
            status="programada",
        )

        self.notification_repo.create_notification.assert_called_once()
        self.transaction.commit.assert_called_once()
        self.assertIsInstance(out, SessionOut)

    async def test_create_sessions_notification_failure_triggers_rollback(self):
        self.notification_repo.create_notification.side_effect = RuntimeError("Notification error")

        with self.assertRaises(RuntimeError):
            await self.repo.create_sessions(
                creator_id=10,
                tutor_id=10,
                student_ids=[101],
                service_type_id=1,
                scheduled_at=datetime(2026, 8, 10, 10, 0),
                status="programada",
            )

        self.transaction.rollback.assert_called_once()
        self.transaction.commit.assert_not_called()

    async def test_update_session_completada_updates_streak_and_notifies(self):
        mock_session_orm = MagicMock()
        mock_session_orm.id = 1
        mock_session_orm.student_id = 101
        mock_session_orm.tutor_id = 10
        mock_session_orm.status = "programada"
        mock_session_orm.scheduled_at = datetime(2026, 8, 10, 10, 0)
        mock_session_orm.notes = ""
        mock_session_orm.title = "T"
        mock_session_orm.location = "V"
        mock_session_orm.service_type_id = 1
        mock_session_orm.student = create_fake_user_out(101, "S", "estudiante")
        mock_session_orm.tutor = create_fake_user_out(10, "T", "tutor")
        mock_session_orm.service_type = ServiceTypeOut(id=1, name="Indiv")

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_session_orm
        self.db.execute.return_value = mock_result

        update_in = SessionUpdate(status="completada")
        res = await self.repo.update_session(session_id=1, session_in=update_in, user_id=10)

        self.streak_repo.update_on_session_complete.assert_called_once_with(101)
        self.notification_repo.create_notification.assert_called_once()
        self.transaction.commit.assert_called_once()
        self.assertEqual(res.status, "completada")

    async def test_update_session_ausente_resets_streak_and_notifies(self):
        mock_session_orm = MagicMock()
        mock_session_orm.id = 1
        mock_session_orm.student_id = 101
        mock_session_orm.tutor_id = 10
        mock_session_orm.status = "programada"
        mock_session_orm.scheduled_at = datetime(2026, 8, 10, 10, 0)
        mock_session_orm.notes = ""
        mock_session_orm.title = "T"
        mock_session_orm.location = "V"
        mock_session_orm.service_type_id = 1
        mock_session_orm.student = create_fake_user_out(101, "S", "estudiante")
        mock_session_orm.tutor = create_fake_user_out(10, "T", "tutor")
        mock_session_orm.service_type = ServiceTypeOut(id=1, name="Indiv")

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_session_orm
        self.db.execute.return_value = mock_result

        update_in = SessionUpdate(status="ausente")
        await self.repo.update_session(session_id=1, session_in=update_in, user_id=10)

        self.streak_repo.reset_on_session_absent.assert_called_once_with(101)
        self.notification_repo.create_notification.assert_called_once()
        self.transaction.commit.assert_called_once()

    async def test_update_session_cancelada_notifies_recipient(self):
        mock_session_orm = MagicMock()
        mock_session_orm.id = 1
        mock_session_orm.student_id = 101
        mock_session_orm.tutor_id = 10
        mock_session_orm.status = "programada"
        mock_session_orm.scheduled_at = datetime(2026, 8, 10, 10, 0)
        mock_session_orm.notes = ""
        mock_session_orm.title = "T"
        mock_session_orm.location = "V"
        mock_session_orm.service_type_id = 1
        mock_session_orm.student = create_fake_user_out(101, "S", "estudiante")
        mock_session_orm.tutor = create_fake_user_out(10, "T", "tutor")
        mock_session_orm.service_type = ServiceTypeOut(id=1, name="Indiv")

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_session_orm
        self.db.execute.return_value = mock_result

        update_in = SessionUpdate(status="cancelada")
        # Tutor cancelling -> recipient should be student_id (101)
        await self.repo.update_session(session_id=1, session_in=update_in, user_id=10)

        self.notification_repo.create_notification.assert_called_once()
        call_kwargs = self.notification_repo.create_notification.call_args[1]
        self.assertEqual(call_kwargs["user_id"], 101)
        self.transaction.commit.assert_called_once()

    async def test_update_session_streak_failure_triggers_rollback(self):
        mock_session_orm = MagicMock()
        mock_session_orm.id = 1
        mock_session_orm.student_id = 101
        mock_session_orm.tutor_id = 10
        mock_session_orm.status = "programada"
        mock_session_orm.scheduled_at = datetime(2026, 8, 10, 10, 0)
        mock_session_orm.notes = ""
        mock_session_orm.title = "T"
        mock_session_orm.location = "V"
        mock_session_orm.service_type_id = 1

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_session_orm
        self.db.execute.return_value = mock_result

        self.streak_repo.update_on_session_complete.side_effect = RuntimeError("Streak failure")

        update_in = SessionUpdate(status="completada")
        with self.assertRaises(RuntimeError):
            await self.repo.update_session(session_id=1, session_in=update_in, user_id=10)

        self.transaction.rollback.assert_called_once()
        self.transaction.commit.assert_not_called()

    async def test_update_session_commit_failure_triggers_rollback(self):
        mock_session_orm = MagicMock()
        mock_session_orm.id = 1
        mock_session_orm.student_id = 101
        mock_session_orm.tutor_id = 10
        mock_session_orm.status = "programada"
        mock_session_orm.scheduled_at = datetime(2026, 8, 10, 10, 0)
        mock_session_orm.notes = ""
        mock_session_orm.title = "T"
        mock_session_orm.location = "V"
        mock_session_orm.service_type_id = 1

        mock_result = MagicMock()
        mock_result.scalars().first.return_value = mock_session_orm
        self.db.execute.return_value = mock_result

        self.transaction.commit.side_effect = RuntimeError("Commit failure")

        update_in = SessionUpdate(notes="New notes")
        with self.assertRaises(RuntimeError):
            await self.repo.update_session(session_id=1, session_in=update_in, user_id=10)

        self.transaction.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
