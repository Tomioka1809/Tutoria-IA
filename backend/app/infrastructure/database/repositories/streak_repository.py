from typing import Tuple
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.application.ports.other_ports import StreakRepositoryPort
from app.domain.entities.streak import StreakOut
from app.infrastructure.database.models.streak import Streak


class StreakRepository(StreakRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_student_streak(self, student_id: int) -> Tuple[StreakOut, bool]:
        result = await self.db.execute(select(Streak).where(Streak.student_id == student_id))
        streak = result.scalars().first()
        is_created = False
        if not streak:
            streak = Streak(student_id=student_id, current_streak=0, max_streak=0)
            self.db.add(streak)
            await self.db.flush()
            is_created = True
        return StreakOut.model_validate(streak), is_created

    async def update_on_session_complete(self, student_id: int) -> StreakOut:
        result = await self.db.execute(select(Streak).where(Streak.student_id == student_id))
        streak = result.scalars().first()
        if not streak:
            streak = Streak(student_id=student_id, current_streak=0, max_streak=0)
            self.db.add(streak)

        today = date.today()
        if streak.last_session_date is None:
            streak.current_streak = 1
            streak.max_streak = max(streak.max_streak, 1)
            streak.last_session_date = today
        elif streak.last_session_date != today:
            days_since = (today - streak.last_session_date).days
            if days_since <= 180:
                streak.current_streak += 1
            else:
                streak.current_streak = 1
            streak.max_streak = max(streak.max_streak, streak.current_streak)
            streak.last_session_date = today

        self.db.add(streak)
        await self.db.flush()
        return StreakOut.model_validate(streak)

    async def reset_on_session_absent(self, student_id: int) -> StreakOut:
        result = await self.db.execute(select(Streak).where(Streak.student_id == student_id))
        streak = result.scalars().first()
        if not streak:
            streak = Streak(student_id=student_id, current_streak=0, max_streak=0)
        streak.current_streak = 0
        self.db.add(streak)
        await self.db.flush()
        return StreakOut.model_validate(streak)
