import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import json
from datetime import datetime

from app.application.use_cases.chat_use_cases import (
    ChatUseCase,
    classify_intent,
    reconstruct_query,
    is_ambiguous_tutoria_general_followup,
    check_malla_ambiguity,
    extract_malla_state,
    decompose_multi_topic_query,
)
from app.infrastructure.adapters.gemini_adapter import (
    GeminiAdapter,
    _classify_gemini_error,
)
from app.domain.exceptions import (
    LLMAuthenticationError,
    LLMQuotaError,
    LLMTimeoutError,
    LLMNetworkError,
    LLMServiceError,
)
from app.application.ports.repository_ports import (
    ChatRepositoryPort,
    CorpusRepositoryPort,
    TutorAssignmentRepositoryPort,
    CalendarRepositoryPort,
)
from app.application.ports.llm_port import LLMPort
from app.application.dtos.rag_dtos import RetrievedChunkDTO, RAGRetrievalPolicy


class FakeConversation:
    def __init__(self, id: int = 1):
        self.id = id


class FakeMessage:
    def __init__(self, id: int, role: str, content: str, conversation_id: int = 1):
        self.id = id
        self.role = role
        self.content = content
        self.conversation_id = conversation_id


class FakeChatRepository(ChatRepositoryPort):
    def __init__(self, conv_id: int = 1):
        self.messages = []
        self.conv = FakeConversation(id=conv_id)
        self._siguiente_id = 1

    async def get_or_create_conversation(self, user_id: int):
        return self.conv

    async def reset_conversation(self, user_id: int):
        self.messages.clear()

    async def save_message(self, conversation_id: int, role: str, content: str):
        msg = FakeMessage(
            id=self._siguiente_id, role=role, content=content, conversation_id=conversation_id
        )
        self._siguiente_id += 1
        self.messages.append(msg)
        return msg

    async def get_history(self, conversation_id: int, limit: int | None = None):
        return self.messages[-limit:] if limit else self.messages

    async def get_message(self, message_id: int):
        return next((m for m in self.messages if m.id == message_id), None)

    async def edit_message_and_truncate(self, message_id: int, content: str):
        msg = await self.get_message(message_id)
        if msg is None:
            raise ValueError(f"No existe el mensaje {message_id}")
        # El id no se reutiliza tras truncar: replica el comportamiento de una
        # secuencia de base de datos, para que la prueba no dependa de que los
        # ids se reciclen.
        self.messages = [m for m in self.messages if m.id <= message_id]
        msg.content = content
        return msg


class TrackingLLM(LLMPort):
    def __init__(self, response_text="Respuesta de prueba."):
        self.response_text = response_text
        self.compute_embedding_calls = 0
        self.generate_response_calls = 0
        self.last_system_instruction = ""
        self.last_user_message = ""

    async def generate_response(self, system_instruction: str, history: list, user_message: str, tools: list = None):
        self.generate_response_calls += 1
        self.last_system_instruction = system_instruction
        self.last_user_message = user_message
        return self.response_text

    async def compute_embedding(self, text: str):
        self.compute_embedding_calls += 1
        return [0.1] * 768


class TrackingCorpusRepository(CorpusRepositoryPort):
    def __init__(self, chunks=None):
        self.search_similar_calls = 0
        self.chunks = chunks if chunks is not None else [
            RetrievedChunkDTO(
                text="Art. 1 - La tutoría es un servicio obligatorio.",
                source="reglamento_tutoria.json",
                cosine_distance=0.1,
                retrieval_method="vector"
            )
        ]

    async def search_similar(
        self,
        query_embedding: list,
        *,
        limit: int,
        query_text: str | None,
        max_cosine_distance: float,
        keyword_fallback_limit: int,
        **_politica_hibrida,
    ):
        self.search_similar_calls += 1
        return self.chunks

    async def insert_chunk(self, text: str, embedding: list):
        pass


class TrackingTutorRepository(TutorAssignmentRepositoryPort):
    def __init__(self):
        self.calls = 0

    async def get_assigned_tutors_data(self, student_id: int):
        self.calls += 1
        return [{"tutor_name": "Ing. Nila Acurio Usca", "email": "acuriousca@unsaac.edu.pe", "office": "Cubículo 4", "specialty": "Tutoría Académica"}]

    async def get_assigned_students_data(self, tutor_id: int):
        self.calls += 1
        return [{"student_name": "Maria Lopez", "student_code": "182930", "email": "maria@unsaac.edu.pe"}]

    async def get_assigned_student_ids(self, tutor_id: int):
        return []


