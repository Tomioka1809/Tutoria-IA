"""Regresion: el endpoint de quiz ni derrocha cuota ni disfraza los fallos de Gemini.

``GET /quiz/generate`` llamaba a Gemini en **cada peticion**, para cualquier usuario
autenticado y sin tope alguno: recargar la pantalla en bucle consumia la cuota que
comparte con el chatbot y dejaba al RAG sin servicio.

Ademas atrapaba toda excepcion y devolvia un 500 generico, de modo que "se agoto la
cuota, reintenta en un rato" era indistinguible de "hay un bug en el servidor".
"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from fastapi import status

from app.domain.exceptions import (
    LLMAuthenticationError,
    LLMNetworkError,
    LLMQuotaError,
    LLMTimeoutError,
)
from app.infrastructure.api.v1.endpoints import quiz


class FakeScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class FakeResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return FakeScalars(self._items)


class FakeDb:
    """Devuelve siempre el mismo fragmento de corpus."""

    def __init__(self):
        self.consultas = 0

    async def execute(self, *_args, **_kwargs):
        self.consultas += 1
        chunk = type("Chunk", (), {"text_content": "Texto de reglamento de prueba."})()
        return FakeResult([chunk])


RESPUESTA_VALIDA = (
    '[{"question": "¿P?", "options": ["a","b","c","d","e"], '
    '"correctAnswerIndex": 0, "explanation": "porque si"}]'
)


class BaseQuizTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        quiz._cache["questions"] = None
        quiz._cache["generated_at"] = None

    def tearDown(self):
        quiz._cache["questions"] = None
        quiz._cache["generated_at"] = None


class TestCacheDeCuota(BaseQuizTest):
    async def test_dos_peticiones_seguidas_llaman_a_gemini_una_sola_vez(self):
        db = FakeDb()
        with patch.object(
            quiz, "call_gemini_api", new=AsyncMock(return_value=RESPUESTA_VALIDA)
        ) as llamada, patch.object(quiz.settings, "GEMINI_API_KEY", "clave"):
            primera = await quiz.generate_quiz(db=db, _=None)
            segunda = await quiz.generate_quiz(db=db, _=None)

        self.assertEqual(
            llamada.await_count,
            1,
            "La segunda peticion volvio a gastar cuota en vez de usar la cache.",
        )
        self.assertEqual(primera, segunda)

    async def test_muchas_peticiones_concurrentes_generan_una_sola_vez(self):
        """Sin candado, varias peticiones simultaneas disparan generaciones paralelas."""
        import anyio

        db = FakeDb()
        with patch.object(
            quiz, "call_gemini_api", new=AsyncMock(return_value=RESPUESTA_VALIDA)
        ) as llamada, patch.object(quiz.settings, "GEMINI_API_KEY", "clave"):
            async with anyio.create_task_group() as tg:
                for _ in range(8):
                    tg.start_soon(quiz.generate_quiz, db, None)

        self.assertEqual(llamada.await_count, 1)

    async def test_la_cache_vencida_vuelve_a_generar(self):
        db = FakeDb()
        with patch.object(
            quiz, "call_gemini_api", new=AsyncMock(return_value=RESPUESTA_VALIDA)
        ) as llamada, patch.object(quiz.settings, "GEMINI_API_KEY", "clave"):
            await quiz.generate_quiz(db=db, _=None)

            quiz._cache["generated_at"] = (
                datetime.now(timezone.utc) - quiz.QUIZ_CACHE_TTL - timedelta(seconds=1)
            )
            await quiz.generate_quiz(db=db, _=None)

        self.assertEqual(llamada.await_count, 2)

    def test_el_ttl_es_positivo_y_acotado(self):
        self.assertGreater(quiz.QUIZ_CACHE_TTL, timedelta(0))
        self.assertLessEqual(quiz.QUIZ_CACHE_TTL, timedelta(hours=1))


class TestErroresDeGeminiNoSeDisfrazan(BaseQuizTest):
    async def test_los_errores_del_proveedor_suben_clasificados(self):
        """Antes se atrapaban todos y salian como 500 generico."""
        for error in (
            LLMQuotaError("sin cuota"),
            LLMNetworkError("sin red"),
            LLMTimeoutError("tarde"),
            LLMAuthenticationError("clave mala"),
        ):
            with self.subTest(error=type(error).__name__):
                self.setUp()
                db = FakeDb()
                with patch.object(
                    quiz, "call_gemini_api", new=AsyncMock(side_effect=error)
                ), patch.object(quiz.settings, "GEMINI_API_KEY", "clave"):
                    with self.assertRaises(type(error)):
                        await quiz.generate_quiz(db=db, _=None)

    async def test_un_fallo_no_envenena_la_cache(self):
        db = FakeDb()
        with patch.object(
            quiz, "call_gemini_api", new=AsyncMock(side_effect=LLMQuotaError("sin cuota"))
        ), patch.object(quiz.settings, "GEMINI_API_KEY", "clave"):
            with self.assertRaises(LLMQuotaError):
                await quiz.generate_quiz(db=db, _=None)

        self.assertIsNone(quiz._cache["questions"])

    async def test_sin_clave_configurada_responde_503_y_no_500(self):
        from fastapi import HTTPException

        db = FakeDb()
        with patch.object(quiz.settings, "GEMINI_API_KEY", ""):
            with self.assertRaises(HTTPException) as ctx:
                await quiz.generate_quiz(db=db, _=None)

        self.assertEqual(ctx.exception.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class TestValidacionDeLasPreguntas(unittest.TestCase):
    def test_rechaza_un_indice_de_respuesta_fuera_de_rango(self):
        """El modelo a veces devuelve un indice inexistente; el cliente lo marcaba

        como correcto igual."""
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            quiz.QuizQuestionOut(
                question="¿P?",
                options=["a", "b", "c", "d", "e"],
                correctAnswerIndex=9,
                explanation="x",
            )

    def test_rechaza_una_cantidad_de_opciones_distinta(self):
        from pydantic import ValidationError

        with self.assertRaises(ValidationError):
            quiz.QuizQuestionOut(
                question="¿P?",
                options=["a", "b"],
                correctAnswerIndex=0,
                explanation="x",
            )

    def test_acepta_una_pregunta_bien_formada(self):
        pregunta = quiz.QuizQuestionOut(
            question="¿P?",
            options=["a", "b", "c", "d", "e"],
            correctAnswerIndex=4,
            explanation="x",
        )
        self.assertEqual(pregunta.correctAnswerIndex, 4)


if __name__ == "__main__":
    unittest.main()
