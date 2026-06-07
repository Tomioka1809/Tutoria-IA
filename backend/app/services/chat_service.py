import json
import urllib.request
import urllib.error
import anyio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import List
from datetime import datetime

from app.models.conversation import Conversation
from app.models.message import Message
from app.core.config import settings

def call_gemini_sync(api_key: str, payload: dict) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return "🦖 ¡Hola! Tuve un inconveniente al procesar tu respuesta en mi cerebro de dinosaurio. ¿Podrías repetirlo?"
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        print(f"Gemini API Error: {error_msg}")
        return "🦖 ¡Grrr! Parece que no pude comunicarme con los servidores de Google Gemini. Verifica tu API Key."
    except Exception as e:
        print(f"Gemini API Exception: {e}")
        return "🦖 ¡Ups! Ocurrió un error al intentar conectarme con mi red de conocimiento."

async def call_gemini_api(api_key: str, payload: dict) -> str:
    return await anyio.to_thread.run_sync(call_gemini_sync, api_key, payload)

async def get_or_create_conversation(db: AsyncSession, student_id: int) -> Conversation:
    # Fetch active conversation for student
    result = await db.execute(
        select(Conversation)
        .where(Conversation.student_id == student_id)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.created_at.desc())
    )
    conversation = result.scalars().first()
    if not conversation:
        conversation = Conversation(student_id=student_id)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        # Initialize with a welcome message from TutorIA
        welcome = Message(
            conversation_id=conversation.id,
            role="assistant",
            content="¡Hola! Soy TutorIA 🦖, tu tutor y consejero académico en forma de dinosaurio morado. Estoy aquí para guiarte en tus cursos, técnicas de estudio o reglamentos universitarios. ¿En qué te puedo ayudar hoy?",
        )
        db.add(welcome)
        await db.commit()
        # Reload conversation with messages
        result = await db.execute(
            select(Conversation)
            .where(Conversation.id == conversation.id)
            .options(selectinload(Conversation.messages))
        )
        conversation = result.scalars().first()
        
    return conversation

async def send_chat_message(
    db: AsyncSession, student_id: int, user_content: str
) -> Message:
    conversation = await get_or_create_conversation(db, student_id)
    
    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=user_content,
    )
    db.add(user_msg)
    await db.commit()
    
    # Check if Gemini API key is configured
    if not settings.GEMINI_API_KEY:
        assistant_content = (
            "¡Hola! Soy TutorIA 🦖. Mi cerebro de Inteligencia Artificial requiere que configures "
            "la variable `GEMINI_API_KEY` en el archivo `.env` del backend. Por ahora, "
            "estoy en modo de simulación y te sugiero consultar tus planes de estudios directamente en el calendario."
        )
    else:
        # Build prompt and conversation history
        history_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.sent_at.asc())
        )
        history_messages = history_result.scalars().all()
        
        # Prepare content turns for Gemini API
        contents = []
        for msg in history_messages:
            role_map = "user" if msg.role == "user" else "model"
            contents.append({
                "role": role_map,
                "parts": [{"text": msg.content}]
            })
            
        system_instruction = (
            "Eres TutorIA, el tutor académico inteligente de la universidad. Te presentas como un amigable dinosaurio morado. "
            "Tu objetivo es ayudar a los estudiantes con sus consultas académicas, planes de estudio, reglamentos universitarios y técnicas de estudio. "
            "Mantén siempre un tono entusiasta, paciente, motivador, alegre y amigable. Utiliza emojis ocasionalmente para ser más cercano (🦖, 📚, ✍️, ✨). "
            "Si te preguntan algo fuera del ámbito académico o universitario, recuérdales amablemente que tu especialidad es el éxito estudiantil y los temas de la universidad."
        )
        
        payload = {
            "contents": contents,
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            }
        }
        
        # Call Gemini API
        assistant_content = await call_gemini_api(settings.GEMINI_API_KEY, payload)
        
    # Save assistant message
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant_content,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    return assistant_msg
