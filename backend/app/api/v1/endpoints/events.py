from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.schemas.event import EventCreate, EventOut
from app.models.event import Event
from app.models.user import User
from app.models.tutor_assignment import TutorAssignment
from app.models.session import Session

router = APIRouter()

@router.get("/", response_model=List[EventOut])
async def read_events(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role == "estudiante":
        # Students see events created by their assigned tutors OR linked to their sessions
        tutor_ids_subquery = select(TutorAssignment.tutor_id).where(TutorAssignment.student_id == current_user.id)
        session_ids_subquery = select(Session.id).where(Session.student_id == current_user.id)
        
        result = await db.execute(
            select(Event).where(
                (Event.created_by.in_(tutor_ids_subquery)) | 
                (Event.session_id.in_(session_ids_subquery))
            )
        )
        return list(result.scalars().all())
        
    elif current_user.role == "tutor":
        # Tutors see events they created
        result = await db.execute(select(Event).where(Event.created_by == current_user.id))
        return list(result.scalars().all())
        
    else: # admin
        result = await db.execute(select(Event))
        return list(result.scalars().all())

@router.post("/", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_new_event(
    event_in: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ["tutor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tutors or admins can create events.",
        )
        
    db_event = Event(
        created_by=current_user.id,
        session_id=event_in.session_id,
        title=event_in.title,
        starts_at=event_in.starts_at,
        ends_at=event_in.ends_at,
        type=event_in.type,
    )
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event
