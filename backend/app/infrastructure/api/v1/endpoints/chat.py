from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.api.dependencies import get_current_user, get_chat_use_case
from app.domain.entities.chat import ConversationOut, MessageOut, MessageCreate
from app.infrastructure.database.models.user import User
from app.application.use_cases.chat_use_cases import ChatUseCase

router = APIRouter()

@router.get("/conversation", response_model=ConversationOut)
async def read_conversation(
    current_user: User = Depends(get_current_user),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    if current_user.role != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students can access TutorIA chatbot conversations.",
        )
    return await chat_use_case.get_or_create_conversation(student_id=current_user.id)

@router.post("/message", response_model=MessageOut)
async def send_message(
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    if current_user.role != "estudiante":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students can chat with TutorIA.",
        )
    return await chat_use_case.send_chat_message(
        student_id=current_user.id, user_content=message_in.content
    )
