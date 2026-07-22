import sys
import os
import argparse
import asyncio
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.infrastructure.config.config import settings
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter
from app.infrastructure.database.models.corpus_chunk import CorpusChunk
from sqlalchemy.future import select

logger = logging.getLogger(__name__)


async def rebuild_corpus_embeddings(dry_run: bool = False) -> int:
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY environment variable is not configured.")

    adapter = GeminiAdapter(api_key=settings.GEMINI_API_KEY, allow_embedding_fallback=False)
    async with SessionLocal() as session:
        try:
            result = await session.execute(select(CorpusChunk))
            chunks = result.scalars().all()
            total_chunks = len(chunks)
            logger.info("Found %d corpus chunks to process.", total_chunks)

            embeddings_to_update = []
            for chunk in chunks:
                new_embedding = await adapter.compute_embedding(chunk.text_content)
                if not new_embedding or len(new_embedding) != 768:
                    raise RuntimeError(f"Failed to generate valid 768-dim embedding for chunk {chunk.id}")
                embeddings_to_update.append((chunk, new_embedding))

            if not dry_run:
                for chunk, new_emb in embeddings_to_update:
                    chunk.embedding = new_emb
                await session.commit()
                logger.info("Successfully rebuilt and committed embeddings for %d chunks.", len(embeddings_to_update))
            else:
                await session.rollback()
                logger.info("[DRY-RUN] Validated embeddings for %d chunks without committing.", len(embeddings_to_update))

            return len(embeddings_to_update)

        except Exception as e:
            await session.rollback()
            logger.error("Error during embedding rebuilding: %s", e)
            raise


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Rebuild corpus embeddings using gemini-embedding-2 (768-dim).")
    parser.add_argument("--dry-run", action="store_true", help="Simulate rebuilding without committing changes to DB.")
    args = parser.parse_args()

    count = asyncio.run(rebuild_corpus_embeddings(dry_run=args.dry_run))
    logger.info("Rebuilt embeddings process finished. Total: %d (dry_run=%s)", count, args.dry_run)


if __name__ == "__main__":
    main()
