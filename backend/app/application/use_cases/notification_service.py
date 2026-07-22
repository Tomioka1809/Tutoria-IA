from typing import List
from app.application.ports.other_ports import NotificationRepositoryPort
from app.application.ports.repository_ports import TutorAssignmentRepositoryPort
from app.application.ports.transaction_port import TransactionPort
from app.domain.entities.notification import NotificationOut
from app.domain.exceptions import ResourceNotFoundError, NotAuthorizedError


class NotificationUseCase:
    def __init__(
        self,
        notification_repo: NotificationRepositoryPort,
        tutor_assignment_repo: TutorAssignmentRepositoryPort,
        transaction: TransactionPort,
    ):
        self.notification_repo = notification_repo
        self.tutor_assignment_repo = tutor_assignment_repo
        self.transaction = transaction

    async def get_user_notifications(self, user_id: int, user_role: str) -> List[NotificationOut]:
        return await self.notification_repo.get_user_notifications(user_id=user_id, user_role=user_role)

    async def get_unread_count(self, user_id: int) -> int:
        return await self.notification_repo.get_unread_count(user_id=user_id)

    async def create_notification(
        self, user_id: int, title: str, body: str, notification_type: str
    ) -> NotificationOut:
        try:
            notification = await self.notification_repo.create_notification(
                user_id=user_id, title=title, body=body, notification_type=notification_type
            )
            await self.transaction.commit()
            return notification
        except Exception:
            await self.transaction.rollback()
            raise

    async def mark_notification_as_read(
        self, notification_id: int, user_id: int, user_role: str
    ) -> NotificationOut:
        access_data = await self.notification_repo.get_access_data(notification_id)
        if not access_data:
            raise ResourceNotFoundError("Notification not found")

        # Authorization rules
        is_allowed = False
        if user_role == "admin":
            is_allowed = True
        elif user_role == "estudiante":
            is_allowed = (user_id == access_data.user_id)
        elif user_role == "tutor":
            if user_id == access_data.user_id:
                is_allowed = True
            else:
                assigned_student_ids = await self.tutor_assignment_repo.get_assigned_student_ids(user_id)
                is_allowed = (access_data.user_id in assigned_student_ids)

        if not is_allowed:
            raise NotAuthorizedError("Not authorized to access this notification")

        try:
            notification = await self.notification_repo.mark_as_read(notification_id=notification_id)
            if not notification:
                raise ResourceNotFoundError("Notification not found")
            await self.transaction.commit()
            return notification
        except Exception:
            await self.transaction.rollback()
            raise
