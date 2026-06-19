from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.application.ports.repository_ports import ChatRepositoryPort
from app.infrastructure.database.models.conversation import Conversation
from app.infrastructure.database.models.message import Message

class ChatRepository(ChatRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_conversation(self, student_id: int) -> Conversation:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.student_id == student_id)
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.created_at.desc())
        )
        conversation = result.scalars().first()
        if not conversation:
            conversation = Conversation(student_id=student_id)
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)
            
            # Initialize with welcome message
            welcome = Message(
                conversation_id=conversation.id,
                role="assistant",
                content="¡Hola! Soy TutorIA 🦖, tu tutor y consejero académico en forma de dinosaurio morado. Estoy aquí para guiarte en tus cursos, técnicas de estudio o reglamentos universitarios. ¿En qué te puedo ayudar hoy?",
            )
            self.db.add(welcome)
            await self.db.commit()
            
            result = await self.db.execute(
                select(Conversation)
                .where(Conversation.id == conversation.id)
                .options(selectinload(Conversation.messages))
            )
            conversation = result.scalars().first()
        return conversation

    async def save_message(self, conversation_id: int, role: str, content: str) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_history(self, conversation_id: int) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sent_at.asc())
        )
        return list(result.scalars().all())
