import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List

import anyio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import func

from app.domain.exceptions import LLMServiceError
from app.infrastructure.adapters.quiz_gemini_client import call_gemini_api
from app.infrastructure.api.dependencies import get_db, get_current_user
from app.infrastructure.config.config import settings
from app.infrastructure.database.models.corpus_chunk import CorpusChunk
from app.infrastructure.database.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Cuanto vive un cuestionario generado antes de pedirle otro a Gemini.
#
# El endpoint llamaba a Gemini en cada peticion, para cualquier usuario autenticado
# y sin tope: bastaba con recargar la pantalla para consumir la cuota compartida con
# el chatbot, y dejar sin servicio al RAG. Con la cache el gasto queda acotado a unas
# pocas llamadas por hora sin importar cuantos estudiantes la abran.
#
# El costo es que dentro de la ventana todos ven el mismo cuestionario. Para un quiz
# de repaso generado sobre fragmentos al azar del corpus es un intercambio razonable;
# si molesta, bajar el TTL sube el gasto de forma proporcional y predecible.
QUIZ_CACHE_TTL = timedelta(minutes=10)

NUM_PREGUNTAS = 10
NUM_OPCIONES = 5
CHUNKS_DE_CONTEXTO = 5
MAX_CARACTERES_POR_CHUNK = 1500

# Cache en memoria del proceso. A diferencia de los codigos de recuperacion, que
# necesitaban una tabla, aca degradar con varios workers es inocuo: el peor caso es
# una generacion por worker en vez de una global, no una falla de correccion.
_cache: dict = {"questions": None, "generated_at": None}
_cache_lock = anyio.Lock()


class QuizQuestionOut(BaseModel):
    question: str
    options: List[str] = Field(..., min_length=NUM_OPCIONES, max_length=NUM_OPCIONES)
    correctAnswerIndex: int
    explanation: str

    @field_validator("correctAnswerIndex")
    @classmethod
    def indice_dentro_de_rango(cls, v: int) -> int:
        # El modelo a veces devuelve un indice fuera de rango. Sin esta comprobacion
        # el cliente marca como correcta una opcion que no existe.
        if not 0 <= v < NUM_OPCIONES:
            raise ValueError(f"correctAnswerIndex debe estar entre 0 y {NUM_OPCIONES - 1}")
        return v


SYSTEM_INSTRUCTION = (
    "Eres un generador experto de cuestionarios académicos (quizzes) de opción múltiple para estudiantes universitarios. "
    f"Tu objetivo es generar exactamente {NUM_PREGUNTAS} preguntas basadas EXCLUSIVAMENTE en el texto de contexto proporcionado. "
    "Si el contexto es muy corto, puedes generar preguntas generales relacionadas al entorno universitario. "
    f"Cada pregunta debe tener {NUM_OPCIONES} opciones de respuesta, el índice de la respuesta correcta (del 0 al {NUM_OPCIONES - 1}), y una breve explicación de por qué es correcta. "
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

CONTEXTO_DE_RESPALDO = (
    "La Universidad Nacional de San Antonio Abad del Cusco (UNSAAC) es una universidad pública de Perú, "
    "fundada en 1692. Tiene diversas facultades como Ingeniería, Ciencias, Letras, etc. El sistema de "
    "evaluación universitaria contempla parciales y finales. La nota aprobatoria mínima es 14."
)


def _cache_vigente() -> bool:
    generado = _cache["generated_at"]
    if generado is None or _cache["questions"] is None:
        return False
    return datetime.now(timezone.utc) - generado < QUIZ_CACHE_TTL


async def _construir_contexto(db: AsyncSession) -> str:
    result = await db.execute(select(CorpusChunk).order_by(func.random()).limit(CHUNKS_DE_CONTEXTO))
    chunks = result.scalars().all()
    if not chunks:
        return CONTEXTO_DE_RESPALDO
    return "\n\n".join(chunk.text_content[:MAX_CARACTERES_POR_CHUNK] for chunk in chunks)


async def _generar_cuestionario(db: AsyncSession) -> List[dict]:
    contexto = await _construir_contexto(db)
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"Contexto:\n{contexto}\n\n"
                        f"Genera las {NUM_PREGUNTAS} preguntas en formato JSON estricto."
                    }
                ],
            }
        ],
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"},
    }

    # Los errores del cliente (cuota, red, timeout) suben clasificados hasta el
    # manejador, que les pone el codigo HTTP que corresponde. Antes se atrapaba todo
    # y se devolvia un 500 generico que no distinguia un bug de la cuota agotada.
    respuesta = await call_gemini_api(settings.GEMINI_API_KEY, payload)

    try:
        preguntas = json.loads(respuesta)
    except json.JSONDecodeError as e:
        logger.error("Gemini devolvió un JSON inválido para el quiz: %s", respuesta[:200])
        raise LLMServiceError("El servicio de IA devolvió un cuestionario ilegible.") from e

    if not isinstance(preguntas, list) or not preguntas:
        raise LLMServiceError("El servicio de IA no devolvió ninguna pregunta.")

    return preguntas


@router.get("/generate", response_model=List[QuizQuestionOut])
async def generate_quiz(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503, detail="El servicio de cuestionarios no está configurado."
        )

    if _cache_vigente():
        return _cache["questions"]

    # El candado evita que varias peticiones simultaneas disparen generaciones
    # paralelas al encontrar la cache vencida a la vez.
    async with _cache_lock:
        if _cache_vigente():
            return _cache["questions"]

        preguntas = await _generar_cuestionario(db)
        _cache["questions"] = preguntas
        _cache["generated_at"] = datetime.now(timezone.utc)
        return preguntas