class TrackingCalendarRepository(CalendarRepositoryPort):
    def __init__(self):
        self.calls = 0

    async def get_calendar_events_data(self, user_id: int, role: str, start_dt: datetime, end_dt: datetime):
        self.calls += 1
        return {"sessions": [], "events": []}


class TestF1AChatRAG(unittest.IsolatedAsyncioTestCase):

    # 1. Malla -> 2017 -> "De 8vo semestre?"
    async def test_01_malla_2017_8vo_semestre_retains_plan_no_abstention(self):
        chat_repo = FakeChatRepository()
        corpus_repo = TrackingCorpusRepository(chunks=[
            RetrievedChunkDTO(text="Malla Curricular Plan 2017 octavo semestre", source="malla_curricular_2017.json", cosine_distance=0.1, retrieval_method="vector"),
        ])
        llm = TrackingLLM(response_text="Cursos del 8vo semestre Plan 2017.")
        use_case = ChatUseCase(
            chat_repo=chat_repo, corpus_repo=corpus_repo, llm=llm,
            tutor_assignment_repo=TrackingTutorRepository(), calendar_repo=TrackingCalendarRepository(), rag_policy=RAGRetrievalPolicy(),
        )

        await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="Dame información de mi malla curricular")
        await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="2017")
        msg = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="De 8vo semestre?")

        self.assertEqual(msg.content, "Cursos del 8vo semestre Plan 2017.")
        self.assertIn("2017", llm.last_system_instruction)


    # 2. Malla -> 2017 -> "De 8vo ciclo?"
    async def test_02_malla_2017_8vo_ciclo_retains_plan(self):
        chat_repo = FakeChatRepository()
        corpus_repo = TrackingCorpusRepository(chunks=[
            RetrievedChunkDTO(text="Malla Curricular Plan 2017 octavo semestre", source="malla_curricular_2017.json", cosine_distance=0.1, retrieval_method="vector"),
        ])
        llm = TrackingLLM(response_text="Cursos del 8vo ciclo Plan 2017.")
        use_case = ChatUseCase(
            chat_repo=chat_repo, corpus_repo=corpus_repo, llm=llm,
            tutor_assignment_repo=TrackingTutorRepository(), calendar_repo=TrackingCalendarRepository(), rag_policy=RAGRetrievalPolicy(),
        )

        await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="Dame información de mi malla curricular")
        await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="2017")
        msg = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="De 8vo ciclo?")

        self.assertEqual(msg.content, "Cursos del 8vo ciclo Plan 2017.")

    # 3. Malla -> 2025 -> "Octavo semestre"
    async def test_03_malla_2025_octavo_semestre_retains_plan_2025(self):
        chat_repo = FakeChatRepository()
        corpus_repo = TrackingCorpusRepository(chunks=[
            RetrievedChunkDTO(text="Malla Curricular Plan 2025 octavo semestre", source="malla_curricular_2025.json", cosine_distance=0.1, retrieval_method="vector"),
        ])
        llm = TrackingLLM(response_text="Cursos del 8vo semestre Plan 2025.")
        use_case = ChatUseCase(
            chat_repo=chat_repo, corpus_repo=corpus_repo, llm=llm,
            tutor_assignment_repo=TrackingTutorRepository(), calendar_repo=TrackingCalendarRepository(), rag_policy=RAGRetrievalPolicy(),
        )

        await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="Dame información de mi malla curricular")
        await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="2025")
        msg = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="Octavo semestre")

        self.assertEqual(msg.content, "Cursos del 8vo semestre Plan 2025.")

    # 4. Malla -> 2017 -> nueva solicitud completa de malla -> reinicia el flujo
    async def test_04_new_malla_request_resets_flow(self):
        chat_repo = FakeChatRepository()
        corpus_repo = TrackingCorpusRepository(chunks=[
            RetrievedChunkDTO(text="Malla Plan 2017", source="malla_curricular_2017.json", cosine_distance=0.1, retrieval_method="vector"),
            RetrievedChunkDTO(text="Malla Plan 2025", source="malla_curricular_2025.json", cosine_distance=0.1, retrieval_method="vector"),
        ])
        llm = TrackingLLM(response_text="Plan 2017.")
        use_case = ChatUseCase(
            chat_repo=chat_repo, corpus_repo=corpus_repo, llm=llm,
            tutor_assignment_repo=TrackingTutorRepository(), calendar_repo=TrackingCalendarRepository(), rag_policy=RAGRetrievalPolicy(),
        )

        await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="Dame información de mi malla curricular")
        await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="2017")

        # New standalone request
        msg_reset = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="Dame información de mi malla curricular")
        self.assertIn("Encontré los planes de estudios 2017 y 2025. ¿A cuál pertenece tu malla curricular?", msg_reset.content)

    # 5. PERSONAL_CALENDAR después de consultar al tutor
    async def test_05_personal_calendar_after_tutor_query_has_no_tutor_data(self):
        chat_repo = FakeChatRepository()
        tutor_repo = TrackingTutorRepository()
        calendar_repo = TrackingCalendarRepository()
        corpus_repo = TrackingCorpusRepository()
        llm = TrackingLLM()

        use_case = ChatUseCase(
            chat_repo=chat_repo, corpus_repo=corpus_repo, llm=llm,
            tutor_assignment_repo=tutor_repo, calendar_repo=calendar_repo, rag_policy=RAGRetrievalPolicy(),
        )

        # Query 1: Tutor
        msg1 = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="¿Quién es mi tutor?")
        self.assertIn("Nila Acurio Usca", msg1.content)

        # Query 2: Calendar
        msg2 = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="¿Cuándo es mi próxima tutoría?")
        self.assertNotIn("acuriousca@unsaac.edu.pe", msg2.content)
        self.assertNotIn("Nila Acurio Usca", msg2.content)
        self.assertIn("No tienes tutorías ni eventos programados", msg2.content)

    # 6. PERSONAL_TUTOR no consulta calendario
    async def test_06_personal_tutor_does_not_query_calendar(self):
        chat_repo = FakeChatRepository()
        tutor_repo = TrackingTutorRepository()
        calendar_repo = TrackingCalendarRepository()
        corpus_repo = TrackingCorpusRepository()
        llm = TrackingLLM()

        use_case = ChatUseCase(
            chat_repo=chat_repo, corpus_repo=corpus_repo, llm=llm,
            tutor_assignment_repo=tutor_repo, calendar_repo=calendar_repo, rag_policy=RAGRetrievalPolicy(),
        )

        await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="¿Quién es mi tutor?")
        self.assertEqual(calendar_repo.calls, 0)
        self.assertEqual(tutor_repo.calls, 1)

    # 7. Reglamentos de tutoría e intercambio obtiene evidencia por tema
    async def test_07_multi_topic_retrieval_subtopics(self):
        chat_repo = FakeChatRepository()
        corpus_repo = TrackingCorpusRepository(chunks=[
            RetrievedChunkDTO(text="Reglamento de tutoría", source="reglamento_tutoria.json", cosine_distance=0.1, retrieval_method="vector"),
            RetrievedChunkDTO(text="Reglamento de intercambio estudiantil", source="reglamento_intercambio_estudiantil.json", cosine_distance=0.1, retrieval_method="vector"),
        ])
        llm = TrackingLLM(response_text="Información de tutoría e intercambio.")

        use_case = ChatUseCase(
            chat_repo=chat_repo, corpus_repo=corpus_repo, llm=llm,
            tutor_assignment_repo=TrackingTutorRepository(), calendar_repo=TrackingCalendarRepository(), rag_policy=RAGRetrievalPolicy(),
        )

        await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="¿Cuáles son los reglamentos de tutoría y de intercambio estudiantil?")
        self.assertGreaterEqual(corpus_repo.search_similar_calls, 2)

    # 8. Solo existe evidencia de intercambio -> responde intercambio e indica falta tutoría
    async def test_08_multi_topic_partial_evidence(self):
        chat_repo = FakeChatRepository()
        corpus_repo = TrackingCorpusRepository(chunks=[
            RetrievedChunkDTO(text="Oficina de Cooperación y Relaciones Internacionales OCRI intercambio estudiantil", source="reglamento_intercambio.json", cosine_distance=0.1, retrieval_method="vector"),
        ])
        llm = TrackingLLM(response_text="Información de intercambio. No se cuenta con información de tutoría.")

        use_case = ChatUseCase(
            chat_repo=chat_repo, corpus_repo=corpus_repo, llm=llm,
            tutor_assignment_repo=TrackingTutorRepository(), calendar_repo=TrackingCalendarRepository(), rag_policy=RAGRetrievalPolicy(),
        )

        msg = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="¿Cuáles son los reglamentos de tutoría y de intercambio estudiantil?")
        self.assertEqual(msg.content, "Información de intercambio. No se cuenta con información de tutoría.")

    # 9. Aisleamiento entre usuarios y conversaciones
    async def test_09_user_isolation(self):
        chat_repo_a = FakeChatRepository(conv_id=1)
        chat_repo_b = FakeChatRepository(conv_id=2)
        corpus_repo = TrackingCorpusRepository()
        llm = TrackingLLM()

        use_case_a = ChatUseCase(
            chat_repo=chat_repo_a, corpus_repo=corpus_repo, llm=llm,
            tutor_assignment_repo=TrackingTutorRepository(), calendar_repo=TrackingCalendarRepository(), rag_policy=RAGRetrievalPolicy(),
        )
        use_case_b = ChatUseCase(
            chat_repo=chat_repo_b, corpus_repo=corpus_repo, llm=llm,
            tutor_assignment_repo=TrackingTutorRepository(), calendar_repo=TrackingCalendarRepository(), rag_policy=RAGRetrievalPolicy(),
        )

        await use_case_a.send_chat_message(user_id=1, user_role="estudiante", user_content="Dame información de mi malla curricular")
        msg_b = await use_case_b.send_chat_message(user_id=2, user_role="estudiante", user_content="¿Quién es mi tutor?")
        self.assertIn("Nila Acurio Usca", msg_b.content)

    # 10. No regresión de UNKNOWN y "Y tutoría general?"
    async def test_10_non_regression_unknown_and_followup(self):
        chat_repo = FakeChatRepository()
        corpus_repo = TrackingCorpusRepository()
        llm = TrackingLLM()

        use_case = ChatUseCase(
            chat_repo=chat_repo, corpus_repo=corpus_repo, llm=llm,
            tutor_assignment_repo=TrackingTutorRepository(), calendar_repo=TrackingCalendarRepository(), rag_policy=RAGRetrievalPolicy(),
        )

        # UNKNOWN
        msg_unk = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="Hola")
        self.assertEqual(msg_unk.content, "Respuesta de prueba.")

        # Ambiguous follow-up
        await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="¿Cuándo es mi próxima tutoría?")
        msg_fol = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="Y tutoría general?")
        self.assertIn("¿Te refieres a la definición de tutoría general, al reglamento, al cronograma", msg_fol.content)

    # 11. Verificación de jerarquía de excepciones y compatibilidad con RuntimeError
    def test_11_llm_exceptions_are_runtime_error_subclasses(self):
        self.assertTrue(issubclass(LLMAuthenticationError, RuntimeError))
        self.assertTrue(issubclass(LLMQuotaError, RuntimeError))
        self.assertTrue(issubclass(LLMTimeoutError, RuntimeError))
        self.assertTrue(issubclass(LLMNetworkError, RuntimeError))

    # 12. Strict mode without API key raises LLMAuthenticationError (also satisfies RuntimeError)
    async def test_12_strict_mode_without_key_raises(self):
        adapter = GeminiAdapter(api_key="", allow_generation_fallback=False)
        with self.assertRaises(LLMAuthenticationError):
            await adapter.generate_response("sys", [], "user")

        with self.assertRaises(RuntimeError):
            await adapter.generate_response("sys", [], "user")

    # 13. RuntimeError in generate_response propagates and does not duplicate save_message
    async def test_13_runtime_error_propagates_no_duplicate_save(self):
        chat_repo = FakeChatRepository()
        llm = TrackingLLM()

        async def failing_generate(*args, **kwargs):
            raise RuntimeError("503 Gemini Error")

        llm.generate_response = failing_generate

        use_case = ChatUseCase(
            chat_repo=chat_repo, corpus_repo=TrackingCorpusRepository(), llm=llm,
            tutor_assignment_repo=TrackingTutorRepository(), calendar_repo=TrackingCalendarRepository(), rag_policy=RAGRetrievalPolicy(),
        )

        with self.assertRaises(RuntimeError):
            await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="Hola")

        msgs = await chat_repo.get_history(1)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].role, "user")


if __name__ == "__main__":
    unittest.main()
