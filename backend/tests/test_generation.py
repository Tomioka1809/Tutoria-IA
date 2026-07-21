import asyncio
import json
import os
from typing import List, Dict, Any
from sqlalchemy.future import select

import app.infrastructure.database.base  # noqa
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models.user import User
from app.infrastructure.database.repositories.chat_repository import ChatRepository
from app.infrastructure.database.repositories.corpus_repository import CorpusRepository
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter
from app.application.use_cases.chat_use_cases import ChatUseCase
from app.infrastructure.config.config import settings

class GenerationEvaluator:
    def __init__(self):
        self.llm = GeminiAdapter(api_key=settings.GEMINI_API_KEY)

    async def get_or_create_eval_user(self, db) -> User:
        result = await db.execute(select(User).where(User.email == "eval_bot@unsaac.edu.pe"))
        user = result.scalars().first()
        if not user:
            user = User(
                email="eval_bot@unsaac.edu.pe",
                password_hash="eval_hash",
                role="estudiante",
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            from app.infrastructure.database.models.profiles import StudentProfile
            profile = StudentProfile(
                user_id=user.id,
                full_name="Usuario Evaluación Paper IEEE",
                student_code="20260001",
                current_semester=5
            )
            db.add(profile)
            await db.commit()
            await db.refresh(user)
        return user

    async def evaluate_item(self, item: Dict[str, Any], user: User, db) -> Dict[str, Any]:
        question = item["pregunta"]
        expected_answer = item["respuesta_esperada"]
        expected_keywords = item.get("palabras_clave_esperadas", [])
        categoria = item["categoria"]

        chat_repo = ChatRepository(db)
        corpus_repo = CorpusRepository(db)
        use_case = ChatUseCase(chat_repo=chat_repo, corpus_repo=corpus_repo, llm=self.llm)

        # Generate response end-to-end
        try:
            msg = await use_case.send_chat_message(user, question, db)
            bot_response = msg.content
        except Exception as e:
            bot_response = f"Error al generar respuesta: {str(e)}"

        bot_response_lower = bot_response.lower()

        # Compute Pertinencia / Faithfulness score (0.0 to 1.0)
        pertinencia = 0.0

        if categoria == "fuera_de_alcance":
            # For out-of-scope, bot MUST state refusal / lack of info in database
            refusal_markers = ["no tengo esa información", "no se encuentra en mi base", "no cuento con esa información", "base de datos de la universidad"]
            has_refusal = any(marker in bot_response_lower for marker in refusal_markers)
            pertinencia = 1.0 if has_refusal else 0.2
        else:
            # Check keyword coverage in generated response
            keyword_hits = sum(1 for kw in expected_keywords if kw.lower() in bot_response_lower)
            kw_ratio = keyword_hits / len(expected_keywords) if expected_keywords else 1.0
            
            # Check non-empty & grounded response
            is_valid_len = len(bot_response) >= 30
            
            pertinencia = (kw_ratio * 0.7) + (0.3 if is_valid_len else 0.0)

        pertinencia = min(max(pertinencia, 0.0), 1.0)

        return {
            "id": item["id"],
            "categoria": categoria,
            "pregunta": question,
            "bot_response": bot_response,
            "pertinencia": round(pertinencia, 4)
        }

async def run_generation_benchmark(golden_set_path: str) -> List[Dict[str, Any]]:
    with open(golden_set_path, "r", encoding="utf-8") as f:
        golden_set = json.load(f)

    evaluator = GenerationEvaluator()
    results = []

    async with SessionLocal() as db:
        eval_user = await evaluator.get_or_create_eval_user(db)
        for item in golden_set:
            res = await evaluator.evaluate_item(item, eval_user, db)
            results.append(res)
            await asyncio.sleep(0.8)  # Rate limit Gemini API

    return results

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "dataset", "golden_set.json")
    results = asyncio.run(run_generation_benchmark(path))
    print(f"Evaluados {len(results)} respuestas del LLM.")
