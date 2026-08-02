from typing import Literal
import json
import logging
import re
import unicodedata
from datetime import datetime, timedelta

from app.application.ports.repository_ports import (
    ChatRepositoryPort,
    CorpusRepositoryPort,
    TutorAssignmentRepositoryPort,
    CalendarRepositoryPort,
)
from app.application.ports.llm_port import LLMPort
from app.application.dtos.rag_dtos import RAGRetrievalPolicy, RetrievedChunkDTO

logger = logging.getLogger(__name__)

ABSTENTION_MESSAGE = (
    "No cuento con información suficiente en la base oficial de la UNSAAC "
    "para responder con certeza."
)

# Ventana de contexto conversacional. Sin tope, cada turno reenvia la conversacion
# completa al LLM y el costo por mensaje crece de forma indefinida. El valor cubre con
# holgura los ultimos 6 mensajes que consultan las heuristicas de malla y seguimiento.
HISTORY_WINDOW_MESSAGES = 20


def _normalize_text_pure(text: str) -> str:
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text.casefold())
    cleaned = "".join(c for c in nfkd if not unicodedata.combining(c))
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def classify_intent(user_content: str, user_role: str = "estudiante") -> str:
    norm = _normalize_text_pure(user_content)
    if not norm:
        return "UNKNOWN"

    greetings_thanks = [
        "hola", "buenas", "buenos dias", "buenas tardes", "buenas noches",
        "gracias", "muchas gracias", "cuentame algo", "necesito ayuda",
        "ayuda", "ok", "vale", "esta bien"
    ]
    # SOCIAL se separa de UNKNOWN: un saludo debe recibir respuesta conversacional,
    # mientras que una consulta sustantiva sin clasificar debe intentar recuperacion
    # y abstenerse si el corpus no la respalda.
    if norm in greetings_thanks:
        return "SOCIAL"

    calendar_keywords = [
        "proxima tutoria", "siguiente tutoria", "tutoria programada", "tutorias programadas",
        "mis tutorias", "mis sesiones", "mi calendario", "horario de tutoria", "agenda de tutoria",
        "tengo tutoria", "cuando es mi tutoria", "sesiones programadas", "mis citas", "reuniones tengo",
        "proxima sesion", "siguiente sesion", "mis reuniones"
    ]

    tutor_keywords = [
        "quien es mi tutor", "mi tutor asignado", "contacto con mi tutor", "contactar a mi tutor",
        "correo de mi tutor", "email de mi tutor", "oficina de mi tutor", "datos de mi tutor",
        "como contacto con mi tutor", "quien es el tutor", "quien me toca de tutor"
    ]

    student_keywords = [
        "mis estudiantes", "mis tutorados", "estudiantes asignados", "alumnos asignados",
        "lista de estudiantes", "quienes son mis tutorados", "mis alumnos"
    ]

    documental_keywords = [
        "reglamento", "reglamentos", "intercambio estudiantil", "malla curricular", "plan de estudios",
        "que es una tutoria", "glosario", "estatuto", "ley universitaria", "tupa", "tesoreria",
        "bienestar universitario", "biblioteca", "creditos", "requisitos", "tramite", "procedimiento",
        "semestre 2026", "cronograma academico", "calendario academico"
    ]

    has_calendar = any(k in norm for k in calendar_keywords) or ("cuando" in norm and "tutoria" in norm and "mi" in norm)
    has_tutor = any(k in norm for k in tutor_keywords) or ("quien" in norm and "tutor" in norm and "mi" in norm) or ("contacto" in norm and "tutor" in norm and "mi" in norm)
    has_students = (user_role == "tutor") and (any(k in norm for k in student_keywords) or ("mis" in norm and "alumnos" in norm))

    has_personal = has_calendar or has_tutor or has_students
    has_doc = any(k in norm for k in documental_keywords) or norm.startswith("que es") or "malla" in norm or "reglamento" in norm or "intercambio" in norm

    if has_personal and has_doc:
        return "MIXED"
    if has_calendar:
        return "PERSONAL_CALENDAR"
    if has_tutor:
        return "PERSONAL_TUTOR"
    if has_students:
        return "PERSONAL_STUDENTS"
    if has_doc:
        return "DOCUMENTAL_UNSAAC"

    return "UNKNOWN"


