from typing import List, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.application.ports.other_ports import SessionRepositoryPort
from app.application.dtos.session_dtos import SessionAccessDTO
from app.domain.entities.session import SessionOut, SessionUpdate
from app.infrastructure.database.models.session import Session
from app.infrastructure.database.models.event import Event
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.streak import Streak
from app.infrastructure.database.models.notification import Notification


class SessionRepository(SessionRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

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

            # Create notification
            notification = Notification(
                user_id=db_session.student_id,
                title="Nueva tutoría asignada",
                body=f"Se ha programado una sesión de tutoría para el {db_session.scheduled_at.strftime('%d/%m/%Y a las %H:%M')}.",
                type="session",
                is_read=False,
            )
            self.db.add(notification)
            created_sessions.append(db_session.id)

        await self.db.commit()

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

        # Handle side effects of status transitions
        if session.status == "completada" and old_status != "completada":
            # Update streak
            streak_result = await self.db.execute(
                select(Streak).where(Streak.student_id == session.student_id)
            )
            streak = streak_result.scalars().first()
            if not streak:
                streak = Streak(student_id=session.student_id, current_streak=0, max_streak=0)
                self.db.add(streak)

            today = date.today()
            if streak.last_session_date is None:
                streak.current_streak = 1
                streak.max_streak = max(streak.max_streak, 1)
                streak.last_session_date = today
            elif streak.last_session_date != today:
                days = (today - streak.last_session_date).days
                if days <= 180:
                    streak.current_streak += 1
                else:
                    streak.current_streak = 1
                streak.max_streak = max(streak.max_streak, streak.current_streak)
                streak.last_session_date = today

            self.db.add(streak)

            # Notification
            noti = Notification(
                user_id=session.student_id,
                title="¡Tutoría Completada!",
                body=f"Has completado tu sesión de tutoría. Tu racha actual es de {streak.current_streak} semestres.",
                type="streak",
                is_read=False,
            )
            self.db.add(noti)

        elif session.status == "ausente" and old_status != "ausente":
            # Reset streak
            streak_result = await self.db.execute(
                select(Streak).where(Streak.student_id == session.student_id)
            )
            streak = streak_result.scalars().first()
            if not streak:
                streak = Streak(student_id=session.student_id, current_streak=0, max_streak=0)
            streak.current_streak = 0
            self.db.add(streak)

            # Notification
            noti = Notification(
                user_id=session.student_id,
                title="Inasistencia a Tutoría",
                body="Se ha registrado tu inasistencia a la sesión. Tu racha ha vuelto a 0.",
                type="streak",
                is_read=False,
            )
            self.db.add(noti)

        elif session.status == "cancelada" and old_status != "cancelada":
            recipient_id = session.student_id if user_id == session.tutor_id else session.tutor_id
            noti = Notification(
                user_id=recipient_id,
                title="Tutoría Cancelada",
                body=f"La sesión de tutoría del {session.scheduled_at.strftime('%d/%m/%Y')} ha sido cancelada.",
                type="session",
                is_read=False,
            )
            self.db.add(noti)

        await self.db.commit()
        return SessionOut.model_validate(session)
