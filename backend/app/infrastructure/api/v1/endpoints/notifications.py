from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.infrastructure.api.dependencies import get_db, get_current_user
from app.domain.entities.notification import NotificationOut
from app.infrastructure.database.models.user import User
from app.application.use_cases import notification_service

router = APIRouter()

@router.get("/", response_model=List[NotificationOut])
async def read_notifications(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return await notification_service.get_user_notifications(db=db, user=current_user)

@router.put("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await notification_service.mark_notification_as_read(
        db=db, notification_id=notification_id, user_id=current_user.id
    )