def is_ambiguous_tutoria_general_followup(user_content: str, history_msgs: list) -> bool:
    norm = _normalize_text_pure(user_content)
    if "tutoria general" in norm:
        if history_msgs:
            for msg in reversed(history_msgs[:-1]):
                role = getattr(msg, "role", "") if hasattr(msg, "role") else (msg.get("role", "") if isinstance(msg, dict) else "")
                content = getattr(msg, "content", "") if hasattr(msg, "content") else (msg.get("content", "") if isinstance(msg, dict) else "")
                if role == "user":
                    prev_norm = _normalize_text_pure(content)
                    if any(k in prev_norm for k in ["proxima", "mi tutor", "mis tutorias", "agenda", "sesion"]):
                        return True
                    break
            if norm == "y tutoria general" or norm == "tutoria general":
                return True
    return False


def extract_malla_state(user_content: str, history_msgs: list) -> dict:
    norm_curr = _normalize_text_pure(user_content)
    norm_curr_sem = re.sub(r"\bciclo\b", "semestre", norm_curr)

    curr_years = re.findall(r"\b(19\d\d|20\d\d)\b", norm_curr)
    curr_plan = curr_years[0] if curr_years else None

    sem_terms = ["semestre", "ciclo", "primer", "segundo", "tercer", "cuarto", "quinto", "sexto", "septimo", "octavo", "noveno", "decimo", "1er", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no", "10mo"]
    has_curr_semester = any(st in norm_curr for st in sem_terms)

    is_standalone_malla = ("malla" in norm_curr or "plan de estudios" in norm_curr) and not curr_plan and not has_curr_semester

    if is_standalone_malla or not history_msgs:
        return {
            "is_new_request": True,
            "active_plan": curr_plan,
            "active_semester": norm_curr_sem if has_curr_semester else None,
            "reconstructed_query": "malla curricular" if not curr_plan else f"malla curricular Plan {curr_plan}"
        }

    recent_history = history_msgs[-6:]
    user_history_msgs = []
    for m in recent_history:
        role = getattr(m, "role", "") if hasattr(m, "role") else (m.get("role", "") if isinstance(m, dict) else "")
        content = getattr(m, "content", "") if hasattr(m, "content") else (m.get("content", "") if isinstance(m, dict) else "")
        if role == "user":
            user_history_msgs.append(content)

    hist_plan = None
    hist_semester = None

    for msg_text in reversed(user_history_msgs[:-1]):
        mnorm = _normalize_text_pure(msg_text)
        years = re.findall(r"\b(19\d\d|20\d\d)\b", mnorm)
        if years and not hist_plan:
            hist_plan = years[0]
        if any(st in mnorm for st in sem_terms) and not hist_semester:
            hist_semester = msg_text
        if ("malla" in mnorm or "plan de estudios" in mnorm) and not years and not any(st in mnorm for st in sem_terms):
            break

    effective_plan = curr_plan or hist_plan

    effective_semester = None
    if has_curr_semester:
        effective_semester = norm_curr_sem
    elif hist_semester:
        effective_semester = _normalize_text_pure(re.sub(r"\bciclo\b", "semestre", hist_semester))

    elements = ["malla curricular"]
    if effective_plan:
        elements.append(f"Plan {effective_plan}")
    if effective_semester:
        elements.append(effective_semester)

    rec_query = " ".join(elements)

    return {
        "is_new_request": False,
        "active_plan": effective_plan,
        "active_semester": effective_semester,
        "reconstructed_query": rec_query
    }


def reconstruct_query(user_content: str, history_msgs: list) -> str:
    norm_curr = _normalize_text_pure(user_content)
    if not history_msgs:
        return user_content

    history_has_malla = False
    for m in history_msgs[-6:]:
        r = getattr(m, "role", "") if hasattr(m, "role") else (m.get("role", "") if isinstance(m, dict) else "")
        c = getattr(m, "content", "") if hasattr(m, "content") else (m.get("content", "") if isinstance(m, dict) else "")
        if "malla" in _normalize_text_pure(c) or "plan" in _normalize_text_pure(c):
            history_has_malla = True
            break

    is_year_digit = bool(re.match(r"^(19\d\d|20\d\d)$", norm_curr.strip()))
    sem_terms = ["semestre", "ciclo", "primer", "segundo", "tercer", "cuarto", "quinto", "sexto", "septimo", "octavo", "noveno", "decimo", "1er", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no", "10mo"]
    has_sem = any(st in norm_curr for st in sem_terms)

    if "malla" in norm_curr or "plan" in norm_curr or is_year_digit or (history_has_malla and (has_sem or is_year_digit)):
        state = extract_malla_state(user_content, history_msgs)
        return state["reconstructed_query"]

    return user_content


def check_malla_ambiguity(retrieved_chunks: list, user_content: str, history_msgs: list, active_plan: str | None = None) -> str | None:
    norm_content = _normalize_text_pure(user_content)
    user_text_history = ""
    if history_msgs:
        for m in history_msgs:
            role = getattr(m, "role", "") if hasattr(m, "role") else (m.get("role", "") if isinstance(m, dict) else "")
            content = getattr(m, "content", "") if hasattr(m, "content") else (m.get("content", "") if isinstance(m, dict) else "")
            if role == "user":
                user_text_history += " " + _normalize_text_pure(content)

    full_user_text = f"{user_text_history} {norm_content}"

    is_malla_query = "malla" in full_user_text or "plan" in full_user_text
    if not is_malla_query:
        return None

    curr_years = re.findall(r"\b(19\d\d|20\d\d)\b", norm_content)
    sem_terms = ["semestre", "ciclo", "primer", "segundo", "tercer", "cuarto", "quinto", "sexto", "septimo", "octavo", "noveno", "decimo", "1er", "2do", "3ro", "4to", "5to", "6to", "7mo", "8vo", "9no", "10mo"]
    has_curr_sem = any(st in norm_content for st in sem_terms)
    is_standalone_new = ("malla" in norm_content or "plan de estudios" in norm_content) and not curr_years and not has_curr_sem

    if is_standalone_new:
        active_plan = None

    if active_plan:
        return None

    detected_plans = set()
    for chunk in retrieved_chunks:
        src = getattr(chunk, "source", "") or ""
        text = getattr(chunk, "text", "") or ""
        years = re.findall(r"\b(19\d\d|20\d\d)\b", f"{src} {text[:150]}")
        for y in years:
            detected_plans.add(y)

    if len(detected_plans) > 1:
        if not is_standalone_new:
            for p in detected_plans:
                if p in full_user_text or f"plan {p}" in full_user_text:
                    return None

        sorted_plans = sorted(detected_plans)
        if len(sorted_plans) == 2:
            plans_str = f"{sorted_plans[0]} y {sorted_plans[1]}"
        else:
            plans_str = ", ".join(sorted_plans[:-1]) + " y " + sorted_plans[-1]

        return f"Encontré los planes de estudios {plans_str}. ¿A cuál pertenece tu malla curricular?"

    return None


def decompose_multi_topic_query(query_text: str) -> list[str]:
    norm = _normalize_text_pure(query_text)
    if "tutoria" in norm and ("intercambio" in norm or "relaciones internacionales" in norm or "ocri" in norm):
        return [
            "reglamento de tutoria universitaria",
            "reglamento de intercambio estudiantil movilidad academica ocri"
        ]
    return [query_text]


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

        # 1. Save user message first
        await self.chat_repo.save_message(conversation.id, "user", user_content)

        # 2. Get conversation history
        history_msgs = await self.chat_repo.get_history(
            conversation.id, limit=HISTORY_WINDOW_MESSAGES
        )

        # 3. Check ambiguous follow-up for "Y tutoría general?"
        if is_ambiguous_tutoria_general_followup(user_content, history_msgs):
            clarification = "¿Te refieres a la definición de tutoría general, al reglamento, al cronograma o a una tutoría programada en tu calendario?"
            assistant_msg = await self.chat_repo.save_message(conversation.id, "assistant", clarification)
            return assistant_msg

        # 4. Context Query Reconstruction
        rag_query = reconstruct_query(user_content, history_msgs)

        # 5. Deterministic Intent Classification (evaluated on reconstructed query)
        intent = classify_intent(rag_query, user_role)

        # 6. DETERMINISTIC PERSONAL ROUTES EXECUTION (0 Gemini, 0 Embeddings, 0 Corpus)
        if intent == "PERSONAL_CALENDAR":
            now = datetime.now()
            start_dt = now - timedelta(days=30)
            end_dt = now + timedelta(days=60)
            cal_data = await self.calendar_repo.get_calendar_events_data(
                user_id=user_id,
                role=user_role,
                start_dt=start_dt,
                end_dt=end_dt
            )
            sessions = cal_data.get("sessions", [])
            events = cal_data.get("events", [])

            if not sessions and not events:
                content = "No tienes tutorías ni eventos programados en tu calendario actualmente. 📅✨"
            else:
                lines = ["Aquí tienes tus actividades programadas: 📅✨\n"]
                for s in sessions:
                    title = s.get("title", "Tutoría")
                    sched = s.get("scheduled_at", "")
                    lines.append(f"* **Tutoría:** {title} - {sched}")
                for ev in events:
                    title = ev.get("title", "Evento")
                    start_val = ev.get("start_date", "")
                    lines.append(f"* **Evento:** {title} - {start_val}")
                content = "\n".join(lines)

            assistant_msg = await self.chat_repo.save_message(conversation.id, "assistant", content)
            return assistant_msg

        elif intent == "PERSONAL_TUTOR":
            if user_role == "estudiante":
                tutors = await self.tutor_assignment_repo.get_assigned_tutors_data(user_id)
                if not tutors:
                    content = "No tienes ningún tutor asignado actualmente en el sistema. 🦖"
                else:
                    lines = ["Tu tutor asignado es: 🦖✨\n"]
                    for t in tutors:
                        name = t.get("tutor_name", "Sin nombre")
                        email = t.get("email", "Sin correo")
                        office = t.get("office", "Cubículo por asignar")
                        spec = t.get("specialty", "Tutoría Académica General")
                        lines.append(f"* **Nombre:** {name}")
                        lines.append(f"* **Correo:** {email}")
                        lines.append(f"* **Oficina/Cubículo:** {office}")
                        lines.append(f"* **Especialidad:** {spec}")
                    content = "\n".join(lines)
            else:
                content = "La consulta de tutor asignado es para estudiantes. 🦖"

            assistant_msg = await self.chat_repo.save_message(conversation.id, "assistant", content)
            return assistant_msg

        elif intent == "PERSONAL_STUDENTS":
            if user_role == "tutor":
                students = await self.tutor_assignment_repo.get_assigned_students_data(user_id)
                if not students:
                    content = "No tienes estudiantes asignados actualmente en el sistema. 🦖"
                else:
                    lines = ["Tus estudiantes asignados son: 🦖✨\n"]
                    for st in students:
                        name = st.get("student_name", "Sin nombre")
                        code = st.get("student_code", "")
                        email = st.get("email", "")
                        lines.append(f"* **Estudiante:** {name} (Código: {code}) - {email}")
                    content = "\n".join(lines)
            else:
                content = "La consulta de estudiantes asignados es para tutores. REX 🦖"

            assistant_msg = await self.chat_repo.save_message(conversation.id, "assistant", content)
            return assistant_msg

        # 7. DOCUMENTAL_UNSAAC, MIXED, UNKNOWN o SOCIAL: respuesta generada por el LLM.
        # SOCIAL (saludos, agradecimientos) no consulta el corpus. El resto si lo hace:
        # una consulta sustantiva sin evidencia documental se abstiene aqui, en codigo,
        # en lugar de delegar la abstencion a una instruccion del prompt.
        retrieved_chunks: list[RetrievedChunkDTO] = []
        seen_texts: set[str] = set()

        if intent != "SOCIAL":
            subtopics = decompose_multi_topic_query(rag_query)
            if len(subtopics) > 1:
                for st in subtopics:
                    st_emb = await self.llm.compute_embedding(st)
                    st_chunks = await self.corpus_repo.search_similar(
                        st_emb,
                        limit=3,
                        query_text=st,
                        max_cosine_distance=self.rag_policy.max_cosine_distance,
                        keyword_fallback_limit=self.rag_policy.keyword_fallback_limit,
                        candidatos_por_rama=self.rag_policy.candidatos_por_rama,
                        rrf_k=self.rag_policy.rrf_k,
                        min_ts_rank=self.rag_policy.min_ts_rank,
                    )
                    for c in st_chunks:
                        if c.text not in seen_texts:
                            seen_texts.add(c.text)
                            retrieved_chunks.append(c)
                            if len(retrieved_chunks) >= self.rag_policy.limit:
                                break
                    if len(retrieved_chunks) >= self.rag_policy.limit:
                        break
            else:
                query_embedding = await self.llm.compute_embedding(rag_query)
                retrieved_chunks = await self.corpus_repo.search_similar(
                    query_embedding,
                    limit=self.rag_policy.limit,
                    query_text=rag_query,
                    max_cosine_distance=self.rag_policy.max_cosine_distance,
                    keyword_fallback_limit=self.rag_policy.keyword_fallback_limit,
                    candidatos_por_rama=self.rag_policy.candidatos_por_rama,
                    rrf_k=self.rag_policy.rrf_k,
                    min_ts_rank=self.rag_policy.min_ts_rank,
                )

            # Check plan ambiguity for malla curricular queries
            malla_state = extract_malla_state(user_content, history_msgs)
            malla_clarification = check_malla_ambiguity(
                retrieved_chunks,
                user_content,
                history_msgs,
                active_plan=malla_state.get("active_plan")
            )
            if malla_clarification:
                assistant_msg = await self.chat_repo.save_message(conversation.id, "assistant", malla_clarification)
                return assistant_msg

            # Corte de abstencion: sin fragmentos del corpus no se invoca al LLM, de modo que
            # no pueda responder una consulta institucional desde su conocimiento propio.
            if not retrieved_chunks:
                logger.info(
                    "Abstencion por falta de evidencia documental (intent=%s)", intent
                )
                assistant_msg = await self.chat_repo.save_message(
                    conversation.id, "assistant", ABSTENTION_MESSAGE
                )
                return assistant_msg

        if retrieved_chunks:
            context_parts = []
            for chunk in retrieved_chunks:
                src = chunk.source or "Desconocido"
                context_parts.append(f"[Fuente: {src}]\n{chunk.text}")
            corpus_context = "\n\n".join(context_parts)
        else:
            corpus_context = "NO HAY FRAGMENTOS RELEVANTES DEL CORPUS PARA ESTA CONSULTA."

        history = []
        for msg in history_msgs:
            if msg.id == history_msgs[-1].id and msg.role == "user":
                continue
            role_map = "user" if msg.role == "user" else "model"
            history.append({
                "role": role_map,
                "parts": [{"text": msg.content}]
            })

        system_instruction = (
            "Eres TutorIA, el tutor académico inteligente de la universidad UNSAAC. Te presentas como un amigable dinosaurio morado. "
            "Tu objetivo es ayudar a los estudiantes y tutores con sus consultas académicas, planes de estudio, reglamentos universitarios, "
            "técnicas de estudio y gestión de sus horarios.\n"
            "Mantén un tono entusiasta, paciente y amigable, pero sé conciso, directo y profesional.\n\n"
            f"La fecha y hora actual del servidor es: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n\n"
            "REGLAS OBLIGATORIAS DE GROUNDING Y ABSTENCIÓN DOCUMENTAL:\n"
            "1. No inventes normas, fechas, procedimientos, autoridades o requisitos institucionales de la UNSAAC.\n"
            "2. No presentes como oficial una afirmación que no aparezca en los fragmentos del corpus.\n"
            "3. Si la consulta incluye varios temas (multi-tema) y solo hay evidencia suficiente para uno de ellos, responde detalladamente la parte respaldada e indica específicamente qué tema no pudo ser confirmado por falta de información en la base oficial.\n"
            "4. Si el contexto del corpus no permite responder la consulta sobre la UNSAAC con certeza, debes responder exactamente:\n"
            "   'No cuento con información suficiente en la base oficial de la UNSAAC para responder con certeza.'\n\n"
            "Aquí tienes fragmentos de la base de datos oficial (corpus) de la universidad UNSAAC:\n"
            f"{corpus_context}\n\n"
            "REGLAS OBLIGATORIAS DE FORMATO Y CONCISIÓN:\n"
            "1. Sé conciso y ve al grano inmediatamente. Evita introducciones largas.\n"
            "2. Utiliza un máximo de 2 emojis en todo el mensaje.\n"
            "3. Utiliza negrita (`**`) únicamente para destacar datos críticos.\n"
            "4. Resume las respuestas en máximo 1 o 2 párrafos cortos y precisos."
        )

        assistant_content = await self.llm.generate_response(
            system_instruction=system_instruction,
            history=history,
            user_message=user_content,
            tools=None
        )

        assistant_msg = await self.chat_repo.save_message(conversation.id, "assistant", assistant_content)
        return assistant_msg
