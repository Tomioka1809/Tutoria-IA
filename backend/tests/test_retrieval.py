import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.future import select

import app.infrastructure.database.base  # noqa
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.repositories.corpus_repository import CorpusRepository
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter
from app.infrastructure.config.config import settings

from tests.evaluation_support import (
    EvaluationConfig,
    execute_with_retry,
    compute_retrieval_metrics,
    sanitize_secret_message,
    InfrastructureError,
    NonRetryableError
)

class RetrievalEvaluator:
    def __init__(self, top_k: int = 6):
        self.top_k = top_k
        self.llm = GeminiAdapter(api_key=settings.GEMINI_API_KEY)

    async def evaluate_item(
        self,
        item: Dict[str, Any],
        db,
        config: Optional[EvaluationConfig] = None
    ) -> Dict[str, Any]:
        cfg = config or EvaluationConfig()
        question = item["pregunta"]
        expected_refs = item.get("articulos_referencia", [])
        expected_keywords = item.get("palabras_clave_esperadas", [])
        categoria = item["categoria"]

        async def _fetch_chunks():
            query_vector = await self.llm.compute_embedding(question)
            corpus_repo = CorpusRepository(db)
            retrieved_chunks = await corpus_repo.search_similar(query_vector, limit=self.top_k, query_text=question)
            return retrieved_chunks

        try:
            retrieved_chunks, attempts = await execute_with_retry(_fetch_chunks, config=cfg)
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
                "attempts": 1,
                "technical_error": err_msg,
                "retrieved_count": 0,
                "precision": None,
                "cobertura": None,
                "retrieved_samples": []
            }

        precision, cobertura = compute_retrieval_metrics(
            retrieved_chunks=retrieved_chunks,
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
            "retrieved_count": len(retrieved_chunks),
            "precision": precision,
            "cobertura": cobertura,
            "retrieved_samples": [c[:120] + "..." for c in retrieved_chunks[:2]]
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

    evaluator = RetrievalEvaluator(top_k=6)
    results = []

    async with SessionLocal() as db:
        for item in golden_set:
            res = await evaluator.evaluate_item(item, db, config=cfg)
            results.append(res)
            if cfg.inter_case_delay > 0:
                await asyncio.sleep(cfg.inter_case_delay)

    return results

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "dataset", "golden_set.json")
    results = asyncio.run(run_retrieval_benchmark(path))
    print(f"Evaluados {len(results)} items de recuperación.")
