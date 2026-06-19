from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.infrastructure.api.dependencies import get_db, get_current_user
from app.domain.entities.session import SessionCreate, SessionUpdate, SessionOut
from app.infrastructure.database.models.user import User
from app.application.use_cases import session_service

router = APIRouter()

@router.get("/", response_model=List[SessionOut])
async def read_sessions(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return await session_service.get_user_sessions(db=db, user=current_user)

@router.post("/", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_new_session(
    session_in: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await session_service.create_session(
        db=db, session_in=session_in, creator=current_user
    )

@router.put("/{session_id}", response_model=SessionOut)
async def update_existing_session(
    session_id: int,
    session_in: SessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await session_service.update_session(
        db=db, session_id=session_id, session_in=session_in, user=current_user
    )
