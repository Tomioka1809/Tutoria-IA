from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.application.ports.repository_ports import CorpusRepositoryPort
from app.infrastructure.database.models.corpus_chunk import CorpusChunk

class CorpusRepository(CorpusRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_similar(self, query_embedding: List[float], limit: int = 5) -> List[str]:
        # Perform L2 distance search using pgvector (<-> operator)
        result = await self.db.execute(
            select(CorpusChunk)
            .order_by(CorpusChunk.embedding.l2_distance(query_embedding))
            .limit(limit)
        )
        chunks = result.scalars().all()
        return [chunk.text_content for chunk in chunks]

    async def insert_chunk(self, text: str, embedding: List[float], source: str = None):
        chunk = CorpusChunk(
            source=source,
            text_content=text,
            embedding=embedding
        )
        self.db.add(chunk)
        await self.db.commit()
