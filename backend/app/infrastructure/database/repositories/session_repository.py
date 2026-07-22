from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.application.ports.other_ports import (
    SessionRepositoryPort,
    StreakRepositoryPort,
    NotificationRepositoryPort,
)
from app.application.ports.transaction_port import TransactionPort
from app.application.dtos.session_dtos import SessionAccessDTO
from app.domain.entities.session import SessionOut, SessionUpdate
from app.infrastructure.database.models.session import Session
from app.infrastructure.database.models.event import Event
from app.infrastructure.database.models.user import User


class SessionRepository(SessionRepositoryPort):
    def __init__(
        self,
        db: AsyncSession,
        streak_repo: StreakRepositoryPort,
        notification_repo: NotificationRepositoryPort,
        transaction: TransactionPort,
    ):
        self.db = db
        self.streak_repo = streak_repo
        self.notification_repo = notification_repo
        self.transaction = transaction

    async def get_user_sessions(self, user_id: int, user_role: str) -> List[SessionOut]:
        if user_role == "estudiante":
            query = select(Session).where(Session.student_id == user_id)
        elif user_role == "tutor":
            query = select(Session).where(Session.tutor_id == user_id)
        else:  # admin
            query = select(Session)

        query = query.options(
            selectinload(Session.student).selectinload(User.student_profile),
            selectinload(Session.student).selectinload(User.tutor_profile),
            selectinload(Session.student).selectinload(User.admin_profile),
            selectinload(Session.tutor).selectinload(User.tutor_profile),
            selectinload(Session.tutor).selectinload(User.student_profile),
            selectinload(Session.tutor).selectinload(User.admin_profile),
            selectinload(Session.service_type),
        ).order_by(Session.scheduled_at.desc())

        result = await self.db.execute(query)
        db_sessions = result.scalars().all()
        return [SessionOut.model_validate(s) for s in db_sessions]

    async def get_access_data(self, session_id: int) -> Optional[SessionAccessDTO]:
        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalars().first()
        if not session:
            return None
        return SessionAccessDTO(
            id=session.id,
            student_id=session.student_id,
            tutor_id=session.tutor_id,
            status=session.status,
        )

    async def create_sessions(
        self,
        creator_id: int,
        tutor_id: int,
        student_ids: List[int],
        service_type_id: int,
        scheduled_at: datetime,
        status: str,
        title: Optional[str] = None,
        notes: Optional[str] = None,
        location: Optional[str] = None,
    ) -> SessionOut:
        created_sessions = []
        try:
            for s_id in student_ids:
                db_session = Session(
                    student_id=s_id,
                    tutor_id=tutor_id,
                    service_type_id=service_type_id,
                    scheduled_at=scheduled_at,
                    status=status,
                    title=title,
                    notes=notes,
                    location=location,
                )
                self.db.add(db_session)
                await self.db.flush()  # Populate ID

                # Create linked calendar event
                event = Event(
                    created_by=creator_id,
                    session_id=db_session.id,
                    title=title or "Tutoría Programada",
                    starts_at=db_session.scheduled_at,
                    ends_at=db_session.scheduled_at + timedelta(hours=1),
                    type="tutoria",
                )
                self.db.add(event)

                # Delegate notification to notification repository
                await self.notification_repo.create_notification(
                    user_id=db_session.student_id,
                    title="Nueva tutoría asignada",
                    body=f"Se ha programado una sesión de tutoría para el {db_session.scheduled_at.strftime('%d/%m/%Y a las %H:%M')}.",
                    notification_type="session",
                )
                created_sessions.append(db_session.id)

            await self.transaction.commit()
        except Exception:
            await self.transaction.rollback()
            raise

        # Reload first created session with relationships and map to SessionOut
        result = await self.db.execute(
            select(Session)
            .where(Session.id == created_sessions[0])
            .options(
                selectinload(Session.student).selectinload(User.student_profile),
                selectinload(Session.student).selectinload(User.tutor_profile),
                selectinload(Session.student).selectinload(User.admin_profile),
                selectinload(Session.tutor).selectinload(User.tutor_profile),
                selectinload(Session.tutor).selectinload(User.student_profile),
                selectinload(Session.tutor).selectinload(User.admin_profile),
                selectinload(Session.service_type),
            )
        )
        first_session = result.scalars().first()
        return SessionOut.model_validate(first_session)

    async def update_session(
        self,
        session_id: int,
        session_in: SessionUpdate,
        user_id: int,
    ) -> Optional[SessionOut]:
        result = await self.db.execute(
            select(Session)
            .where(Session.id == session_id)
            .options(
                selectinload(Session.student).selectinload(User.student_profile),
                selectinload(Session.student).selectinload(User.tutor_profile),
                selectinload(Session.student).selectinload(User.admin_profile),
                selectinload(Session.tutor).selectinload(User.tutor_profile),
                selectinload(Session.tutor).selectinload(User.student_profile),
                selectinload(Session.tutor).selectinload(User.admin_profile),
                selectinload(Session.service_type),
            )
        )
        session = result.scalars().first()
        if not session:
            return None

        try:
            # Update fields
            if session_in.scheduled_at is not None:
                session.scheduled_at = session_in.scheduled_at
                event_result = await self.db.execute(
                    select(Event).where(Event.session_id == session.id)
                )
                event = event_result.scalars().first()
                if event:
                    event.starts_at = session.scheduled_at
                    event.ends_at = session.scheduled_at + timedelta(hours=1)
                    self.db.add(event)

            old_status = session.status
            if session_in.status is not None:
                session.status = session_in.status

            if session_in.notes is not None:
                session.notes = session_in.notes

            if session_in.title is not None:
                session.title = session_in.title

            if session_in.location is not None:
                session.location = session_in.location

            self.db.add(session)
            await self.db.flush()

            # Handle side effects of status transitions via repositories
            if session.status == "completada" and old_status != "completada":
                streak = await self.streak_repo.update_on_session_complete(session.student_id)
                await self.notification_repo.create_notification(
                    user_id=session.student_id,
                    title="¡Tutoría Completada!",
                    body=f"Has completado tu sesión de tutoría. Tu racha actual es de {streak.current_streak} semestres.",
                    notification_type="streak",
                )
            elif session.status == "ausente" and old_status != "ausente":
                await self.streak_repo.reset_on_session_absent(session.student_id)
                await self.notification_repo.create_notification(
                    user_id=session.student_id,
                    title="Inasistencia a Tutoría",
                    body="Se ha registrado tu inasistencia a la sesión. Tu racha ha vuelto a 0.",
                    notification_type="streak",
                )
            elif session.status == "cancelada" and old_status != "cancelada":
                recipient_id = session.student_id if user_id == session.tutor_id else session.tutor_id
                await self.notification_repo.create_notification(
                    user_id=recipient_id,
                    title="Tutoría Cancelada",
                    body=f"La sesión de tutoría del {session.scheduled_at.strftime('%d/%m/%Y')} ha sido cancelada.",
                    notification_type="session",
                )

            await self.transaction.commit()
        except Exception:
            await self.transaction.rollback()
            raise

        return SessionOut.model_validate(session)
