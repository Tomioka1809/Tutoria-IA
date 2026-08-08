"""Edicion de un mensaje propio con regeneracion de la respuesta.

Editar la pregunta invalida la respuesta que le siguio, asi que la edicion
descarta esa respuesta y todo lo posterior y vuelve a responder. Eso no es un
detalle cosmetico: el historial alimenta `reconstruct_query`, de modo que dejar
viva una respuesta que contradice la pregunta editada envenena la recuperacion
de los turnos siguientes.

Contrato verificado aqui:
  - El texto se reescribe y lo posterior desaparece.
  - Se responde por el mismo camino que un mensaje nuevo: misma guarda
    institucional, misma abstencion, misma recuperacion.
  - No se puede editar un mensaje ajeno ni una respuesta del asistente.
"""
import unittest

from app.application.dtos.rag_dtos import RAGRetrievalPolicy, RetrievedChunkDTO
from app.application.ports.llm_port import LLMPort
from app.application.ports.repository_ports import (
    ChatRepositoryPort,
    CorpusRepositoryPort,
)
from app.application.use_cases.chat_use_cases import ABSTENTION_MESSAGE, ChatUseCase


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
        self.conv = FakeConversation(id=conv_id)
        self.messages: list[FakeMessage] = []
        self._siguiente_id = 1

    async def get_or_create_conversation(self, user_id: int):
        return self.conv

    async def reset_conversation(self, user_id: int):
        self.messages.clear()

    async def save_message(self, conversation_id: int, role: str, content: str):
        msg = FakeMessage(self._siguiente_id, role, content, conversation_id)
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
        self.messages = [m for m in self.messages if m.id <= message_id]
        msg.content = content
        return msg


class FakeCorpusRepository(CorpusRepositoryPort):
    def __init__(self, chunks=None):
        self.chunks = chunks if chunks is not None else [
            RetrievedChunkDTO(
                text="Art. 1 - La tutoría es un servicio obligatorio.",
                source="reglamento_tutoria.json",
                distance=0.1,
            )
        ]
        self.consultas = []

    async def search_similar(self, query_embedding: list, **kwargs):
        self.consultas.append(kwargs.get("query_text"))
        return self.chunks

    async def insert_chunk(self, *args, **kwargs):
        raise NotImplementedError("El chat no indexa; este doble solo recupera.")


class FakeLLM(LLMPort):
    def __init__(self, response_text="Respuesta generada."):
        self.response_text = response_text
        self.generate_calls = 0
        self.last_user_message = None

    async def generate_response(self, system_instruction, history, user_message, tools=None):
        self.generate_calls += 1
        self.last_user_message = user_message
        return self.response_text

    async def compute_embedding(self, text: str):
        return [0.1] * 768


class FakeTutorAssignmentRepository:
    async def get_assigned_tutors_data(self, user_id: int):
        return []

    async def get_assigned_students_data(self, user_id: int):
        return []


class FakeCalendarRepository:
    async def get_events_for_user(self, user_id: int, **kwargs):
        return []


def construir(chat_repo=None, corpus_repo=None, llm=None):
    return ChatUseCase(
        chat_repo=chat_repo or FakeChatRepository(),
        corpus_repo=corpus_repo or FakeCorpusRepository(),
        llm=llm or FakeLLM(),
        tutor_assignment_repo=FakeTutorAssignmentRepository(),
        calendar_repo=FakeCalendarRepository(),
        rag_policy=RAGRetrievalPolicy(),
    )


