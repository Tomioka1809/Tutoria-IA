from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.application.ports.repository_ports import CalendarRepositoryPort
from app.application.dtos.chat_tool_dtos import CalendarDataDTO, CalendarSessionDTO, CalendarEventDTO
from app.infrastructure.database.models.session import Session
from app.infrastructure.database.models.event import Event
from app.infrastructure.database.models.tutor_assignment import TutorAssignment
from app.infrastructure.database.models.user import User

class CalendarRepository(CalendarRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_calendar_events_data(
        self, user_id: int, role: str, start_dt: datetime, end_dt: datetime
    ) -> CalendarDataDTO:
        if role == "estudiante":
            session_query = select(Session).where(
                Session.student_id == user_id,
                Session.scheduled_at >= start_dt,
                Session.scheduled_at <= end_dt
            ).options(
                selectinload(Session.tutor).selectinload(User.tutor_profile),
                selectinload(Session.service_type)
            )
        else:
            session_query = select(Session).where(
                Session.tutor_id == user_id,
                Session.scheduled_at >= start_dt,
                Session.scheduled_at <= end_dt
            ).options(
                selectinload(Session.student).selectinload(User.student_profile),
                selectinload(Session.service_type)
            )

        sessions_res = await self.db.execute(session_query)
        sessions = sessions_res.scalars().all()

        if role == "estudiante":
            tutor_ids_subquery = select(TutorAssignment.tutor_id).where(TutorAssignment.student_id == user_id)
            session_ids_subquery = select(Session.id).where(Session.student_id == user_id)
            event_query = select(Event).where(
                (Event.starts_at >= start_dt) & (Event.starts_at <= end_dt) &
                ((Event.created_by.in_(tutor_ids_subquery)) | (Event.session_id.in_(session_ids_subquery)))
            )
        else:
            event_query = select(Event).where(
                Event.created_by == user_id,
                Event.starts_at >= start_dt,
                Event.starts_at <= end_dt
            )

        events_res = await self.db.execute(event_query)
        events = events_res.scalars().all()

        result_data: CalendarDataDTO = {
            "sessions": [],
            "events": []
        }

        for s in sessions:
            other_name = s.tutor.full_name if role == "estudiante" else s.student.full_name
            session_dto: CalendarSessionDTO = {
                "session_id": s.id,
                "title": s.title or (s.service_type.name if s.service_type else "Tutoría"),
                "scheduled_at": s.scheduled_at.strftime("%Y-%m-%d %H:%M:%S"),
                "status": s.status,
                "location": s.location or "No definido",
                "notes": s.notes or "",
                "other_participant": other_name
            }
            result_data["sessions"].append(session_dto)

        for e in events:
            event_dto: CalendarEventDTO = {
                "event_id": e.id,
                "title": e.title,
                "starts_at": e.starts_at.strftime("%Y-%m-%d %H:%M:%S"),
                "ends_at": e.ends_at.strftime("%Y-%m-%d %H:%M:%S"),
                "type": e.type
            }
            result_data["events"].append(event_dto)

        return result_data
