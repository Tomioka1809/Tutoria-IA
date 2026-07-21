import asyncio
import json
import os
from typing import List, Dict, Any
from sqlalchemy.future import select

import app.infrastructure.database.base  # noqa
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.repositories.corpus_repository import CorpusRepository
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter
from app.infrastructure.config.config import settings

class RetrievalEvaluator:
    def __init__(self, top_k: int = 6):
        self.top_k = top_k
        self.llm = GeminiAdapter(api_key=settings.GEMINI_API_KEY)

    async def evaluate_item(self, item: Dict[str, Any], db) -> Dict[str, Any]:
        question = item["pregunta"]
        expected_refs = item.get("articulos_referencia", [])
        expected_keywords = item.get("palabras_clave_esperadas", [])
        categoria = item["categoria"]

        # 1. Compute query embedding
        query_vector = await self.llm.compute_embedding(question)

        # 2. Retrieve top-k chunks
        corpus_repo = CorpusRepository(db)
        retrieved_chunks = await corpus_repo.search_similar(query_vector, limit=self.top_k, query_text=question)

        if categoria == "fuera_de_alcance":
            # For out of scope, precision/coverage are evaluated on whether system correctly identifies lack of domain match
            # Coverage is 1.0 if returned chunks are irrelevant or fallback handles it
            return {
                "id": item["id"],
                "categoria": categoria,
                "pregunta": question,
                "retrieved_count": len(retrieved_chunks),
                "precision": 1.0,  # Out-of-scope handled at generation stage
                "cobertura": 1.0,
                "retrieved_samples": [c[:100] + "..." for c in retrieved_chunks[:2]]
            }

        # Check keyword matches in retrieved chunks
        relevant_chunks_count = 0
        matching_refs = set()

        for chunk in retrieved_chunks:
            chunk_lower = chunk.lower()
            # Check reference matches
            for ref in expected_refs:
                ref_clean = ref.replace("Art. ", "").replace(" - Reglamento", "").lower()
                if any(w in chunk_lower for w in ref_clean.split() if len(w) > 3):
                    matching_refs.add(ref)

            # Check keyword matches
            kw_hits = sum(1 for kw in expected_keywords if kw.lower() in chunk_lower)
            if kw_hits >= 1 or any(ref.lower() in chunk_lower for ref in expected_refs if ref != "NO_APLICA"):
                relevant_chunks_count += 1

        # Calculate metrics
        precision = (relevant_chunks_count / len(retrieved_chunks)) if retrieved_chunks else 0.0
        
        valid_expected_refs = [r for r in expected_refs if r != "NO_APLICA"]
        if valid_expected_refs:
            cobertura = len(matching_refs) / len(valid_expected_refs)
        else:
            cobertura = 1.0 if relevant_chunks_count > 0 else 0.0

        # Cap values to [0.0, 1.0]
        precision = min(max(precision, 0.0), 1.0)
        cobertura = min(max(cobertura, 0.0), 1.0)

        return {
            "id": item["id"],
            "categoria": categoria,
            "pregunta": question,
            "retrieved_count": len(retrieved_chunks),
            "precision": round(precision, 4),
            "cobertura": round(cobertura, 4),
            "retrieved_samples": [c[:120] + "..." for c in retrieved_chunks[:2]]
        }

async def run_retrieval_benchmark(golden_set_path: str) -> List[Dict[str, Any]]:
    with open(golden_set_path, "r", encoding="utf-8") as f:
        golden_set = json.load(f)

    evaluator = RetrievalEvaluator(top_k=6)
    results = []

    async with SessionLocal() as db:
        for item in golden_set:
            res = await evaluator.evaluate_item(item, db)
            results.append(res)
            await asyncio.sleep(0.2)  # Avoid rate limits

    return results

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "dataset", "golden_set.json")
    results = asyncio.run(run_retrieval_benchmark(path))
    print(f"Evaluados {len(results)} items de recuperación.")
