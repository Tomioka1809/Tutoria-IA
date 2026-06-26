from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.api.dependencies import get_current_user, get_chat_use_case, get_db
from app.domain.entities.chat import ConversationOut, MessageOut, MessageCreate
from app.infrastructure.database.models.user import User
from app.application.use_cases.chat_use_cases import ChatUseCase

router = APIRouter()

@router.get("/conversation", response_model=ConversationOut)
async def read_conversation(
    current_user: User = Depends(get_current_user),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    if current_user.role not in ["estudiante", "tutor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students and tutors can access TutorIA chatbot conversations.",
        )
    return await chat_use_case.get_or_create_conversation(user_id=current_user.id)

@router.post("/message", response_model=MessageOut)
async def send_message(
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["estudiante", "tutor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students and tutors can chat with TutorIA.",
        )
    return await chat_use_case.send_chat_message(
        user=current_user, user_content=message_in.content, db=db
    )

@router.delete("/conversation", response_model=dict)
async def reset_conversation(
    current_user: User = Depends(get_current_user),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    if current_user.role not in ["estudiante", "tutor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students and tutors can access TutorIA chatbot conversations.",
        )
    await chat_use_case.reset_conversation(user_id=current_user.id)
    return {"status": "success", "message": "Conversation reset."}
