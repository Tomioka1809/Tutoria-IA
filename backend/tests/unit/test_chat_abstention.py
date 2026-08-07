"""Regresion: la abstencion documental se aplica en codigo, no solo en el prompt.

Origen: send_chat_message se saltaba la recuperacion cuando el intent era UNKNOWN pero
igual invocaba al LLM con corpus vacio, de modo que una consulta fuera de dominio se
respondia desde el conocimiento propio del modelo (incidentes F5D-002). La regla de
abstencion vivia unicamente dentro del system_instruction y el modelo podia ignorarla.

Contrato verificado aqui:
  - SOCIAL (saludos)          -> responde el LLM, sin consultar el corpus.
  - Consulta sin evidencia    -> abstencion determinista, sin invocar al LLM.
  - Consulta con evidencia    -> responde el LLM con el contexto recuperado.
"""

import unittest

from app.application.use_cases.chat_use_cases import (
    ABSTENTION_MESSAGE,
    ChatUseCase,
    classify_intent,
)
from app.application.dtos.rag_dtos import RAGRetrievalPolicy, RetrievedChunkDTO
from app.application.ports.llm_port import LLMPort
from app.application.ports.repository_ports import ChatRepositoryPort


class FakeConversation:
    def __init__(self, id: int = 1):
        self.id = id


class FakeMessage:
    def __init__(self, id: int, role: str, content: str):
        self.id = id
        self.role = role
        self.content = content


class FakeChatRepository(ChatRepositoryPort):
    def __init__(self):
        self.messages = []
        self.conv = FakeConversation()

    async def get_or_create_conversation(self, user_id: int):
        return self.conv

    async def reset_conversation(self, user_id: int):
        self.messages.clear()

    async def save_message(self, conversation_id: int, role: str, content: str):
        msg = FakeMessage(len(self.messages) + 1, role, content)
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
        self.messages = [m for m in self.messages if m.id <= message_id]
        msg.content = content
        return msg


class SpyLLM(LLMPort):
    """Devuelve una respuesta fuera de dominio para evidenciar la alucinacion evitada."""

    def __init__(self):
        self.generate_calls = 0
        self.embed_calls = 0

    async def generate_response(self, system_instruction, history, user_message, tools=None):
        self.generate_calls += 1
        return "El ceviche se prepara con pescado fresco, limon y cebolla."

    async def compute_embedding(self, text: str):
        self.embed_calls += 1
        return [0.1] * 768


class StubCorpusRepository:
    def __init__(self, chunks):
        self.chunks = chunks

    async def search_similar(self, embedding, *, limit, query_text,
                             max_cosine_distance, keyword_fallback_limit, **_politica_hibrida):
        return list(self.chunks)


class EmptyRelationRepository:
    async def get_assigned_tutors_data(self, user_id):
        return []

    async def get_assigned_students_data(self, user_id):
        return []

    async def get_calendar_events_data(self, **kwargs):
        return {"sessions": [], "events": []}


GROUNDING_CHUNK = RetrievedChunkDTO(
    text="Art. 1 - La tutoria es un servicio obligatorio.",
    source="reglamento_tutoria.json",
    cosine_distance=0.1,
    retrieval_method="vector",
)


def build_use_case(chunks):
    llm = SpyLLM()
    use_case = ChatUseCase(
        chat_repo=FakeChatRepository(),
        corpus_repo=StubCorpusRepository(chunks),
        llm=llm,
        tutor_assignment_repo=EmptyRelationRepository(),
        calendar_repo=EmptyRelationRepository(),
        rag_policy=RAGRetrievalPolicy(),
    )
    return use_case, llm


class TestChatAbstention(unittest.IsolatedAsyncioTestCase):
    async def test_out_of_domain_query_abstains_without_calling_llm(self):
        use_case, llm = build_use_case(chunks=[])

        msg = await use_case.send_chat_message(
            user_id=1, user_role="estudiante",
            user_content="dame una receta de ceviche peruano",
        )

        self.assertEqual(msg.content, ABSTENTION_MESSAGE)
        self.assertEqual(
            llm.generate_calls, 0,
            "El LLM no debe invocarse sin evidencia documental",
        )

    async def test_institutional_query_without_evidence_abstains(self):
        use_case, llm = build_use_case(chunks=[])

        msg = await use_case.send_chat_message(
            user_id=2, user_role="estudiante",
            user_content="que dice el reglamento de tutoria",
        )

        self.assertEqual(msg.content, ABSTENTION_MESSAGE)
        self.assertEqual(llm.generate_calls, 0)

    async def test_query_with_evidence_reaches_the_llm(self):
        use_case, llm = build_use_case(chunks=[GROUNDING_CHUNK])

        msg = await use_case.send_chat_message(
            user_id=3, user_role="estudiante",
            user_content="que dice el reglamento de tutoria",
        )

        self.assertEqual(llm.generate_calls, 1)
        self.assertNotEqual(msg.content, ABSTENTION_MESSAGE)

    async def test_greeting_is_conversational_and_skips_retrieval(self):
        """Un saludo no debe abstenerse ni gastar un embedding."""
        use_case, llm = build_use_case(chunks=[])

        msg = await use_case.send_chat_message(
            user_id=4, user_role="estudiante", user_content="Hola",
        )

        self.assertEqual(llm.generate_calls, 1)
        self.assertEqual(llm.embed_calls, 0, "SOCIAL no debe consultar el corpus")
        self.assertNotEqual(msg.content, ABSTENTION_MESSAGE)

    def test_greetings_classify_as_social_not_unknown(self):
        for greeting in ("Hola", "Buenos dias", "gracias", "ok"):
            with self.subTest(greeting=greeting):
                self.assertEqual(classify_intent(greeting), "SOCIAL")

    def test_substantive_unclassified_query_is_unknown_not_social(self):
        """UNKNOWN debe seguir intentando recuperacion; solo SOCIAL la omite."""
        self.assertEqual(classify_intent("dame una receta de ceviche peruano"), "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
