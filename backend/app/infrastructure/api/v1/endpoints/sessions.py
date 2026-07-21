from fastapi import APIRouter, Depends, status
from typing import List

from app.infrastructure.api.dependencies import get_current_user, get_session_use_case
from app.domain.entities.session import SessionCreate, SessionUpdate, SessionOut
from app.infrastructure.database.models.user import User
from app.application.use_cases.session_service import SessionUseCase

router = APIRouter()

@router.get("/", response_model=List[SessionOut])
async def read_sessions(
    current_user: User = Depends(get_current_user),
    session_use_case: SessionUseCase = Depends(get_session_use_case)
):
    return await session_use_case.get_user_sessions(
        user_id=current_user.id,
        user_role=current_user.role
    )

@router.post("/", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_new_session(
    session_in: SessionCreate,
    current_user: User = Depends(get_current_user),
    session_use_case: SessionUseCase = Depends(get_session_use_case)
):
    return await session_use_case.create_session(
        creator_id=current_user.id,
        creator_role=current_user.role,
        session_in=session_in
    )

@router.put("/{session_id}", response_model=SessionOut)
async def update_existing_session(
    session_id: int,
    session_in: SessionUpdate,
    current_user: User = Depends(get_current_user),
    session_use_case: SessionUseCase = Depends(get_session_use_case)
):
    return await session_use_case.update_session(
        session_id=session_id,
        user_id=current_user.id,
        user_role=current_user.role,
        session_in=session_in
    )
