from typing import List, Dict
from app.application.ports.repository_ports import ChatRepositoryPort, CorpusRepositoryPort
from app.application.ports.llm_port import LLMPort
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.session import Session
from app.infrastructure.database.models.tutor_assignment import TutorAssignment

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
        
        system_instruction = (
            "Eres TutorIA, el tutor académico inteligente de la universidad UNSAAC. Te presentas como un amigable dinosaurio morado. "
            "Tu objetivo es ayudar a los estudiantes con sus consultas académicas, planes de estudio, reglamentos universitarios y técnicas de estudio. "
            "Mantén siempre un tono entusiasta, paciente, motivador, alegre y amigable. Utiliza emojis ocasionalmente para ser más cercano (🦖, 📚, ✍️, ✨).\n\n"
            "Aquí tienes fragmentos relevantes de la base de datos oficial (corpus) de la universidad UNSAAC sobre el reglamento de tutoría y servicios:\n"
            f"{corpus_context}\n\n"
        )
        
        # Inject dynamic context for Tutors
        if user.role == "tutor":
            result = await db.execute(
                select(Session)
                .where(Session.tutor_id == user.id)
                .options(
                    selectinload(Session.student).selectinload(User.student_profile),
                    selectinload(Session.student).selectinload(User.tutor_profile),
                    selectinload(Session.student).selectinload(User.admin_profile)
                )
                .options(selectinload(Session.service_type))
            )
            tutor_sessions = result.scalars().all()
            
            schedule_info = "El usuario actual con el que estás hablando es un TUTOR de la universidad. Esta es la información de sus tutorías programadas y sus alumnos:\n"
            if not tutor_sessions:
                schedule_info += "Actualmente no tiene ninguna tutoría o alumno asignado en el sistema.\n"
            else:
                for s in tutor_sessions:
                    student_name = s.student.full_name if s.student else f"Estudiante ID {s.student_id}"
                    svc_name = s.service_type.name if s.service_type else "Tutoría"
                    schedule_info += f"- Alumno: {student_name} | Actividad: {s.title or svc_name} | Fecha y Hora: {s.scheduled_at} | Estado: {s.status} | Lugar: {s.location or 'No definido'} | Notas: {s.notes or 'Ninguna'}\n"
            
            system_instruction += schedule_info + "\n"
            
        # Inject dynamic context for Students
        elif user.role == "estudiante":
            # Fetch permanent assignments
            assignment_result = await db.execute(
                select(TutorAssignment)
                .where(TutorAssignment.student_id == user.id)
                .options(
                    selectinload(TutorAssignment.tutor).selectinload(User.tutor_profile)
                )
            )
            assignments = assignment_result.scalars().all()
            
            # Fetch scheduled sessions
            result = await db.execute(
                select(Session)
                .where(Session.student_id == user.id)
                .options(
                    selectinload(Session.tutor).selectinload(User.tutor_profile),
                    selectinload(Session.tutor).selectinload(User.student_profile),
                    selectinload(Session.tutor).selectinload(User.admin_profile)
                )
                .options(selectinload(Session.service_type))
            )
            student_sessions = result.scalars().all()
            
            schedule_info = "El usuario actual con el que estás hablando es un ESTUDIANTE de la universidad. Esta es su información académica:\n"
            
            if not assignments:
                schedule_info += "- Tutor Principal Asignado: Ninguno (No tiene tutor asignado en el sistema).\n"
            else:
                for a in assignments:
                    tutor_name = a.tutor.full_name if a.tutor else f"Tutor ID {a.tutor_id}"
                    schedule_info += f"- Tutor Principal Asignado: {tutor_name} (Periodo: {a.academic_period})\n"
            
            if not student_sessions:
                schedule_info += "- Tutorías Programadas: Ninguna actualmente.\n"
            else:
                schedule_info += "- Tutorías Programadas:\n"
                for s in student_sessions:
                    tutor_name = s.tutor.full_name if s.tutor else f"Tutor ID {s.tutor_id}"
                    svc_name = s.service_type.name if s.service_type else "Tutoría"
                    schedule_info += f"  * Tutor: {tutor_name} | Actividad: {s.title or svc_name} | Fecha y Hora: {s.scheduled_at} | Estado: {s.status} | Lugar: {s.location or 'No definido'}\n"
            
            system_instruction += schedule_info + "\n"


        system_instruction += (
            "INSTRUCCIONES IMPORTANTES DE RESPUESTA:\n"
            "1. Intenta responder a la consulta del estudiante/tutor utilizando la información de la base de datos oficial (corpus) anterior o la información de su horario provista.\n"
            "2. Si la respuesta NO se encuentra en la base de datos oficial anterior o en el contexto de sus tutorías, debes responder utilizando tus conocimientos generales.\n"
            "3. En este último caso, debes aclarar obligatoriamente al inicio de tu respuesta que no tienes esa información en tu base de datos oficial, pero que según internet/conocimiento general es de cierta manera."
        )
        
        # 3. Generate response via Gemini
        assistant_content = await self.llm.generate_response(
            system_instruction=system_instruction,
            history=history,
            user_message=user_content
        )
        
        # Save assistant message
        assistant_msg = await self.chat_repo.save_message(conversation.id, "assistant", assistant_content)
        return assistant_msg
