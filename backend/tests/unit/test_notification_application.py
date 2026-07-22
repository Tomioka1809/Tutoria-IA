import unittest
import os
import ast
import inspect
from datetime import datetime

from app.application.use_cases.notification_service import NotificationUseCase
from app.application.ports.other_ports import NotificationRepositoryPort
from app.application.ports.repository_ports import TutorAssignmentRepositoryPort
from app.application.ports.transaction_port import TransactionPort
from app.application.dtos.notification_dtos import NotificationAccessDTO
from app.domain.entities.notification import NotificationOut
from app.domain.exceptions import ResourceNotFoundError, NotAuthorizedError


class FakeTransaction(TransactionPort):
    def __init__(self, fail_commit=False):
        self.commit_count = 0
        self.rollback_count = 0
        self.fail_commit = fail_commit

    async def commit(self) -> None:
        if self.fail_commit:
            raise RuntimeError("Commit failure simulated")
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1


class FakeNotificationRepository(NotificationRepositoryPort):
    def __init__(self, fail_create=False, fail_mark=False):
        self.notifications = {}
        self.counter = 1
        self.fail_create = fail_create
        self.fail_mark = fail_mark

    async def get_user_notifications(self, user_id: int, user_role: str) -> list[NotificationOut]:
        return [n for n in self.notifications.values() if n.user_id == user_id]

    async def get_unread_count(self, user_id: int) -> int:
        return len([n for n in self.notifications.values() if n.user_id == user_id and not n.is_read])

    async def get_access_data(self, notification_id: int) -> NotificationAccessDTO | None:
        noti = self.notifications.get(notification_id)
        if not noti:
            return None
        return NotificationAccessDTO(
            id=noti.id,
            user_id=noti.user_id,
            is_read=noti.is_read,
        )

    async def create_notification(
        self, user_id: int, title: str, body: str, notification_type: str
    ) -> NotificationOut:
        if self.fail_create:
            raise RuntimeError("Create notification failure simulated")
        noti = NotificationOut(
            id=self.counter,
            user_id=user_id,
            title=title,
            body=body,
            type=notification_type,
            is_read=False,
            created_at=datetime.now(),
        )
        self.notifications[self.counter] = noti
        self.counter += 1
        return noti

    async def mark_as_read(self, notification_id: int) -> NotificationOut | None:
        if self.fail_mark:
            raise RuntimeError("Mark as read failure simulated")
        noti = self.notifications.get(notification_id)
        if not noti:
            return None
        updated = NotificationOut(
            id=noti.id,
            user_id=noti.user_id,
            title=noti.title,
            body=noti.body,
            type=noti.type,
            is_read=True,
            created_at=noti.created_at,
        )
        self.notifications[notification_id] = updated
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


