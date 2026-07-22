from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.application.ports.other_ports import NotificationRepositoryPort
from app.application.dtos.notification_dtos import NotificationAccessDTO
from app.domain.entities.notification import NotificationOut
from app.infrastructure.database.models.notification import Notification
from app.infrastructure.database.models.tutor_assignment import TutorAssignment


class NotificationRepository(NotificationRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_notifications(self, user_id: int, user_role: str) -> List[NotificationOut]:
        if user_role == "estudiante":
            query = select(Notification).where(Notification.user_id == user_id)
        elif user_role == "tutor":
            student_ids_subquery = select(TutorAssignment.student_id).where(TutorAssignment.tutor_id == user_id)
            query = select(Notification).where(
                (Notification.user_id == user_id) | (Notification.user_id.in_(student_ids_subquery))
            )
        else:  # admin
            query = select(Notification)

        result = await self.db.execute(query.order_by(Notification.created_at.desc()))
        db_notifications = result.scalars().all()
        return [NotificationOut.model_validate(n) for n in db_notifications]

    async def get_unread_count(self, user_id: int) -> int:
        result = await self.db.execute(
            select(Notification).where(Notification.user_id == user_id, Notification.is_read == False)
        )
        return len(result.scalars().all())

    async def get_access_data(self, notification_id: int) -> Optional[NotificationAccessDTO]:
        result = await self.db.execute(select(Notification).where(Notification.id == notification_id))
        noti = result.scalars().first()
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
        noti = Notification(
            user_id=user_id,
            title=title,
            body=body,
            type=notification_type,
            is_read=False,
        )
        self.db.add(noti)
        await self.db.flush()
        return NotificationOut.model_validate(noti)

    async def mark_as_read(self, notification_id: int) -> Optional[NotificationOut]:
        result = await self.db.execute(select(Notification).where(Notification.id == notification_id))
        noti = result.scalars().first()
        if not noti:
            return None
        noti.is_read = True
        self.db.add(noti)
        await self.db.flush()
        return NotificationOut.model_validate(noti)
