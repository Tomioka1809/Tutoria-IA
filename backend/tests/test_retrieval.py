import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select

import app.infrastructure.database.base  # noqa
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.repositories.corpus_repository import CorpusRepository
from app.infrastructure.config.config import settings
from app.application.dtos.rag_dtos import RAGRetrievalPolicy, RetrievedChunkDTO

from tests.evaluation_support import (
    EvaluationConfig,
    EvaluationGeminiAdapter,
    execute_with_retry,
    compute_retrieval_metrics,
    sanitize_secret_message,
    InfrastructureError,
    NonRetryableError
)

class RetrievalEvaluator:
    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.cfg = config or EvaluationConfig()
        self.rag_policy = RAGRetrievalPolicy(
            limit=6,
            max_cosine_distance=0.45,
            keyword_fallback_limit=2
        )
        self.llm = EvaluationGeminiAdapter(
            api_key=settings.GEMINI_API_KEY,
            config=self.cfg
        )

    async def evaluate_item(
        self,
        item: Dict[str, Any],
        db,
        config: Optional[EvaluationConfig] = None
    ) -> Dict[str, Any]:
        cfg = config or self.cfg
        question = item["pregunta"]
        expected_refs = item.get("articulos_referencia", [])
        expected_keywords = item.get("palabras_clave_esperadas", [])
        categoria = item["categoria"]

        # 1. Separate embedding generation from PostgreSQL query
        try:
            query_vector = await self.llm.compute_embedding(question)
            embed_attempts = getattr(self.llm, "last_embedding_attempts", 1)
        except (InfrastructureError, NonRetryableError) as e:
            return {
                "id": item["id"],
                "categoria": categoria,
                "pregunta": question,
                "status": "infrastructure_error",
                "attempts": e.attempts,
                "technical_error": e.sanitized_message,
                "retrieved_count": 0,
                "precision": None,
                "cobertura": None,
                "retrieved_samples": []
            }
        except Exception as e:
            err_msg = sanitize_secret_message(str(e))
            return {
                "id": item["id"],
                "categoria": categoria,
                "pregunta": question,
                "status": "infrastructure_error",
                "attempts": getattr(e, "attempts", 1),
                "technical_error": err_msg,
                "retrieved_count": 0,
                "precision": None,
                "cobertura": None,
                "retrieved_samples": []
            }

        # 2. Independent PostgreSQL query retry (does not re-request embedding if DB fails)
        async def _fetch_chunks():
            corpus_repo = CorpusRepository(db)
            chunks = await corpus_repo.search_similar(
                query_vector,
                limit=self.rag_policy.limit,
                query_text=question,
                max_cosine_distance=self.rag_policy.max_cosine_distance,
                keyword_fallback_limit=self.rag_policy.keyword_fallback_limit
            )
            return chunks

        try:
            retrieved_chunks, db_attempts = await execute_with_retry(_fetch_chunks, config=cfg)

            retrieved_texts = []
            if not isinstance(retrieved_chunks, list):
                raise InfrastructureError("CorpusRepository.search_similar no devolvió una lista")

            for chunk in retrieved_chunks:
                if not isinstance(chunk, RetrievedChunkDTO) or not isinstance(chunk.text, str) or not chunk.text.strip():
                    raise InfrastructureError("Elemento devuelto por search_similar no es un RetrievedChunkDTO válido con texto")
                retrieved_texts.append(chunk.text)

            attempts = max(embed_attempts, db_attempts)

        except (InfrastructureError, NonRetryableError) as e:
            total_attempts = max(embed_attempts, e.attempts)
            return {
                "id": item["id"],
                "categoria": categoria,
                "pregunta": question,
                "status": "infrastructure_error",
                "attempts": total_attempts,
                "technical_error": e.sanitized_message,
                "retrieved_count": 0,
                "precision": None,
                "cobertura": None,
                "retrieved_samples": []
            }
        except Exception as e:
            err_msg = sanitize_secret_message(str(e))
            return {
                "id": item["id"],
                "categoria": categoria,
                "pregunta": question,
                "status": "infrastructure_error",
                "attempts": embed_attempts,
                "technical_error": err_msg,
                "retrieved_count": 0,
                "precision": None,
                "cobertura": None,
                "retrieved_samples": []
            }

        precision, cobertura = compute_retrieval_metrics(
            retrieved_chunks=retrieved_texts,
            expected_refs=expected_refs,
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
            "retrieved_count": len(retrieved_texts),
            "precision": precision,
            "cobertura": cobertura,
            "retrieved_samples": [t[:120] + "..." for t in retrieved_texts[:2]]
        }

async def run_retrieval_benchmark(
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
        evaluator = RetrievalEvaluator(config=cfg)
        async with SessionLocal() as db:
            for item in golden_set:
                res = await evaluator.evaluate_item(item, db, config=cfg)
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
                    "retrieved_count": 0,
                    "precision": None,
                    "cobertura": None,
                    "retrieved_samples": []
                })

    return results

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "dataset", "golden_set.json")
    results = asyncio.run(run_retrieval_benchmark(path))
    print(f"Evaluados {len(results)} items de recuperación.")
