from fastapi import APIRouter, Depends
from typing import List

from app.infrastructure.api.dependencies import get_current_user, get_notification_use_case
from app.domain.entities.notification import NotificationOut
from app.infrastructure.database.models.user import User
from app.application.use_cases.notification_service import NotificationUseCase

router = APIRouter()

@router.get("/", response_model=List[NotificationOut])
async def read_notifications(
    current_user: User = Depends(get_current_user),
    notification_use_case: NotificationUseCase = Depends(get_notification_use_case)
):
    return await notification_use_case.get_user_notifications(
        user_id=current_user.id,
        user_role=current_user.role
    )

@router.put("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    notification_use_case: NotificationUseCase = Depends(get_notification_use_case)
):
    return await notification_use_case.mark_notification_as_read(
        notification_id=notification_id,
        user_id=current_user.id,
        user_role=current_user.role
    )
