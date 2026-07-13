from typing import List, Dict
import json
from datetime import datetime, timedelta
from app.application.ports.repository_ports import ChatRepositoryPort, CorpusRepositoryPort
from app.application.ports.llm_port import LLMPort
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.session import Session
from app.infrastructure.database.models.tutor_assignment import TutorAssignment
from app.infrastructure.database.models.event import Event

class ChatUseCase:
    def __init__(
        self,
        chat_repo: ChatRepositoryPort,
        corpus_repo: CorpusRepositoryPort,
        llm: LLMPort
    ):
        self.chat_repo = chat_repo
        self.corpus_repo = corpus_repo
        self.llm = llm

    async def get_or_create_conversation(self, user_id: int):
        return await self.chat_repo.get_or_create_conversation(user_id)

    async def reset_conversation(self, user_id: int):
        return await self.chat_repo.reset_conversation(user_id)

    async def send_chat_message(self, user: 'User', user_content: str, db: 'AsyncSession'):
        conversation = await self.chat_repo.get_or_create_conversation(user.id)
        
        # Save user message
        await self.chat_repo.save_message(conversation.id, "user", user_content)
        
        # Get conversation history
        history_msgs = await self.chat_repo.get_history(conversation.id)
        history = []
        for msg in history_msgs:
            # We don't include the newly added user message in the history we pass separately
            if msg.id == history_msgs[-1].id and msg.role == "user":
                continue
            role_map = "user" if msg.role == "user" else "model"
            history.append({
                "role": role_map,
                "parts": [{"text": msg.content}]
            })
            
        # 1. Embed user query
        query_embedding = await self.llm.compute_embedding(user_content)
        
        # 2. Search corpus in pgvector
        similar_chunks = await self.corpus_repo.search_similar(query_embedding, limit=3)
        corpus_context = "\n\n".join(similar_chunks)
        
        # Define Tools for Function Calling
        async def get_assigned_tutors() -> str:
            """
            Obtiene la lista de tutores asignados al estudiante actual en el sistema.
            Retorna un JSON con el nombre, correo, oficina y especialidad de cada tutor.
            """
            result = await db.execute(
                select(TutorAssignment)
                .where(TutorAssignment.student_id == user.id)
                .options(
                    selectinload(TutorAssignment.tutor).selectinload(User.tutor_profile),
                    selectinload(TutorAssignment.service_type)
                )
            )
            assignments = result.scalars().all()
            if not assignments:
                return "No tienes ningún tutor asignado actualmente."
            
            data = []
            for a in assignments:
                t = a.tutor
                t_profile = t.tutor_profile if t else None
                data.append({
                    "tutor_name": t.full_name if t else "No definido",
                    "email": t.email if t else "No definido",
                    "office_location": t_profile.office_location if t_profile else "No definido",
                    "expertise_areas": t_profile.expertise_areas if t_profile else "No definido",
                    "service_type": a.service_type.name if a.service_type else "Tutoría",
                    "academic_period": a.academic_period
                })
            return json.dumps(data, ensure_ascii=False)

        async def get_assigned_students() -> str:
            """
            Obtiene la lista de estudiantes asignados al tutor actual en el sistema.
            Retorna un JSON con el nombre, correo, código de estudiante, celular, semestre actual, estado académico, periodo académico y tipo de tutoría de cada estudiante.
            """
            result = await db.execute(
                select(TutorAssignment)
                .where(TutorAssignment.tutor_id == user.id)
                .options(
                    selectinload(TutorAssignment.student).selectinload(User.student_profile),
                    selectinload(TutorAssignment.service_type)
                )
            )
            assignments = result.scalars().all()
            if not assignments:
                return "No tienes ningún estudiante asignado actualmente."
            
            data = []
            for a in assignments:
                s = a.student
                if not s:
                    continue
                s_profile = s.student_profile
                data.append({
                    "student_name": s.full_name,
                    "email": s.email,
                    "student_code": s_profile.student_code if s_profile else "No definido",
                    "current_semester": s_profile.current_semester if s_profile else "No definido",
                    "academic_status": s_profile.academic_status if s_profile else "No definido",
                    "phone_number": s_profile.phone_number if s_profile else "No definido",
                    "academic_period": a.academic_period,
                    "service_type": a.service_type.name if a.service_type else "Tutoría"
                })
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

            if user.role == "estudiante":
                session_query = select(Session).where(
                    Session.student_id == user.id,
                    Session.scheduled_at >= start_dt,
                    Session.scheduled_at <= end_dt
                ).options(
                    selectinload(Session.tutor).selectinload(User.tutor_profile),
                    selectinload(Session.service_type)
                )
            else:
                session_query = select(Session).where(
                    Session.tutor_id == user.id,
                    Session.scheduled_at >= start_dt,
                    Session.scheduled_at <= end_dt
                ).options(
                    selectinload(Session.student).selectinload(User.student_profile),
                    selectinload(Session.service_type)
                )

            sessions_res = await db.execute(session_query)
            sessions = sessions_res.scalars().all()

            if user.role == "estudiante":
                tutor_ids_subquery = select(TutorAssignment.tutor_id).where(TutorAssignment.student_id == user.id)
                session_ids_subquery = select(Session.id).where(Session.student_id == user.id)
                event_query = select(Event).where(
                    (Event.starts_at >= start_dt) & (Event.starts_at <= end_dt) &
                    ((Event.created_by.in_(tutor_ids_subquery)) | (Event.session_id.in_(session_ids_subquery)))
                )
            else:
                event_query = select(Event).where(
                    Event.created_by == user.id,
                    Event.starts_at >= start_dt,
                    Event.starts_at <= end_dt
                )

            events_res = await db.execute(event_query)
            events = events_res.scalars().all()

            result_data = {
                "sessions": [],
                "events": []
            }

            for s in sessions:
                other_name = s.tutor.full_name if user.role == "estudiante" else s.student.full_name
                result_data["sessions"].append({
                    "session_id": s.id,
                    "title": s.title or (s.service_type.name if s.service_type else "Tutoría"),
                    "scheduled_at": s.scheduled_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": s.status,
                    "location": s.location or "No definido",
                    "notes": s.notes or "",
                    "other_participant": other_name
                })

            for e in events:
                result_data["events"].append({
                    "event_id": e.id,
                    "title": e.title,
                    "starts_at": e.starts_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "ends_at": e.ends_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "type": e.type
                })

            return json.dumps(result_data, ensure_ascii=False)

        # Assemble list of tools based on user role
        tools = [get_calendar_events]
        if user.role == "estudiante":
            tools.append(get_assigned_tutors)
        elif user.role == "tutor":
            tools.append(get_assigned_students)

        system_instruction = (
            "Eres TutorIA, el tutor académico inteligente de la universidad UNSAAC. Te presentas como un amigable dinosaurio morado. "
            "Tu objetivo es ayudar a los estudiantes y tutores con sus consultas académicas, planes de estudio, reglamentos universitarios, "
            "técnicas de estudio y gestión de sus horarios.\n"
            "Mantén siempre un tono entusiasta, paciente, motivador, alegre y amigable. Utiliza emojis ocasionalmente para ser más cercano (🦖, 📚, ✍️, ✨).\n\n"
            f"La fecha y hora actual del servidor es: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n\n"
            "Tienes acceso a herramientas en tiempo real para obtener información específica del usuario. "
            "Si la consulta del usuario requiere conocer sus tutores asignados, estudiantes asignados, o sus horarios/actividades del calendario, "
            "DEBES invocar la herramienta correspondiente para dar una respuesta precisa basada en datos reales de la base de datos.\n\n"
            "Aquí tienes fragmentos relevantes de la base de datos oficial (corpus) de la universidad UNSAAC sobre el reglamento de tutoría y servicios:\n"
            f"{corpus_context}\n\n"
            "INSTRUCCIONES IMPORTANTES DE RESPUESTA:\n"
            "1. Intenta responder a la consulta del estudiante/tutor utilizando la información de la base de datos oficial (corpus) anterior o los datos recuperados por las herramientas.\n"
            "2. Si la respuesta NO se encuentra en la base de datos oficial anterior ni en los datos de las herramientas, debes responder utilizando tus conocimientos generales.\n"
            "3. En este último caso, debes aclarar obligatoriamente al inicio de tu respuesta que no tienes esa información en tu base de datos oficial, pero que según internet/conocimiento general es de cierta manera."
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
