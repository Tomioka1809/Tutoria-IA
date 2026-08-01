from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func
from pydantic import BaseModel
from typing import List
import json

from app.infrastructure.api.dependencies import get_db, get_current_user
from app.infrastructure.database.models.corpus_chunk import CorpusChunk
from app.infrastructure.database.models.user import User
from app.infrastructure.config.config import settings
from app.infrastructure.adapters.quiz_gemini_client import call_gemini_api

import logging
logger = logging.getLogger(__name__)

router = APIRouter()


class QuizQuestionOut(BaseModel):
    question: str
    options: List[str]
    correctAnswerIndex: int
    explanation: str


@router.get("/generate", response_model=List[QuizQuestionOut])
async def generate_quiz(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY no está configurada en el backend.")

    # Fetch 5 random corpus chunks to provide context for the quiz
    result = await db.execute(
        select(CorpusChunk).order_by(func.random()).limit(5)
    )
    chunks = result.scalars().all()
    
    if not chunks:
        # Fallback context if db is empty
        context_text = "La Universidad Nacional de San Antonio Abad del Cusco (UNSAAC) es una universidad pública de Perú, fundada en 1692. Tiene diversas facultades como Ingeniería, Ciencias, Letras, etc. El sistema de evaluación universitaria contempla parciales y finales. La nota aprobatoria mínima es 14."
    else:
        # Limit text length to avoid extremely long prompts
        context_text = "\n\n".join([chunk.text_content[:1500] for chunk in chunks])

    system_instruction = (
        "Eres un generador experto de cuestionarios académicos (quizzes) de opción múltiple para estudiantes universitarios. "
        "Tu objetivo es generar exactamente 10 preguntas basadas EXCLUSIVAMENTE en el texto de contexto proporcionado. "
        "Si el contexto es muy corto, puedes generar preguntas generales relacionadas al entorno universitario. "
        "Cada pregunta debe tener 5 opciones de respuesta, el índice de la respuesta correcta (del 0 al 4), y una breve explicación de por qué es correcta. "
        "REQUISITO ESTRICTO: Tu respuesta debe ser ÚNICAMENTE un arreglo JSON válido, sin formato de markdown (sin ```json) y sin texto adicional. "
        "El formato exacto debe ser:\n"
        "[\n"
        "  {\n"
        "    \"question\": \"¿Pregunta?\",\n"
        "    \"options\": [\"Opción A\", \"Opción B\", \"Opción C\", \"Opción D\", \"Opción E\"],\n"
        "    \"correctAnswerIndex\": 0,\n"
        "    \"explanation\": \"Explicación corta.\"\n"
        "  }\n"
        "]"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Contexto:\n{context_text}\n\nGenera las 10 preguntas en formato JSON estricto."}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json"
        }
    }

    try:
        response_text = await call_gemini_api(settings.GEMINI_API_KEY, payload)
        
        # When responseMimeType is application/json, Gemini returns raw JSON without markdown blocks.
        questions = json.loads(response_text)
        
        # Validate format roughly
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("El JSON no es una lista válida de preguntas.")
            
        return questions
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Gemini response as JSON: %s", response_text)
        raise HTTPException(status_code=500, detail="Error parseando las preguntas generadas.")
    except Exception as e:
        logger.error("Error generating quiz: %s", e)
        raise HTTPException(status_code=500, detail="Error interno al generar el quiz.")
