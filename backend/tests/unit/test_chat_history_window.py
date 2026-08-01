"""Regresion: el historial enviado al LLM esta acotado a una ventana fija.

Origen: ChatRepository.get_history emitia un SELECT sin LIMIT y send_chat_message
reenviaba la conversacion completa a Gemini en cada turno, de modo que el costo y la
latencia por mensaje crecian sin techo a lo largo de una conversacion.
"""

import unittest

import app.infrastructure.database.base  # noqa: F401  - registra los mappers ORM
from app.application.use_cases.chat_use_cases import (
    HISTORY_WINDOW_MESSAGES,
    ChatUseCase,
)
from app.application.dtos.rag_dtos import RAGRetrievalPolicy, RetrievedChunkDTO
from app.application.ports.llm_port import LLMPort
from app.application.ports.repository_ports import ChatRepositoryPort
from app.infrastructure.database.repositories.chat_repository import ChatRepository


class FakeConversation:
    def __init__(self, id: int = 1):
        self.id = id


class FakeMessage:
    def __init__(self, id: int, role: str, content: str):
        self.id = id
        self.role = role
        self.content = content


class RecordingChatRepository(ChatRepositoryPort):
    """Guarda el limit recibido y aplica la ventana como lo haria la base de datos."""

    def __init__(self, preexisting: int = 0):
        self.conv = FakeConversation()
        self.messages = [
            FakeMessage(i + 1, "user" if i % 2 == 0 else "assistant", f"mensaje {i}")
            for i in range(preexisting)
        ]
        self.limits_received = []

    async def get_or_create_conversation(self, user_id: int):
        return self.conv

    async def reset_conversation(self, user_id: int):
        self.messages.clear()

    async def save_message(self, conversation_id: int, role: str, content: str):
        msg = FakeMessage(len(self.messages) + 1, role, content)
        self.messages.append(msg)
        return msg

    async def get_history(self, conversation_id: int, limit: int | None = None):
        self.limits_received.append(limit)
        return self.messages[-limit:] if limit else self.messages


class CapturingLLM(LLMPort):
    def __init__(self):
        self.last_history = None

    async def generate_response(self, system_instruction, history, user_message, tools=None):
        self.last_history = history
        return "respuesta"

    async def compute_embedding(self, text: str):
        return [0.1] * 768


class StubCorpusRepository:
    async def search_similar(self, embedding, *, limit, query_text,
                             max_cosine_distance, keyword_fallback_limit):
        return [RetrievedChunkDTO(
            text="Art. 1 - La tutoria es un servicio obligatorio.",
            source="reglamento_tutoria.json",
            cosine_distance=0.1, retrieval_method="vector",
        )]


class EmptyRelationRepository:
    async def get_assigned_tutors_data(self, user_id): return []
    async def get_assigned_students_data(self, user_id): return []
    async def get_calendar_events_data(self, **kwargs): return {"sessions": [], "events": []}


class TestHistoryWindowInUseCase(unittest.IsolatedAsyncioTestCase):
    async def _send(self, preexisting):
        repo = RecordingChatRepository(preexisting=preexisting)
        llm = CapturingLLM()
        use_case = ChatUseCase(
            chat_repo=repo, corpus_repo=StubCorpusRepository(), llm=llm,
            tutor_assignment_repo=EmptyRelationRepository(),
            calendar_repo=EmptyRelationRepository(),
            rag_policy=RAGRetrievalPolicy(),
        )
        await use_case.send_chat_message(
            user_id=1, user_role="estudiante",
            user_content="que dice el reglamento de tutoria",
        )
        return repo, llm

    async def test_history_is_requested_with_the_configured_window(self):
        repo, _ = await self._send(preexisting=0)
        self.assertEqual(repo.limits_received, [HISTORY_WINDOW_MESSAGES])
        self.assertIsNotNone(
            repo.limits_received[0],
            "get_history sin limit vuelve a traer la conversacion completa",
        )

    async def test_long_conversation_does_not_grow_the_llm_payload(self):
        _, llm = await self._send(preexisting=500)
        self.assertLessEqual(len(llm.last_history), HISTORY_WINDOW_MESSAGES)

    async def test_window_is_bounded_regardless_of_conversation_length(self):
        _, short = await self._send(preexisting=4)
        _, long = await self._send(preexisting=400)
        self.assertLessEqual(len(long.last_history), HISTORY_WINDOW_MESSAGES)
        self.assertGreaterEqual(len(long.last_history), len(short.last_history))

    def test_window_covers_the_heuristics_lookback(self):
        """Las heuristicas de malla y seguimiento consultan history_msgs[-6:]."""
        self.assertGreaterEqual(HISTORY_WINDOW_MESSAGES, 6)


class CapturingSession:
    """Sesion falsa que retiene la sentencia compilada y devuelve filas fijas."""

    def __init__(self, rows):
        self.rows = rows
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        session = self

        class Result:
            def scalars(self_inner): return self_inner
            def all(self_inner): return list(session.rows)

        return Result()


class TestHistoryWindowInRepository(unittest.IsolatedAsyncioTestCase):
    async def test_limit_emits_a_bounded_query(self):
        session = CapturingSession(rows=[])
        repo = ChatRepository(session)

        await repo.get_history(conversation_id=1, limit=20)

        sql = str(session.statements[0])
        self.assertIn("LIMIT", sql.upper())
        self.assertIn("DESC", sql.upper(), "los ultimos N se obtienen ordenando descendente")

    async def test_without_limit_query_stays_unbounded(self):
        session = CapturingSession(rows=[])
        repo = ChatRepository(session)

        await repo.get_history(conversation_id=1)

        self.assertNotIn("LIMIT", str(session.statements[0]).upper())

    async def test_windowed_result_is_returned_in_chronological_order(self):
        newest_first = [FakeMessage(3, "user", "c"), FakeMessage(2, "assistant", "b"),
                        FakeMessage(1, "user", "a")]
        repo = ChatRepository(CapturingSession(rows=newest_first))

        history = await repo.get_history(conversation_id=1, limit=3)

        self.assertEqual([m.content for m in history], ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
