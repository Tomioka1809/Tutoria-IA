from fastapi import APIRouter, Depends
from app.infrastructure.api.dependencies import get_current_user, get_streak_use_case
from app.domain.entities.streak import StreakOut
from app.infrastructure.database.models.user import User
from app.application.use_cases.streak_service import StreakUseCase

router = APIRouter()

@router.get("/", response_model=StreakOut)
async def read_streak(
    current_user: User = Depends(get_current_user),
    streak_use_case: StreakUseCase = Depends(get_streak_use_case)
):
    return await streak_use_case.get_student_streak(
        student_id=current_user.id,
        user_role=current_user.role
    )
