import unittest
import json
import os
import ast
import inspect
from datetime import datetime

from app.application.use_cases.chat_use_cases import ChatUseCase
from app.application.ports.repository_ports import (
    ChatRepositoryPort,
    CorpusRepositoryPort,
    TutorAssignmentRepositoryPort,
    CalendarRepositoryPort,
)
from app.application.ports.llm_port import LLMPort
from app.application.dtos.chat_tool_dtos import (
    AssignedTutorDTO,
    AssignedStudentDTO,
    CalendarDataDTO,
)
from app.application.dtos.rag_dtos import RetrievedChunkDTO, RAGRetrievalPolicy


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
        self.conv = FakeConversation(id=1)

    async def get_or_create_conversation(self, user_id: int):
        return self.conv

    async def reset_conversation(self, user_id: int):
        self.messages.clear()

    async def save_message(self, conversation_id: int, role: str, content: str):
        msg = FakeMessage(id=len(self.messages) + 1, role=role, content=content)
        self.messages.append(msg)
        return msg

    async def get_history(self, conversation_id: int, limit: int | None = None):
        return self.messages[-limit:] if limit else self.messages


class FakeCorpusRepository(CorpusRepositoryPort):
    async def search_similar(
        self,
        query_embedding: list,
        *,
        limit: int,
        query_text: str | None,
        max_cosine_distance: float,
        keyword_fallback_limit: int,
    ):
        return [
            RetrievedChunkDTO(
                text="Art. 1 - La tutoría es obligatoria.",
                source="reglamento.json",
                cosine_distance=0.1,
                retrieval_method="vector"
            )
        ]

    async def insert_chunk(self, text: str, embedding: list):
        pass


class FakeLLM(LLMPort):
    def __init__(self):
        self.last_tools = []

    async def generate_response(self, system_instruction: str, history: list, user_message: str, tools: list = None):
        self.last_tools = tools or []
        return "Respuesta de prueba del asistente."

    async def compute_embedding(self, text: str):
        return [0.1] * 768


class FakeTutorAssignmentRepository(TutorAssignmentRepositoryPort):
    def __init__(self, tutors_data=None, students_data=None):
        self.last_student_id_queried = None
        self.last_tutor_id_queried = None
        self.tutors_data = tutors_data if tutors_data is not None else [
            {
                "tutor_name": "Ing. Juan Pérez",
                "email": "juan.perez@unsaac.edu.pe",
                "office_location": "Pabellón A - 201",
                "expertise_areas": "Inteligencia Artificial",
                "service_type": "Tutoría Individual",
                "academic_period": "2026-I"
            }
        ]
        self.students_data = students_data if students_data is not None else [
            {
                "student_name": "Maria Lopez",
                "email": "maria.lopez@unsaac.edu.pe",
                "student_code": "182930",
                "current_semester": 7,
                "academic_status": "Regular",
                "phone_number": "987654321",
                "academic_period": "2026-I",
                "service_type": "Tutoría Individual"
            }
        ]

    async def get_assigned_tutors_data(self, student_id: int):
        self.last_student_id_queried = student_id
        return self.tutors_data

    async def get_assigned_students_data(self, tutor_id: int):
        self.last_tutor_id_queried = tutor_id
        return self.students_data

    async def get_assigned_student_ids(self, tutor_id: int):
        return []


class FakeCalendarRepository(CalendarRepositoryPort):
    def __init__(self, calendar_data=None):
        self.last_user_id_queried = None
        self.last_role_queried = None
        self.last_start_dt_queried = None
        self.last_end_dt_queried = None
        self.calendar_data = calendar_data if calendar_data is not None else {
            "sessions": [
                {
                    "session_id": 10,
                    "title": "Sesión de Orientación",
                    "scheduled_at": "2026-08-01 10:00:00",
                    "status": "programada",
                    "location": "Cubículo 4",
                    "notes": "Revisión de avances",
                    "other_participant": "Ing. Juan Pérez"
                }
            ],
            "events": [
                {
                    "event_id": 1,
                    "title": "Examen Parcial",
                    "starts_at": "2026-08-05 08:00:00",
                    "ends_at": "2026-08-05 10:00:00",
                    "type": "examen"
                }
            ]
        }

    async def get_calendar_events_data(self, user_id: int, role: str, start_dt: datetime, end_dt: datetime):
        self.last_user_id_queried = user_id
        self.last_role_queried = role
        self.last_start_dt_queried = start_dt
        self.last_end_dt_queried = end_dt
        return self.calendar_data


