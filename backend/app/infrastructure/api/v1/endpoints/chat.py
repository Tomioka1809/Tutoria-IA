from fastapi import APIRouter, Depends, HTTPException, status

from app.infrastructure.api.dependencies import get_current_user, get_chat_use_case
from app.domain.entities.chat import ConversationOut, MessageOut, MessageCreate, MessageUpdate
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
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    if current_user.role not in ["estudiante", "tutor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students and tutors can chat with TutorIA.",
        )
    return await chat_use_case.send_chat_message(
        user_id=current_user.id,
        user_role=current_user.role,
        user_content=message_in.content,
    )

@router.patch("/message/{message_id}", response_model=ConversationOut)
async def edit_message(
    message_id: int,
    message_in: MessageUpdate,
    current_user: User = Depends(get_current_user),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    """Reescribe un mensaje propio y vuelve a responderlo.

    Devuelve la conversacion completa y no solo la respuesta nueva: la edicion
    descarta los mensajes posteriores, y el cliente no puede reconstruir cuales
    desaparecieron a partir de un unico mensaje.
    """
    if current_user.role not in ["estudiante", "tutor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only students and tutors can chat with TutorIA.",
        )

    try:
        await chat_use_case.edit_chat_message(
            user_id=current_user.id,
            user_role=current_user.role,
            message_id=message_id,
            new_content=message_in.content,
        )
    except LookupError:
        # Mismo 404 para "no existe" y "es de otra conversacion": distinguirlos
        # confirmaria la existencia de mensajes ajenos.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found in this conversation.",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only your own messages can be edited.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return await chat_use_case.get_or_create_conversation(user_id=current_user.id)

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
