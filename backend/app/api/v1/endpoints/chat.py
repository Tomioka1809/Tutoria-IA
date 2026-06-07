from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.schemas.chat import ConversationOut, MessageOut, MessageCreate
from app.models.user import User
from app.services import chat_service

router = APIRouter()

@router.get("/conversation", response_model=ConversationOut)
async def read_conversation(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    if current_user.role != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students can access TutorIA chatbot conversations.",
        )
    return await chat_service.get_or_create_conversation(db=db, student_id=current_user.id)

@router.post("/message", response_model=MessageOut)
async def send_message(
    message_in: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students can chat with TutorIA.",
        )
    return await chat_service.send_chat_message(
        db=db, student_id=current_user.id, user_content=message_in.content
    )
