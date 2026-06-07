from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.schemas.streak import StreakOut
from app.models.user import User
from app.services import streak_service

router = APIRouter()

@router.get("/", response_model=StreakOut)
async def read_streak(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students have study streaks.",
        )
    return await streak_service.get_student_streak(db=db, student_id=current_user.id)
