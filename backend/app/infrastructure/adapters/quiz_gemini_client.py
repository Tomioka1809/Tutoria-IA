import json
import logging
import urllib.error
import urllib.request
from typing import Dict, Mapping

import anyio

from app.domain.exceptions import LLMServiceError

logger = logging.getLogger(__name__)

MODELO_QUIZ = "gemini-3.5-flash-lite"
GEMINI_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO_QUIZ}:generateContent"
)
TIMEOUT_SEGUNDOS = 55


def _clasificar(status: int | None, detalle: str) -> LLMServiceError:
    """Traduce el fallo de Gemini al error de dominio que le corresponde.

    Se importa perezosamente para no arrastrar el adaptador principal (y con el, el
    SDK de google-genai) dentro de este cliente, que usa urllib a proposito.
    """
    from app.infrastructure.adapters.gemini_adapter import _classify_gemini_error

    _, error = _classify_gemini_error(Exception(f"{status} {detalle}"))
    return error


def call_gemini_sync(api_key: str, payload: Mapping[str, object]) -> str:
    req = urllib.request.Request(
        GEMINI_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            # La clave va en cabecera y no en la query string: las URL quedan en los
            # logs de proxies e intermediarios, las cabeceras no.
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEGUNDOS) as response:
            res_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", errors="replace")[:200]
        logger.error("Gemini respondio %s en el quiz: %s", e.code, detalle)
        raise _clasificar(e.code, detalle) from e
    except urllib.error.URLError as e:
        logger.error("Fallo de red hablando con Gemini en el quiz: %s", e.reason)
        raise _clasificar(None, f"connection error: {e.reason}") from e
    except (TimeoutError, json.JSONDecodeError) as e:
        logger.error("Respuesta ilegible de Gemini en el quiz: %s", e)
        raise _clasificar(None, str(e)) from e

    # Antes cualquier fallo devolvia "{}" y el endpoint lo convertia en un 500
    # generico: la cuota agotada era indistinguible de un bug. Ahora el error viaja
    # clasificado hasta el manejador, que le pone el codigo HTTP correcto.
    candidates = res_data.get("candidates", [])
    if not candidates:
        motivo = res_data.get("promptFeedback", {}).get("blockReason")
        raise LLMServiceError(
            f"Gemini no devolvió candidatos para el quiz (motivo: {motivo or 'desconocido'})"
        )

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise LLMServiceError("Gemini devolvió un candidato sin contenido para el quiz")

    texto = parts[0].get("text", "")
    if not texto:
        raise LLMServiceError("Gemini devolvió un texto vacío para el quiz")
    return texto


async def call_gemini_api(api_key: str, payload: Dict[str, object]) -> str:
    return await anyio.to_thread.run_sync(call_gemini_sync, api_key, payload)
