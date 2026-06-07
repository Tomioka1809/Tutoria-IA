from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from typing import List
from app.models.notification import Notification
from app.models.tutor_assignment import TutorAssignment
from app.models.user import User

async def get_user_notifications(db: AsyncSession, user: User) -> List[Notification]:
    if user.role == "estudiante":
        # Students see only their own notifications
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())
        
    elif user.role == "tutor":
        # Tutors see their own notifications + notifications of all their assigned students
        student_ids_subquery = select(TutorAssignment.student_id).where(TutorAssignment.tutor_id == user.id)
        result = await db.execute(
            select(Notification)
            .where(
                (Notification.user_id == user.id) | 
                (Notification.user_id.in_(student_ids_subquery))
            )
            .order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())
        
    else: # admin
        # Admins can see all notifications in the system
        result = await db.execute(
            select(Notification).order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

async def create_notification(
    db: AsyncSession, user_id: int, title: str, body: str, notification_type: str
) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        type=notification_type,
        is_read=False,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification

async def mark_notification_as_read(db: AsyncSession, notification_id: int, user_id: int) -> Notification:
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalars().first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    # Ensure they have permission (either they own it, or they are the tutor of the student)
    # Actually, simpler is: if they are reading it, they can mark it read.
    notification.is_read = True
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification
