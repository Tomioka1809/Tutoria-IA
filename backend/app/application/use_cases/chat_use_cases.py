from typing import List, Dict
from app.application.ports.repository_ports import ChatRepositoryPort, CorpusRepositoryPort
from app.application.ports.llm_port import LLMPort

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

    async def get_or_create_conversation(self, student_id: int):
        return await self.chat_repo.get_or_create_conversation(student_id)

    async def send_chat_message(self, student_id: int, user_content: str):
        conversation = await self.chat_repo.get_or_create_conversation(student_id)
        
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
            "INSTRUCCIONES IMPORTANTES DE RESPUESTA:\n"
            "1. Intenta responder a la consulta del estudiante utilizando la información de la base de datos oficial (corpus) anterior.\n"
            "2. Si la respuesta NO se encuentra en la base de datos oficial anterior, debes responder utilizando tus conocimientos generales.\n"
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
