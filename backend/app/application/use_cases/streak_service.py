from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date, timedelta
from app.infrastructure.database.models.streak import Streak

async def get_student_streak(db: AsyncSession, student_id: int) -> Streak:
    result = await db.execute(select(Streak).where(Streak.student_id == student_id))
    streak = result.scalars().first()
    if not streak:
        # If it doesn't exist for some reason, create it
        streak = Streak(student_id=student_id, current_streak=0, max_streak=0)
        db.add(streak)
        await db.commit()
        await db.refresh(streak)
    return streak

async def update_streak_on_session_complete(db: AsyncSession, student_id: int) -> Streak:
    streak = await get_student_streak(db, student_id)
    today = date.today()
    
    if streak.last_session_date is None:
        # First session ever
        streak.current_streak = 1
        streak.max_streak = max(streak.max_streak, 1)
        streak.last_session_date = today
    else:
        # Check if they already did a session today
        if streak.last_session_date == today:
            # Already updated today, keep current streak
            pass
        else:
            # Check if last session was in the current semester (approx. 180 days)
            days_since_last_session = (today - streak.last_session_date).days
            if days_since_last_session <= 180:
                # Active semester streak, increment
                streak.current_streak += 1
            else:
                # Broken streak (different semester), reset to 1
                streak.current_streak = 1
                
            streak.max_streak = max(streak.max_streak, streak.current_streak)
            streak.last_session_date = today
            
    db.add(streak)
    await db.commit()
    await db.refresh(streak)
    return streak

async def reset_streak_on_session_absent(db: AsyncSession, student_id: int) -> Streak:
    streak = await get_student_streak(db, student_id)
    streak.current_streak = 0
    db.add(streak)
    await db.commit()
    await db.refresh(streak)
    return streak
