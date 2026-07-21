from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.application.ports.repository_ports import CorpusRepositoryPort
from app.infrastructure.database.models.corpus_chunk import CorpusChunk

class CorpusRepository(CorpusRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_similar(self, query_embedding: List[float], limit: int = 5, query_text: str = None) -> List[str]:
        # Perform Cosine distance search using pgvector (<=> operator)
        result = await self.db.execute(
            select(CorpusChunk)
            .order_by(CorpusChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        chunks = result.scalars().all()
        texts = [chunk.text_content for chunk in chunks]

        # Hybrid fallback: if query_text is given, boost precision by text matching
        if query_text and len(query_text.strip()) > 3:
            words = [w.lower() for w in query_text.split() if len(w) > 3]
            if words:
                from sqlalchemy import or_
                conditions = [CorpusChunk.text_content.ilike(f"%{w}%") for w in words[:4]]
                kw_result = await self.db.execute(
                    select(CorpusChunk).where(or_(*conditions)).limit(limit)
                )
                kw_chunks = kw_result.scalars().all()
                for c in kw_chunks:
                    if c.text_content not in texts:
                        texts.insert(0, c.text_content)

        return texts[:limit]

    async def insert_chunk(self, text: str, embedding: List[float], source: str = None):
        chunk = CorpusChunk(
            source=source,
            text_content=text,
            embedding=embedding
        )
        self.db.add(chunk)
        await self.db.commit()