class TestNotificationApplication(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.repo = FakeNotificationRepository()
        self.tutor_assignment_repo = FakeTutorAssignmentRepository(
            assigned_students_map={10: [101, 102]}
        )
        self.transaction = FakeTransaction()
        self.use_case = NotificationUseCase(
            notification_repo=self.repo,
            tutor_assignment_repo=self.tutor_assignment_repo,
            transaction=self.transaction,
        )

    async def test_read_operations_do_not_commit(self):
        await self.use_case.get_user_notifications(user_id=101, user_role="estudiante")
        await self.use_case.get_unread_count(user_id=101)
        self.assertEqual(self.transaction.commit_count, 0)

    async def test_create_notification_commits_once(self):
        noti = await self.use_case.create_notification(
            user_id=101, title="Test", body="Body test", notification_type="session"
        )
        self.assertEqual(self.transaction.commit_count, 1)
        self.assertEqual(noti.user_id, 101)

    async def test_student_can_mark_own_notification(self):
        noti = await self.use_case.create_notification(
            user_id=101, title="Test", body="Body test", notification_type="session"
        )
        c_before = self.transaction.commit_count
        read_noti = await self.use_case.mark_notification_as_read(
            notification_id=noti.id, user_id=101, user_role="estudiante"
        )
        self.assertTrue(read_noti.is_read)
        self.assertEqual(self.transaction.commit_count, c_before + 1)

    async def test_student_cannot_mark_other_student_notification(self):
        noti = await self.use_case.create_notification(
            user_id=101, title="Test", body="Body test", notification_type="session"
        )
        c_before = self.transaction.commit_count
        with self.assertRaises(NotAuthorizedError):
            await self.use_case.mark_notification_as_read(
                notification_id=noti.id, user_id=999, user_role="estudiante"
            )
        self.assertEqual(self.transaction.commit_count, c_before)
        self.assertEqual(self.transaction.rollback_count, 0)
        self.assertFalse(self.repo.notifications[noti.id].is_read)

    async def test_tutor_can_mark_own_notification(self):
        noti = await self.use_case.create_notification(
            user_id=10, title="Tutor Noti", body="Body", notification_type="session"
        )
        read_noti = await self.use_case.mark_notification_as_read(
            notification_id=noti.id, user_id=10, user_role="tutor"
        )
        self.assertTrue(read_noti.is_read)

    async def test_tutor_can_mark_assigned_student_notification(self):
        noti = await self.use_case.create_notification(
            user_id=101, title="Student Noti", body="Body", notification_type="session"
        )
        read_noti = await self.use_case.mark_notification_as_read(
            notification_id=noti.id, user_id=10, user_role="tutor"
        )
        self.assertTrue(read_noti.is_read)

    async def test_tutor_cannot_mark_unassigned_student_notification(self):
        noti = await self.use_case.create_notification(
            user_id=999, title="Unassigned Student Noti", body="Body", notification_type="session"
        )
        with self.assertRaises(NotAuthorizedError):
            await self.use_case.mark_notification_as_read(
                notification_id=noti.id, user_id=10, user_role="tutor"
            )
        self.assertEqual(self.transaction.rollback_count, 0)
        self.assertFalse(self.repo.notifications[noti.id].is_read)

    async def test_admin_can_mark_any_notification(self):
        noti = await self.use_case.create_notification(
            user_id=999, title="Random Noti", body="Body", notification_type="session"
        )
        read_noti = await self.use_case.mark_notification_as_read(
            notification_id=noti.id, user_id=777, user_role="admin"
        )
        self.assertTrue(read_noti.is_read)

    async def test_mark_as_read_nonexistent(self):
        with self.assertRaises(ResourceNotFoundError):
            await self.use_case.mark_notification_as_read(
                notification_id=9999, user_id=101, user_role="estudiante"
            )

    async def test_create_notification_repo_failure_triggers_rollback(self):
        repo = FakeNotificationRepository(fail_create=True)
        trans = FakeTransaction()
        use_case = NotificationUseCase(
            notification_repo=repo,
            tutor_assignment_repo=self.tutor_assignment_repo,
            transaction=trans,
        )
        with self.assertRaises(RuntimeError):
            await use_case.create_notification(user_id=101, title="T", body="B", notification_type="s")
        self.assertEqual(trans.rollback_count, 1)

    async def test_create_notification_commit_failure_triggers_rollback(self):
        trans = FakeTransaction(fail_commit=True)
        use_case = NotificationUseCase(
            notification_repo=self.repo,
            tutor_assignment_repo=self.tutor_assignment_repo,
            transaction=trans,
        )
        with self.assertRaises(RuntimeError):
            await use_case.create_notification(user_id=101, title="T", body="B", notification_type="s")
        self.assertEqual(trans.rollback_count, 1)

    async def test_mark_as_read_repo_failure_after_auth_triggers_rollback(self):
        noti = await self.use_case.create_notification(
            user_id=101, title="Test", body="Body test", notification_type="session"
        )
        self.repo.fail_mark = True
        with self.assertRaises(RuntimeError):
            await self.use_case.mark_notification_as_read(
                notification_id=noti.id, user_id=101, user_role="estudiante"
            )
        self.assertEqual(self.transaction.rollback_count, 1)

    async def test_mark_as_read_commit_failure_triggers_rollback(self):
        trans = FakeTransaction(fail_commit=True)
        use_case = NotificationUseCase(
            notification_repo=self.repo,
            tutor_assignment_repo=self.tutor_assignment_repo,
            transaction=trans,
        )
        noti = await self.repo.create_notification(
            user_id=101, title="Test", body="Body test", notification_type="session"
        )
        with self.assertRaises(RuntimeError):
            await use_case.mark_notification_as_read(
                notification_id=noti.id, user_id=101, user_role="estudiante"
            )
        self.assertEqual(trans.rollback_count, 1)

    def test_user_role_is_mandatory_parameter(self):
        sig = inspect.signature(NotificationUseCase.mark_notification_as_read)
        param = sig.parameters["user_role"]
        self.assertEqual(param.default, inspect.Parameter.empty, "user_role must be mandatory without default")

    def test_architectural_decoupling_notification(self):
        use_case_path = os.path.join(
            os.path.dirname(__file__),
            "../../app/application/use_cases/notification_service.py"
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
                    f"Forbidden import '{mod}' found in notification_service.py"
                )


if __name__ == "__main__":
    unittest.main()
