import re
import unicodedata
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.application.ports.repository_ports import CorpusRepositoryPort
from app.application.dtos.rag_dtos import RetrievedChunkDTO
from app.infrastructure.database.models.corpus_chunk import CorpusChunk

STOP_WORDS = {
    "como", "para", "sobre", "entre", "hasta", "desde", "donde", "cuando",
    "quien", "cual", "cuales", "esta", "este", "estos", "estas", "tienen",
    "tiene", "hacer", "puedo", "puede", "pueden", "tengo", "unas", "unos",
    "cada", "todo", "todos", "toda", "todas", "otro", "otra", "que", "los",
    "las", "del", "con", "por", "una", "uno", "unos", "unas", "realizar"
}


def _normalized_stopword_key(token: str) -> str:
    nfkd = unicodedata.normalize("NFKD", token.casefold())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


class CorpusRepository(CorpusRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_similar(
        self,
        query_embedding: List[float],
        *,
        limit: int,
        query_text: str | None,
        max_cosine_distance: float,
        keyword_fallback_limit: int,
    ) -> List[RetrievedChunkDTO]:
        candidate_limit = max(limit * 3, limit)
        distance_expr = CorpusChunk.embedding.cosine_distance(query_embedding).label("cosine_distance")

        result = await self.db.execute(
            select(CorpusChunk, distance_expr)
            .where(CorpusChunk.embedding.is_not(None))
            .order_by(distance_expr)
            .limit(candidate_limit)
        )

        rows = result.all()
        retrieved: List[RetrievedChunkDTO] = []
        seen_texts: set[str] = set()

        # max_cosine_distance = 0.45 corresponds to min_similarity >= 0.55 (similarity_threshold)
        for chunk, dist in rows:
            dist_val = float(dist) if dist is not None else None
            if dist_val is not None and dist_val <= max_cosine_distance:
                if chunk.text_content not in seen_texts:
                    seen_texts.add(chunk.text_content)
                    retrieved.append(
                        RetrievedChunkDTO(
                            text=chunk.text_content,
                            source=chunk.source,
                            cosine_distance=dist_val,
                            retrieval_method="vector"
                        )
                    )
                    if len(retrieved) >= limit:
                        break

        # Keyword Fallback if vector results are insufficient
        if len(retrieved) < limit and keyword_fallback_limit > 0 and query_text:
            normalized = query_text.casefold()
            words = re.findall(r"\w+", normalized)

            clean_terms = []
            seen_normalized_terms = set()
            for w in words:
                norm_key = _normalized_stopword_key(w)
                if len(w) >= 4 and norm_key not in STOP_WORDS and norm_key not in seen_normalized_terms:
                    seen_normalized_terms.add(norm_key)
                    clean_terms.append(w)

            terms_to_search = []
            if len(clean_terms) >= 2:
                terms_to_search = clean_terms[:4]
            elif len(clean_terms) == 1 and clean_terms[0].isalpha() and len(clean_terms[0]) >= 6:
                terms_to_search = [clean_terms[0]]

            if terms_to_search:
                conditions = [CorpusChunk.text_content.ilike(f"%{t}%") for t in terms_to_search]
                kw_query = select(CorpusChunk).where(and_(*conditions)).limit(keyword_fallback_limit)
                kw_result = await self.db.execute(kw_query)
                kw_chunks = kw_result.scalars().all()

                kw_added = 0
                for c in kw_chunks:
                    if c.text_content not in seen_texts and len(retrieved) < limit and kw_added < keyword_fallback_limit:
                        seen_texts.add(c.text_content)
                        retrieved.append(
                            RetrievedChunkDTO(
                                text=c.text_content,
                                source=c.source,
                                cosine_distance=None,
                                retrieval_method="keyword"
                            )
                        )
                        kw_added += 1

        return retrieved[:limit]

    async def insert_chunk(self, text: str, embedding: List[float], source: str = None):
        chunk = CorpusChunk(
            source=source,
            text_content=text,
            embedding=embedding
        )
        self.db.add(chunk)
        await self.db.commit()
