import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select

import app.infrastructure.database.base  # noqa
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models.user import User
from app.infrastructure.database.repositories.chat_repository import ChatRepository
from app.infrastructure.database.repositories.corpus_repository import CorpusRepository
from app.infrastructure.database.repositories.tutor_assignment_repository import TutorAssignmentRepository
from app.infrastructure.database.repositories.calendar_repository import CalendarRepository
from app.application.use_cases.chat_use_cases import ChatUseCase
from app.application.dtos.rag_dtos import RAGRetrievalPolicy
from app.infrastructure.config.config import settings

from tests.evaluation_support import (
    EvaluationConfig,
    EvaluationGeminiAdapter,
    compute_generation_metrics,
    sanitize_secret_message,
    InfrastructureError,
    NonRetryableError
)

class GenerationEvaluator:
    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.cfg = config or EvaluationConfig()
        self.llm = EvaluationGeminiAdapter(
            api_key=settings.GEMINI_API_KEY,
            config=self.cfg
        )

    async def get_or_create_eval_user(self, db, config: Optional[EvaluationConfig] = None) -> User:
        async def _get_user():
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

        user, _ = await self._get_user_with_retry(_get_user, config=config)
        return user

    async def _get_user_with_retry(self, op, config=None):
        from tests.evaluation_support import execute_with_retry
        return await execute_with_retry(op, config=config or self.cfg)

    async def evaluate_item(
        self,
        item: Dict[str, Any],
        user: User,
        db,
        config: Optional[EvaluationConfig] = None
    ) -> Dict[str, Any]:
        cfg = config or self.cfg
        question = item["pregunta"]
        expected_keywords = item.get("palabras_clave_esperadas", [])
        categoria = item["categoria"]

        # Reset LLM attempt counters before processing case
        if hasattr(self.llm, "reset_attempt_counters"):
            self.llm.reset_attempt_counters()

        try:
            chat_repo = ChatRepository(db)
            corpus_repo = CorpusRepository(db)
            tutor_assignment_repo = TutorAssignmentRepository(db)
            calendar_repo = CalendarRepository(db)

            rag_policy = RAGRetrievalPolicy(
                limit=6,
                max_cosine_distance=0.45,
                keyword_fallback_limit=2
            )

            use_case = ChatUseCase(
                chat_repo=chat_repo,
                corpus_repo=corpus_repo,
                llm=self.llm,
                tutor_assignment_repo=tutor_assignment_repo,
                calendar_repo=calendar_repo,
                rag_policy=rag_policy
            )

            # Non-idempotent operation called EXACTLY ONCE without outer execute_with_retry
            msg = await use_case.send_chat_message(
                user_id=user.id,
                user_role=user.role,
                user_content=question
            )
            bot_response = msg.content
            attempts = max(
                getattr(self.llm, "last_embedding_attempts", 1),
                getattr(self.llm, "last_generation_attempts", 1),
                1
            )
        except (InfrastructureError, NonRetryableError) as e:
            attempts = max(
                e.attempts,
                getattr(self.llm, "last_embedding_attempts", 1),
                getattr(self.llm, "last_generation_attempts", 1),
                1
            )
            return {
                "id": item["id"],
                "categoria": categoria,
                "pregunta": question,
                "status": "infrastructure_error",
                "attempts": attempts,
                "technical_error": e.sanitized_message,
                "bot_response": f"Error al generar respuesta: {e.sanitized_message}",
                "pertinencia": None
            }
        except Exception as e:
            err_msg = sanitize_secret_message(str(e))
            attempts = max(
                getattr(e, "attempts", 1),
                getattr(self.llm, "last_embedding_attempts", 1),
                getattr(self.llm, "last_generation_attempts", 1),
                1
            )
            return {
                "id": item["id"],
                "categoria": categoria,
                "pregunta": question,
                "status": "infrastructure_error",
                "attempts": attempts,
                "technical_error": err_msg,
                "bot_response": f"Error al generar respuesta: {err_msg}",
                "pertinencia": None
            }

        pertinencia = compute_generation_metrics(
            bot_response=bot_response,
            expected_keywords=expected_keywords,
            categoria=categoria
        )

        return {
            "id": item["id"],
            "categoria": categoria,
            "pregunta": question,
            "status": "success",
            "attempts": attempts,
            "technical_error": None,
            "bot_response": bot_response,
            "pertinencia": pertinencia
        }

async def run_generation_benchmark(
    golden_set_path: str,
    config: Optional[EvaluationConfig] = None,
    items: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    cfg = config or EvaluationConfig()
    if items is None:
        with open(golden_set_path, "r", encoding="utf-8") as f:
            golden_set = json.load(f)
    else:
        golden_set = items

    results = []

    try:
        evaluator = GenerationEvaluator(config=cfg)
        async with SessionLocal() as db:
            eval_user = await evaluator.get_or_create_eval_user(db, config=cfg)
            for item in golden_set:
                res = await evaluator.evaluate_item(item, eval_user, db, config=cfg)
                results.append(res)
                if cfg.inter_case_delay > 0:
                    await asyncio.sleep(cfg.inter_case_delay)
    except Exception as exc:
        err_msg = sanitize_secret_message(str(exc))
        attempts = getattr(exc, "attempts", 1)
        already_processed_ids = {r["id"] for r in results}
        for item in golden_set:
            if item["id"] not in already_processed_ids:
                results.append({
                    "id": item["id"],
                    "categoria": item["categoria"],
                    "pregunta": item["pregunta"],
                    "status": "infrastructure_error",
                    "attempts": attempts,
                    "technical_error": err_msg,
                    "bot_response": f"Error al generar respuesta: {err_msg}",
                    "pertinencia": None
                })

    return results

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "dataset", "golden_set.json")
    results = asyncio.run(run_generation_benchmark(path))
    print(f"Evaluados {len(results)} respuestas del LLM.")