class TestChatUseCase(unittest.IsolatedAsyncioTestCase):

    async def test_send_message_triggers_assigned_tutor_tool(self):
        chat_repo = FakeChatRepository()
        corpus_repo = FakeCorpusRepository()
        llm = FakeLLM()
        tutor_assignment_repo = FakeTutorAssignmentRepository()
        calendar_repo = FakeCalendarRepository()
        rag_policy = RAGRetrievalPolicy()

        use_case = ChatUseCase(
            chat_repo=chat_repo,
            corpus_repo=corpus_repo,
            llm=llm,
            tutor_assignment_repo=tutor_assignment_repo,
            calendar_repo=calendar_repo,
            rag_policy=rag_policy,
        )

        res = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="¿Quién es mi tutor?")

        self.assertIn("Tu tutor asignado es", res.content)
        self.assertIn("Ing. Juan Pérez", res.content)
        self.assertEqual(tutor_assignment_repo.last_student_id_queried, 101)

    async def test_send_message_triggers_assigned_students_tool(self):
        chat_repo = FakeChatRepository()
        corpus_repo = FakeCorpusRepository()
        llm = FakeLLM()
        tutor_assignment_repo = FakeTutorAssignmentRepository()
        calendar_repo = FakeCalendarRepository()
        rag_policy = RAGRetrievalPolicy()

        use_case = ChatUseCase(
            chat_repo=chat_repo,
            corpus_repo=corpus_repo,
            llm=llm,
            tutor_assignment_repo=tutor_assignment_repo,
            calendar_repo=calendar_repo,
            rag_policy=rag_policy,
        )

        res = await use_case.send_chat_message(user_id=201, user_role="tutor", user_content="¿Quiénes son mis alumnos?")

        self.assertIn("Tus estudiantes asignados son", res.content)
        self.assertIn("Maria Lopez", res.content)
        self.assertEqual(tutor_assignment_repo.last_tutor_id_queried, 201)

    async def test_send_message_triggers_calendar_events_tool(self):
        chat_repo = FakeChatRepository()
        corpus_repo = FakeCorpusRepository()
        llm = FakeLLM()
        tutor_assignment_repo = FakeTutorAssignmentRepository()
        calendar_repo = FakeCalendarRepository()
        rag_policy = RAGRetrievalPolicy()

        use_case = ChatUseCase(
            chat_repo=chat_repo,
            corpus_repo=corpus_repo,
            llm=llm,
            tutor_assignment_repo=tutor_assignment_repo,
            calendar_repo=calendar_repo,
            rag_policy=rag_policy,
        )

        res = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="¿Qué reuniones tengo?")

        self.assertIn("actividades programadas", res.content)
        self.assertEqual(calendar_repo.last_user_id_queried, 101)
        self.assertEqual(calendar_repo.last_role_queried, "estudiante")

    async def test_empty_results_handling(self):
        chat_repo = FakeChatRepository()
        corpus_repo = FakeCorpusRepository()
        llm = FakeLLM()
        tutor_assignment_repo = FakeTutorAssignmentRepository(tutors_data=[], students_data=[])
        calendar_repo = FakeCalendarRepository(calendar_data={"sessions": [], "events": []})
        rag_policy = RAGRetrievalPolicy()

        use_case = ChatUseCase(
            chat_repo=chat_repo,
            corpus_repo=corpus_repo,
            llm=llm,
            tutor_assignment_repo=tutor_assignment_repo,
            calendar_repo=calendar_repo,
            rag_policy=rag_policy,
        )

        res_tutor = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="¿Quién es mi tutor?")
        self.assertIn("No tienes ningún tutor asignado actualmente", res_tutor.content)

        res_cal = await use_case.send_chat_message(user_id=101, user_role="estudiante", user_content="¿Qué reuniones tengo?")
        self.assertIn("No tienes tutorías ni eventos programados", res_cal.content)



    def test_architectural_decoupling_import_rules(self):
        use_case_path = os.path.join(
            os.path.dirname(__file__),
            "../../app/application/use_cases/chat_use_cases.py"
        )
        with open(use_case_path, "r", encoding="utf-8") as f:
            code_text = f.read()

        # AST Inspection
        parsed = ast.parse(code_text)
        imported_modules = []
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.append(node.module)

        forbidden_prefixes = ["fastapi", "sqlalchemy", "app.infrastructure"]
        for mod in imported_modules:
            for prefix in forbidden_prefixes:
                self.assertFalse(
                    mod.startswith(prefix),
                    f"Forbidden import '{mod}' found in chat_use_cases.py"
                )

        # Inspection of signature and constructor parameters
        sig = inspect.signature(ChatUseCase.send_chat_message)
        params = list(sig.parameters.keys())
        self.assertNotIn("db", params, "send_chat_message should not contain 'db' parameter")
        self.assertIn("user_id", params, "send_chat_message must contain 'user_id'")
        self.assertIn("user_role", params, "send_chat_message must contain 'user_role'")
        self.assertIn("user_content", params, "send_chat_message must contain 'user_content'")

        # Constructor parameter inspection (no default values / optional repos)
        init_sig = inspect.signature(ChatUseCase.__init__)
        for name, param in init_sig.parameters.items():
            if name == "self":
                continue
            self.assertEqual(
                param.default,
                inspect.Parameter.empty,
                f"Constructor parameter '{name}' in ChatUseCase must not have a default value"
            )

    def test_legacy_chat_service_removal_and_application_purity(self):
        # 1. chat_service.py file does not exist
        legacy_file = os.path.join(
            os.path.dirname(__file__),
            "../../app/application/use_cases/chat_service.py"
        )
        self.assertFalse(os.path.exists(legacy_file), "chat_service.py must not exist")

        # 2 & 5. No static or dynamic imports of chat_service in backend/app
        app_dir = os.path.join(os.path.dirname(__file__), "../../app")
        for root, _, files in os.walk(app_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.assertNotIn("chat_service", content, f"Found chat_service reference in {filepath}")

        # 3. endpoints/chat.py uses ChatUseCase
        endpoint_path = os.path.join(os.path.dirname(__file__), "../../app/infrastructure/api/v1/endpoints/chat.py")
        with open(endpoint_path, "r", encoding="utf-8") as f:
            endpoint_content = f.read()
        self.assertIn("ChatUseCase", endpoint_content, "endpoints/chat.py must use ChatUseCase")

        # 4. dependencies.py constructs ChatUseCase
        dep_path = os.path.join(os.path.dirname(__file__), "../../app/infrastructure/api/dependencies.py")
        with open(dep_path, "r", encoding="utf-8") as f:
            dep_content = f.read()
        self.assertIn("def get_chat_use_case", dep_content, "dependencies.py must construct ChatUseCase")
        self.assertIn("ChatUseCase(", dep_content)

        # 8. Entire application directory is clean of forbidden framework imports
        use_cases_dir = os.path.join(os.path.dirname(__file__), "../../app/application")
        forbidden_prefixes = ["fastapi", "sqlalchemy", "app.infrastructure"]
        for root, _, files in os.walk(use_cases_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8") as f:
                        code = f.read()
                    parsed = ast.parse(code)
                    imported_modules = []
                    for node in ast.walk(parsed):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imported_modules.append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                imported_modules.append(node.module)

                    for mod in imported_modules:
                        for prefix in forbidden_prefixes:
                            self.assertFalse(
                                mod.startswith(prefix),
                                f"Forbidden import '{mod}' found in {filepath}"
                            )


if __name__ == "__main__":
    unittest.main()
