import asyncio
import inspect
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.future import select
from sqlalchemy import delete

import app.infrastructure.database.base  # noqa
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.profiles import StudentProfile
from app.infrastructure.database.models.conversation import Conversation
from app.infrastructure.database.models.message import Message
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
    derive_case_eval_identity,
    compute_generation_metrics,
    sanitize_secret_message,
    truncate_technical_error,
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

    async def create_case_eval_user(self, db, case_id: int, config: EvaluationConfig) -> Tuple[User, Dict[str, str]]:
        identity = derive_case_eval_identity(config.run_id, case_id)
        try:
            user = User(
                email=identity["email"],
                password_hash="eval_hash",
                role="estudiante",
                is_active=True
            )
            db.add(user)
            await db.flush()  # 1st flush to obtain user.id

            profile = StudentProfile(
                user_id=user.id,
                full_name=identity["full_name"],
                student_code=identity["student_code"],
                current_semester=5
            )
            db.add(profile)
            await db.flush()  # 2nd flush to validate profile insertion

            await db.commit()  # Single commit for BOTH
            return user, identity
        except Exception as exc:
            try:
                await db.rollback()
            except Exception as rb_exc:
                rb_msg = truncate_technical_error(str(rb_exc))
                exc_msg = truncate_technical_error(str(exc))
                raise InfrastructureError(f"Falla al crear usuario temporal ({exc_msg}); además falló el rollback ({rb_msg})") from exc

            err_msg = truncate_technical_error(str(exc))
            raise InfrastructureError(f"Falla al crear usuario temporal de evaluación: {err_msg}") from exc

    async def cleanup_case_eval_user(
        self,
        db,
        user_id: int,
        run_id: str,
        case_id: int
    ):
        identity = derive_case_eval_identity(run_id, case_id)
        try:
            u_res = await db.execute(select(User).where(User.id == user_id))
            user = u_res.scalars().first() if hasattr(u_res, "scalars") else None

            p_res = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
            profile = p_res.scalars().first() if hasattr(p_res, "scalars") else None

            if (
                not user or
                not profile or
                user.id != user_id or
                user.email != identity["email"] or
                user.role != "estudiante" or
                profile.user_id != user_id or
                profile.student_code != identity["student_code"] or
                profile.full_name != identity["full_name"] or
                not user.email.endswith("@eval.unsaac.edu.pe") or
                not user.email.startswith("eval_temp_")
            ):
                raise InfrastructureError("Limpieza rechazada por fallo de verificación estricta de seguridad")

            conv_res = await db.execute(select(Conversation.id).where(Conversation.student_id == user_id))

            conv_ids = []
            if hasattr(conv_res, "scalars"):
                scalars_obj = conv_res.scalars()
                if inspect.iscoroutine(scalars_obj):
                    scalars_obj = await scalars_obj
                if hasattr(scalars_obj, "all"):
                    conv_ids = scalars_obj.all()
                    if inspect.iscoroutine(conv_ids):
                        conv_ids = await conv_ids

            if conv_ids:
                await db.execute(delete(Message).where(Message.conversation_id.in_(conv_ids)))
                await db.execute(delete(Conversation).where(Conversation.student_id == user_id))

            await db.execute(delete(StudentProfile).where(StudentProfile.user_id == user_id))
            await db.execute(delete(User).where(User.id == user_id))
            await db.commit()

        except Exception as exc:
            try:
                await db.rollback()
            except Exception as rb_exc:
                rb_msg = truncate_technical_error(str(rb_exc))
                exc_msg = truncate_technical_error(str(exc))
                raise InfrastructureError(f"Error de limpieza ({exc_msg}); además falló el rollback ({rb_msg})") from exc

            if isinstance(exc, (InfrastructureError, NonRetryableError)):
                raise exc

            err_msg = truncate_technical_error(str(exc))
            raise InfrastructureError(f"Error de limpieza de aislamiento: {err_msg}") from exc

    async def evaluate_item(
        self,
        item: Dict[str, Any],
        user: Optional[User],
        db,
        config: Optional[EvaluationConfig] = None
    ) -> Dict[str, Any]:
        cfg = config or self.cfg
        case_id = item["id"]
        question = item["pregunta"]
        expected_keywords = item.get("palabras_clave_esperadas", [])
        categoria = item["categoria"]

        # Reset LLM attempt and request counters before processing case
        if hasattr(self.llm, "reset_attempt_counters"):
            self.llm.reset_attempt_counters()

        eval_user = user
        case_identity = None
        created_temp_user = False
        res_dict = None

        try:
            if eval_user is None:
                eval_user, case_identity = await self.create_case_eval_user(db, case_id, cfg)
                created_temp_user = True
            else:
                case_identity = derive_case_eval_identity(cfg.run_id, case_id)

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
                user_id=eval_user.id,
                user_role=eval_user.role,
                user_content=question
            )
            bot_response = msg.content
            attempts = max(
                getattr(self.llm, "last_embedding_attempts", 1),
                getattr(self.llm, "last_generation_attempts", 1),
                1
            )
            emb_req = getattr(self.llm, "embedding_requests", 0)
            gen_req = getattr(self.llm, "generation_requests", 0)

            pertinencia = compute_generation_metrics(
                bot_response=bot_response,
                expected_keywords=expected_keywords,
                categoria=categoria
            )

            res_dict = {
                "id": case_id,
                "categoria": categoria,
                "pregunta": question,
                "status": "success",
                "attempts": attempts,
                "embedding_requests": emb_req,
                "generation_requests": gen_req,
                "technical_error": None,
                "bot_response": bot_response,
                "pertinencia": pertinencia
            }

        except (InfrastructureError, NonRetryableError) as e:
            attempts = max(
                e.attempts,
                getattr(self.llm, "last_embedding_attempts", 1),
                getattr(self.llm, "last_generation_attempts", 1),
                1
            )
            emb_req = getattr(self.llm, "embedding_requests", 0)
            gen_req = getattr(self.llm, "generation_requests", 0)

            res_dict = {
                "id": case_id,
                "categoria": categoria,
                "pregunta": question,
                "status": "infrastructure_error",
                "attempts": attempts,
                "embedding_requests": emb_req,
                "generation_requests": gen_req,
                "technical_error": e.sanitized_message,
                "bot_response": f"Error al generar respuesta: {e.sanitized_message}",
                "pertinencia": None
            }
        except Exception as e:
            err_msg = truncate_technical_error(str(e))
            attempts = max(
                getattr(e, "attempts", 1),
                getattr(self.llm, "last_embedding_attempts", 1),
                getattr(self.llm, "last_generation_attempts", 1),
                1
            )
            emb_req = getattr(self.llm, "embedding_requests", 0)
            gen_req = getattr(self.llm, "generation_requests", 0)

            res_dict = {
                "id": case_id,
                "categoria": categoria,
                "pregunta": question,
                "status": "infrastructure_error",
                "attempts": attempts,
                "embedding_requests": emb_req,
                "generation_requests": gen_req,
                "technical_error": err_msg,
                "bot_response": f"Error al generar respuesta: {err_msg}",
                "pertinencia": None
            }
        finally:
            if created_temp_user and eval_user:
                try:
                    await self.cleanup_case_eval_user(
                        db=db,
                        user_id=eval_user.id,
                        run_id=cfg.run_id,
                        case_id=case_id
                    )
                except Exception as cleanup_exc:
                    clean_msg = truncate_technical_error(str(cleanup_exc))
                    if res_dict is not None:
                        res_dict["status"] = "infrastructure_error"
                        res_dict["technical_error"] = clean_msg
                        res_dict["precision"] = None
                        res_dict["cobertura"] = None
                        res_dict["pertinencia"] = None

        return res_dict

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
            for item in golden_set:
                res = await evaluator.evaluate_item(item, None, db, config=cfg)
                results.append(res)
                if cfg.inter_case_delay > 0:
                    await asyncio.sleep(cfg.inter_case_delay)
    except Exception as exc:
        err_msg = truncate_technical_error(str(exc))
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
                    "embedding_requests": 0,
                    "generation_requests": 0,
                    "technical_error": err_msg,
                    "bot_response": f"Error al generar respuesta: {err_msg}",
                    "pertinencia": None
                })

    return results

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "dataset", "golden_set.json")
    results = asyncio.run(run_generation_benchmark(path))
    print(f"Evaluados {len(results)} respuestas del LLM.")
