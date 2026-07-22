import unittest
import os
import ast
import inspect
from datetime import date, timedelta

from app.application.use_cases.streak_service import StreakUseCase
from app.application.ports.other_ports import StreakRepositoryPort
from app.application.ports.transaction_port import TransactionPort
from app.domain.entities.streak import StreakOut
from app.domain.exceptions import StreakUnavailableForRoleError


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


class FakeStreakRepository(StreakRepositoryPort):
    def __init__(self, fail_update=False, fail_reset=False):
        self.streaks = {}
        self.counter = 1
        self.fail_update = fail_update
        self.fail_reset = fail_reset

    async def get_student_streak(self, student_id: int) -> tuple[StreakOut, bool]:
        is_created = False
        if student_id not in self.streaks:
            self.streaks[student_id] = StreakOut(
                id=self.counter,
                student_id=student_id,
                current_streak=0,
                max_streak=0,
                last_session_date=None,
            )
            self.counter += 1
            is_created = True
        return self.streaks[student_id], is_created

    async def update_on_session_complete(self, student_id: int) -> StreakOut:
        if self.fail_update:
            raise RuntimeError("Update failure simulated")
        streak, _ = await self.get_student_streak(student_id)
        today = date.today()

        if streak.last_session_date is None:
            new_current = 1
            new_max = max(streak.max_streak, 1)
        elif streak.last_session_date == today:
            new_current = streak.current_streak
            new_max = streak.max_streak
        else:
            days_since = (today - streak.last_session_date).days
            if days_since <= 180:
                new_current = streak.current_streak + 1
            else:
                new_current = 1
            new_max = max(streak.max_streak, new_current)

        updated = StreakOut(
            id=streak.id,
            student_id=student_id,
            current_streak=new_current,
            max_streak=new_max,
            last_session_date=today,
        )
        self.streaks[student_id] = updated
        return updated

    async def reset_on_session_absent(self, student_id: int) -> StreakOut:
        if self.fail_reset:
            raise RuntimeError("Reset failure simulated")
        streak, _ = await self.get_student_streak(student_id)
        updated = StreakOut(
            id=streak.id,
            student_id=student_id,
            current_streak=0,
            max_streak=streak.max_streak,
            last_session_date=streak.last_session_date,
        )
        self.streaks[student_id] = updated
        return updated


class TestStreakApplication(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.repo = FakeStreakRepository()
        self.transaction = FakeTransaction()
        self.use_case = StreakUseCase(streak_repo=self.repo, transaction=self.transaction)

    async def test_read_existing_streak_does_not_commit(self):
        await self.use_case.get_student_streak(student_id=101, user_role="estudiante")
        self.assertEqual(self.transaction.commit_count, 1)

        await self.use_case.get_student_streak(student_id=101, user_role="estudiante")
        self.assertEqual(self.transaction.commit_count, 1)

    async def test_creation_of_nonexistent_streak_persists_and_commits(self):
        streak = await self.use_case.get_student_streak(student_id=101, user_role="estudiante")
        self.assertEqual(streak.student_id, 101)
        self.assertEqual(self.transaction.commit_count, 1)

    async def test_update_on_session_complete_commits_once(self):
        s1 = await self.use_case.update_streak_on_session_complete(student_id=101)
        self.assertEqual(s1.current_streak, 1)
        self.assertEqual(s1.max_streak, 1)
        self.assertEqual(self.transaction.commit_count, 1)

    async def test_reset_on_session_absent_commits_once(self):
        await self.use_case.update_streak_on_session_complete(student_id=101)
        c_before = self.transaction.commit_count
        res = await self.use_case.reset_streak_on_session_absent(student_id=101)
        self.assertEqual(res.current_streak, 0)
        self.assertEqual(self.transaction.commit_count, c_before + 1)

    async def test_same_day_does_not_double_increment(self):
        s1 = await self.use_case.update_streak_on_session_complete(student_id=101)
        s2 = await self.use_case.update_streak_on_session_complete(student_id=101)
        self.assertEqual(s1.current_streak, 1)
        self.assertEqual(s2.current_streak, 1)

    async def test_days_since_greater_than_180_resets_current_streak(self):
        self.repo.streaks[101] = StreakOut(
            id=1, student_id=101, current_streak=5, max_streak=5, last_session_date=date.today() - timedelta(days=200)
        )
        s = await self.use_case.update_streak_on_session_complete(student_id=101)
        self.assertEqual(s.current_streak, 1)
        self.assertEqual(s.max_streak, 5)

    async def test_days_since_less_or_equal_180_increments(self):
        self.repo.streaks[101] = StreakOut(
            id=1, student_id=101, current_streak=2, max_streak=2, last_session_date=date.today() - timedelta(days=30)
        )
        s = await self.use_case.update_streak_on_session_complete(student_id=101)
        self.assertEqual(s.current_streak, 3)
        self.assertEqual(s.max_streak, 3)

    async def test_max_streak_preserved_when_current_is_lower(self):
        self.repo.streaks[101] = StreakOut(
            id=1, student_id=101, current_streak=0, max_streak=10, last_session_date=date.today() - timedelta(days=5)
        )
        s = await self.use_case.update_streak_on_session_complete(student_id=101)
        self.assertEqual(s.current_streak, 1)
        self.assertEqual(s.max_streak, 10)

    async def test_non_student_role_raises_streak_unavailable_for_role_error(self):
        with self.assertRaises(StreakUnavailableForRoleError):
            await self.use_case.get_student_streak(student_id=101, user_role="tutor")

    async def test_commit_failure_on_new_streak_triggers_rollback(self):
        trans = FakeTransaction(fail_commit=True)
        use_case = StreakUseCase(streak_repo=self.repo, transaction=trans)
        with self.assertRaises(RuntimeError):
            await use_case.get_student_streak(student_id=202, user_role="estudiante")
        self.assertEqual(trans.rollback_count, 1)

    async def test_update_streak_failure_triggers_rollback(self):
        repo = FakeStreakRepository(fail_update=True)
        trans = FakeTransaction()
        use_case = StreakUseCase(streak_repo=repo, transaction=trans)
        with self.assertRaises(RuntimeError):
            await use_case.update_streak_on_session_complete(student_id=101)
        self.assertEqual(trans.rollback_count, 1)

    async def test_reset_streak_failure_triggers_rollback(self):
        repo = FakeStreakRepository(fail_reset=True)
        trans = FakeTransaction()
        use_case = StreakUseCase(streak_repo=repo, transaction=trans)
        with self.assertRaises(RuntimeError):
            await use_case.reset_streak_on_session_absent(student_id=101)
        self.assertEqual(trans.rollback_count, 1)

    def test_user_role_is_mandatory_parameter(self):
        sig = inspect.signature(StreakUseCase.get_student_streak)
        param = sig.parameters["user_role"]
        self.assertEqual(param.default, inspect.Parameter.empty, "user_role must be mandatory without default")

    def test_architectural_decoupling_streak(self):
        use_case_path = os.path.join(
            os.path.dirname(__file__),
            "../../app/application/use_cases/streak_service.py"
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
                    f"Forbidden import '{mod}' found in streak_service.py"
                )


if __name__ == "__main__":
    unittest.main()
