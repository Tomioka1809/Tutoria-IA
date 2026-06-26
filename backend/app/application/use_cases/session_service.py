from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import List
from datetime import datetime, timedelta

from app.infrastructure.database.models.session import Session
from app.infrastructure.database.models.event import Event
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.tutor_assignment import TutorAssignment
from app.domain.entities.session import SessionCreate, SessionUpdate
from app.application.use_cases.streak_service import update_streak_on_session_complete, reset_streak_on_session_absent
from app.application.use_cases.notification_service import create_notification

async def get_user_sessions(db: AsyncSession, user: User) -> List[Session]:
    if user.role == "estudiante":
        result = await db.execute(
            select(Session)
            .where(Session.student_id == user.id)
            .options(
                selectinload(Session.student).selectinload(User.student_profile),
                selectinload(Session.student).selectinload(User.tutor_profile),
                selectinload(Session.student).selectinload(User.admin_profile),
                selectinload(Session.tutor).selectinload(User.tutor_profile),
                selectinload(Session.tutor).selectinload(User.student_profile),
                selectinload(Session.tutor).selectinload(User.admin_profile),
                selectinload(Session.service_type),
            )
            .order_by(Session.scheduled_at.desc())
        )
        return list(result.scalars().all())
    elif user.role == "tutor":
        result = await db.execute(
            select(Session)
            .where(Session.tutor_id == user.id)
            .options(
                selectinload(Session.student).selectinload(User.student_profile),
                selectinload(Session.student).selectinload(User.tutor_profile),
                selectinload(Session.student).selectinload(User.admin_profile),
                selectinload(Session.tutor).selectinload(User.tutor_profile),
                selectinload(Session.tutor).selectinload(User.student_profile),
                selectinload(Session.tutor).selectinload(User.admin_profile),
                selectinload(Session.service_type),
            )
            .order_by(Session.scheduled_at.desc())
        )
        return list(result.scalars().all())
    else: # admin
        result = await db.execute(
            select(Session)
            .options(
                selectinload(Session.student).selectinload(User.student_profile),
                selectinload(Session.student).selectinload(User.tutor_profile),
                selectinload(Session.student).selectinload(User.admin_profile),
                selectinload(Session.tutor).selectinload(User.tutor_profile),
                selectinload(Session.tutor).selectinload(User.student_profile),
                selectinload(Session.tutor).selectinload(User.admin_profile),
                selectinload(Session.service_type),
            )
            .order_by(Session.scheduled_at.desc())
        )
        return list(result.scalars().all())

async def create_session(db: AsyncSession, session_in: SessionCreate, creator: User):
    # Ensure creator is tutor or admin
    if creator.role not in ["tutor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors or admins can schedule tutoring sessions.",
        )
        
    student_ids_to_schedule = []
    
    if session_in.student_id is None:
        # Fetch all students assigned to this tutor
        assignment_result = await db.execute(
            select(TutorAssignment).where(TutorAssignment.tutor_id == session_in.tutor_id)
        )
        assignments = assignment_result.scalars().all()
        student_ids_to_schedule = [a.student_id for a in assignments]
        
        if not student_ids_to_schedule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No students assigned to this tutor to schedule a group session.",
            )
    else:
        student_ids_to_schedule = [session_in.student_id]
        
    created_sessions = []
    
    for s_id in student_ids_to_schedule:
        db_session = Session(
            student_id=s_id,
            tutor_id=session_in.tutor_id,
            service_type_id=session_in.service_type_id,
            scheduled_at=session_in.scheduled_at,
            status=session_in.status,
            title=session_in.title,
            notes=session_in.notes,
            location=session_in.location,
        )
        db.add(db_session)
        await db.flush() # Populate ID
        
        # Automatically create a calendar event linked to this session
        event = Event(
            created_by=creator.id,
            session_id=db_session.id,
            title=session_in.title or f"Tutoría Programada",
            starts_at=db_session.scheduled_at,
            ends_at=db_session.scheduled_at + timedelta(hours=1), # Default 1 hour
            type="tutoria"
        )
        db.add(event)
        
        # Notify the student
        await create_notification(
            db,
            user_id=db_session.student_id,
            title="Nueva tutoría asignada",
            body=f"Se ha programado una sesión de tutoría para el {db_session.scheduled_at.strftime('%d/%m/%Y a las %H:%M')}.",
            notification_type="session"
        )
        created_sessions.append(db_session.id)
        
    await db.commit()
    
    # Reload with relationships for the first created session as response
    # The frontend only expects a single SessionOut back. We return the first one.
    result = await db.execute(
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
    return result.scalars().first()

async def update_session(db: AsyncSession, session_id: int, session_in: SessionUpdate, user: User) -> Session:
    result = await db.execute(
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
        
    # Ensure they have permission (student can view/cancel, tutor can update anything)
    if user.role == "estudiante" and user.id != session.student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if user.role == "tutor" and user.id != session.tutor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
        
    # Update fields
    if session_in.scheduled_at is not None:
        session.scheduled_at = session_in.scheduled_at
        # Update linked event as well
        event_result = await db.execute(select(Event).where(Event.session_id == session.id))
        event = event_result.scalars().first()
        if event:
            event.starts_at = session.scheduled_at
            event.ends_at = session.scheduled_at + timedelta(hours=1)
            db.add(event)
            
    old_status = session.status
    if session_in.status is not None:
        session.status = session_in.status
        
    if session_in.notes is not None:
        session.notes = session_in.notes
        
    if session_in.title is not None:
        session.title = session_in.title
        
    if session_in.location is not None:
        session.location = session_in.location
        
    db.add(session)
    await db.flush()
    
    # Handle side effects of status transitions
    if session.status == "completada" and old_status != "completada":
        # Increment student's streak
        streak = await update_streak_on_session_complete(db, session.student_id)
        
        # Notify student about completed session and current streak
        await create_notification(
            db,
            user_id=session.student_id,
            title="¡Tutoría Completada!",
            body=f"Has completado tu sesión de tutoría. Tu racha actual es de {streak.current_streak} semestres.",
            notification_type="streak"
        )
    elif session.status == "ausente" and old_status != "ausente":
        # Reset student's streak
        await reset_streak_on_session_absent(db, session.student_id)
        
        # Notify student about broken streak
        await create_notification(
            db,
            user_id=session.student_id,
            title="Inasistencia a Tutoría",
            body="Se ha registrado tu inasistencia a la sesión. Tu racha ha vuelto a 0.",
            notification_type="streak"
        )
    elif session.status == "cancelada" and old_status != "cancelada":
        # Notify recipient about cancellation
        recipient_id = session.student_id if user.id == session.tutor_id else session.tutor_id
        await create_notification(
            db,
            user_id=recipient_id,
            title="Tutoría Cancelada",
            body=f"La sesión de tutoría del {session.scheduled_at.strftime('%d/%m/%Y')} ha sido cancelada.",
            notification_type="session"
        )
        
    await db.commit()
    
    return session