class TestEdicionDeMensaje(unittest.IsolatedAsyncioTestCase):
    async def _conversacion_con_dos_turnos(self):
        repo = FakeChatRepository()
        caso = construir(chat_repo=repo)
        await caso.send_chat_message(1, "estudiante", "¿Qué es la tutoría?")
        await caso.send_chat_message(1, "estudiante", "¿Y el reglamento?")
        return repo, caso

    async def test_reescribe_el_texto_del_mensaje(self):
        repo, caso = await self._conversacion_con_dos_turnos()
        id_primero = repo.messages[0].id

        await caso.edit_chat_message(1, "estudiante", id_primero, "¿Qué es la matrícula?")

        self.assertEqual("¿Qué es la matrícula?", repo.messages[0].content)

    async def test_descarta_la_respuesta_vieja_y_todo_lo_posterior(self):
        """El punto de la edicion: sin el corte, el historial se contradice y
        esa contradiccion entra en la reconstruccion de la consulta."""
        repo, caso = await self._conversacion_con_dos_turnos()
        id_primero = repo.messages[0].id
        self.assertEqual(4, len(repo.messages))

        await caso.edit_chat_message(1, "estudiante", id_primero, "¿Qué es la matrícula?")

        # Queda la pregunta editada y su respuesta nueva, nada mas.
        self.assertEqual(2, len(repo.messages))
        self.assertEqual(["user", "assistant"], [m.role for m in repo.messages])
        self.assertNotIn("¿Y el reglamento?", [m.content for m in repo.messages])

    async def test_vuelve_a_responder_con_el_texto_nuevo(self):
        repo = FakeChatRepository()
        corpus = FakeCorpusRepository()
        caso = construir(chat_repo=repo, corpus_repo=corpus)
        await caso.send_chat_message(1, "estudiante", "¿Qué es la tutoría?")
        id_primero = repo.messages[0].id

        await caso.edit_chat_message(1, "estudiante", id_primero, "¿Qué es la matrícula?")

        # La ultima recuperacion se hizo con el texto editado, no con el viejo.
        self.assertIn("matrícula", corpus.consultas[-1])

    async def test_la_respuesta_nueva_es_el_ultimo_mensaje(self):
        repo, caso = await self._conversacion_con_dos_turnos()
        id_primero = repo.messages[0].id

        devuelto = await caso.edit_chat_message(
            1, "estudiante", id_primero, "¿Qué es la matrícula?"
        )

        self.assertEqual("assistant", devuelto.role)
        self.assertIs(repo.messages[-1], devuelto)

    async def test_no_deja_editar_un_mensaje_del_asistente(self):
        repo, caso = await self._conversacion_con_dos_turnos()
        id_respuesta = next(m.id for m in repo.messages if m.role == "assistant")

        with self.assertRaises(PermissionError):
            await caso.edit_chat_message(1, "estudiante", id_respuesta, "texto nuevo")

    async def test_no_deja_editar_un_mensaje_de_otra_conversacion(self):
        """Sin esta comprobacion, el id de un mensaje ajeno bastaria para
        reescribir la conversacion de otro usuario."""
        repo, caso = await self._conversacion_con_dos_turnos()
        ajeno = FakeMessage(999, "user", "mensaje de otro", conversation_id=42)
        repo.messages.append(ajeno)

        with self.assertRaises(LookupError):
            await caso.edit_chat_message(1, "estudiante", 999, "texto nuevo")

    async def test_falla_si_el_mensaje_no_existe(self):
        _, caso = await self._conversacion_con_dos_turnos()

        with self.assertRaises(LookupError):
            await caso.edit_chat_message(1, "estudiante", 12345, "texto nuevo")

    async def test_rechaza_un_texto_vacio(self):
        repo, caso = await self._conversacion_con_dos_turnos()
        id_primero = repo.messages[0].id

        with self.assertRaises(ValueError):
            await caso.edit_chat_message(1, "estudiante", id_primero, "   ")

    async def test_un_texto_vacio_no_toca_la_conversacion(self):
        """La validacion va antes de truncar: si no, un texto vacio borraria el
        historial y ademas fallaria."""
        repo, caso = await self._conversacion_con_dos_turnos()
        antes = list(repo.messages)

        with self.assertRaises(ValueError):
            await caso.edit_chat_message(1, "estudiante", repo.messages[0].id, "")

        self.assertEqual(antes, repo.messages)

    async def test_la_edicion_pasa_por_la_misma_abstencion_que_un_envio(self):
        """Una edicion que esquivara el corte por falta de evidencia seria una
        via para obtener respuestas que el envio normal no da."""
        repo = FakeChatRepository()
        llm = FakeLLM()
        caso = construir(chat_repo=repo, corpus_repo=FakeCorpusRepository(chunks=[]), llm=llm)
        await caso.send_chat_message(1, "estudiante", "¿Qué es la tutoría?")
        id_primero = repo.messages[0].id
        llamadas_antes = llm.generate_calls

        devuelto = await caso.edit_chat_message(
            1, "estudiante", id_primero, "¿Cómo preparo un ceviche?"
        )

        self.assertEqual(ABSTENTION_MESSAGE, devuelto.content)
        self.assertEqual(llamadas_antes, llm.generate_calls, "no debe invocar al LLM")

    async def test_la_edicion_conserva_la_guarda_institucional(self):
        repo = FakeChatRepository()
        caso = construir(chat_repo=repo)
        await caso.send_chat_message(1, "estudiante", "¿Qué es la tutoría?")
        id_primero = repo.messages[0].id

        devuelto = await caso.edit_chat_message(
            1, "estudiante", id_primero, "¿Cuánto cuesta la matrícula en la UNSA?"
        )

        self.assertIn("UNSAAC", devuelto.content)
        self.assertIn("UNSA", devuelto.content)

    async def test_editar_el_ultimo_mensaje_no_borra_los_anteriores(self):
        repo, caso = await self._conversacion_con_dos_turnos()
        id_segundo = repo.messages[2].id

        await caso.edit_chat_message(1, "estudiante", id_segundo, "¿Y el cronograma?")

        self.assertEqual(4, len(repo.messages))
        self.assertEqual("¿Qué es la tutoría?", repo.messages[0].content)
        self.assertEqual("¿Y el cronograma?", repo.messages[2].content)


if __name__ == "__main__":
    unittest.main()
