from app.application.ports.other_ports import StreakRepositoryPort
from app.application.ports.transaction_port import TransactionPort
from app.domain.entities.streak import StreakOut
from app.domain.exceptions import StreakUnavailableForRoleError


class StreakUseCase:
    def __init__(self, streak_repo: StreakRepositoryPort, transaction: TransactionPort):
        self.streak_repo = streak_repo
        self.transaction = transaction

    async def get_student_streak(self, student_id: int, user_role: str) -> StreakOut:
        if user_role != "estudiante":
            raise StreakUnavailableForRoleError("Only students have study streaks.")
        streak, is_created = await self.streak_repo.get_student_streak(student_id)
        if is_created:
            try:
                await self.transaction.commit()
            except Exception:
                await self.transaction.rollback()
                raise
        return streak

    async def update_streak_on_session_complete(self, student_id: int) -> StreakOut:
        try:
            streak = await self.streak_repo.update_on_session_complete(student_id)
            await self.transaction.commit()
            return streak
        except Exception:
            await self.transaction.rollback()
            raise

    async def reset_streak_on_session_absent(self, student_id: int) -> StreakOut:
        try:
            streak = await self.streak_repo.reset_on_session_absent(student_id)
            await self.transaction.commit()
            return streak
        except Exception:
            await self.transaction.rollback()
            raise
