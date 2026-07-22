from typing import Literal
import json
from datetime import datetime, timedelta
from app.application.ports.repository_ports import (
    ChatRepositoryPort,
    CorpusRepositoryPort,
    TutorAssignmentRepositoryPort,
    CalendarRepositoryPort,
)
from app.application.ports.llm_port import LLMPort
from app.application.dtos.rag_dtos import RAGRetrievalPolicy, RetrievedChunkDTO


class ChatUseCase:
    def __init__(
        self,
        chat_repo: ChatRepositoryPort,
        corpus_repo: CorpusRepositoryPort,
        llm: LLMPort,
        tutor_assignment_repo: TutorAssignmentRepositoryPort,
        calendar_repo: CalendarRepositoryPort,
        rag_policy: RAGRetrievalPolicy,
    ):
        self.chat_repo = chat_repo
        self.corpus_repo = corpus_repo
        self.llm = llm
        self.tutor_assignment_repo = tutor_assignment_repo
        self.calendar_repo = calendar_repo
        self.rag_policy = rag_policy

    async def get_or_create_conversation(self, user_id: int):
        return await self.chat_repo.get_or_create_conversation(user_id)

    async def reset_conversation(self, user_id: int):
        return await self.chat_repo.reset_conversation(user_id)

    async def send_chat_message(
        self,
        user_id: int,
        user_role: Literal["estudiante", "tutor"],
        user_content: str,
    ):
        conversation = await self.chat_repo.get_or_create_conversation(user_id)

        # Save user message
        await self.chat_repo.save_message(conversation.id, "user", user_content)

        # Get conversation history
        history_msgs = await self.chat_repo.get_history(conversation.id)
        history = []
        for msg in history_msgs:
            if msg.id == history_msgs[-1].id and msg.role == "user":
                continue
            role_map = "user" if msg.role == "user" else "model"
            history.append({
                "role": role_map,
                "parts": [{"text": msg.content}]
            })

        # RAG Query Expansion/Rewriting for short follow-up messages
        prev_user_content = ""
        for i in range(len(history_msgs) - 2, -1, -1):
            if history_msgs[i].role == "user":
                prev_user_content = history_msgs[i].content
                break

        if prev_user_content and len(user_content.split()) <= 4:
            rag_query = f"{prev_user_content} {user_content}"
        else:
            rag_query = user_content

        # 1. Embed RAG query
        query_embedding = await self.llm.compute_embedding(rag_query)

        # 2. Search corpus using policy
        retrieved_chunks: list[RetrievedChunkDTO] = await self.corpus_repo.search_similar(
            query_embedding,
            limit=self.rag_policy.limit,
            query_text=rag_query,
            max_cosine_distance=self.rag_policy.max_cosine_distance,
            keyword_fallback_limit=self.rag_policy.keyword_fallback_limit,
        )

        if retrieved_chunks:
            context_parts = []
            for chunk in retrieved_chunks:
                src = chunk.source or "Desconocido"
                context_parts.append(f"[Fuente: {src}]\n{chunk.text}")
            corpus_context = "\n\n".join(context_parts)
        else:
            corpus_context = "NO HAY FRAGMENTOS RELEVANTES DEL CORPUS PARA ESTA CONSULTA."

        # Define Tools for Function Calling
        async def get_assigned_tutors() -> str:
            """
            Obtiene la lista de tutores asignados al estudiante actual en el sistema.
            Retorna un JSON con el nombre, correo, oficina y especialidad de cada tutor.
            """
            data = await self.tutor_assignment_repo.get_assigned_tutors_data(user_id)
            if not data:
                return "No tienes ningún tutor asignado actualmente."
            return json.dumps(data, ensure_ascii=False)

        async def get_assigned_students() -> str:
            """
            Obtiene la lista de estudiantes asignados al tutor actual en el sistema.
            Retorna un JSON con el nombre, correo, código de estudiante, celular, semestre actual, estado académico, periodo académico y tipo de tutoría de cada estudiante.
            """
            data = await self.tutor_assignment_repo.get_assigned_students_data(user_id)
            if not data:
                return "No tienes ningún estudiante asignado actualmente."
            return json.dumps(data, ensure_ascii=False)

        async def get_calendar_events(start_date: str = None, end_date: str = None) -> str:
            """
            Obtiene el listado de actividades del calendario, tutorías programadas y sesiones del usuario actual
            en un rango de fechas. Las fechas opcionales deben tener el formato 'YYYY-MM-DD'.
            """
            now = datetime.now()
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    return "Error: Formato de fecha de inicio inválido. Debe ser YYYY-MM-DD."
            else:
                start_dt = now - timedelta(days=30)

            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    return "Error: Formato de fecha de fin inválido. Debe ser YYYY-MM-DD."
            else:
                end_dt = now + timedelta(days=30)

            result_data = await self.calendar_repo.get_calendar_events_data(
                user_id=user_id,
                role=user_role,
                start_dt=start_dt,
                end_dt=end_dt
            )
            return json.dumps(result_data, ensure_ascii=False)

        # Assemble list of tools based on user role
        tools = [get_calendar_events]
        if user_role == "estudiante":
            tools.append(get_assigned_tutors)
        elif user_role == "tutor":
            tools.append(get_assigned_students)

        system_instruction = (
            "Eres TutorIA, el tutor académico inteligente de la universidad UNSAAC. Te presentas como un amigable dinosaurio morado. "
            "Tu objetivo es ayudar a los estudiantes y tutores con sus consultas académicas, planes de estudio, reglamentos universitarios, "
            "técnicas de estudio y gestión de sus horarios.\n"
            "Mantén un tono entusiasta, paciente y amigable, pero sé conciso, directo y profesional.\n\n"
            f"La fecha y hora actual del servidor es: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n"
            "DIRECTIVA DE FECHAS Y SEMESTRES: Para preguntas sobre el cronograma o calendario académico (exámenes, fin de clases, inicio, etc.):\n"
            "- Si la fecha actual está entre el 30 de marzo de 2026 y el 20 de agosto de 2026, asume por defecto que se refiere al semestre 2026-I (salvo que el usuario especifique otro).\n"
            "- Si la fecha actual es posterior al 20 de agosto de 2026 (por ejemplo, en septiembre) y hasta el 12 de enero de 2027, asume por defecto que se refiere al semestre 2026-II.\n"
            "- Sé dinámico y adapta tu respuesta si el usuario pregunta explícitamente por un semestre en particular.\n\n"
            "Tienes acceso a herramientas en tiempo real para obtener información específica del usuario. "
            "Si la consulta del usuario requiere conocer sus tutores asignados, estudiantes asignados, o sus horarios/actividades del calendario, "
            "DEBES invocar la herramienta correspondiente para dar una respuesta precisa basada en datos reales de la base de datos.\n\n"
            "Aquí tienes fragmentos relevantes de la base de datos oficial (corpus) de la universidad UNSAAC sobre el reglamento de tutoría y servicios:\n"
            f"{corpus_context}\n\n"
            "REGLAS OBLIGATORIAS DE GROUNDING Y ABSTENCIÓN:\n"
            "1. No inventes normas, fechas, procedimientos, autoridades, requisitos o datos institucionales de la UNSAAC.\n"
            "2. No presentes como oficial una afirmación que no aparezca en los fragmentos del corpus o en las respuestas de las herramientas.\n"
            "3. Si el contexto del corpus indica 'NO HAY FRAGMENTOS RELEVANTES DEL CORPUS PARA ESTA CONSULTA.' o no permite responder la consulta sobre la UNSAAC con certeza, debes responder exactamente:\n"
            "   'No cuento con información suficiente en la base oficial de la UNSAAC para responder con certeza.'\n"
            "4. Para consultas académicas generales o técnicas de estudio no normativas, puedes ofrecer recomendaciones orientativas, aclarando que no constituyen normativa oficial de la universidad.\n\n"
            "REGLAS OBLIGATORIAS DE FORMATO Y CONCISIÓN:\n"
            "1. Sé conciso y ve al grano inmediatamente. Evita introducciones con relleno y despedidas repetitivas.\n"
            "2. Si la consulta requiere datos específicos recuperados por las herramientas (como quién es su tutor, estudiantes asignados o próximas tutorías), debes mostrar esa información CLAVE en viñetas claras al principio de tu respuesta.\n"
            "3. Utiliza un máximo de 2 emojis en todo el mensaje.\n"
            "4. Utiliza negrita (`**`) únicamente para destacar datos críticos.\n"
            "5. Si la consulta es sobre reglamentos o servicios generales, resume la respuesta en máximo 1 o 2 párrafos cortos y precisos."
        )

        # 3. Generate response via Gemini using function calling
        assistant_content = await self.llm.generate_response(
            system_instruction=system_instruction,
            history=history,
            user_message=user_content,
            tools=tools
        )

        # Save assistant message
        assistant_msg = await self.chat_repo.save_message(conversation.id, "assistant", assistant_content)
        return assistant_msg
