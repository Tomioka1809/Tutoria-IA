"""add_hnsw_index_to_corpus_chunks

Revision ID: 6f892a019e42
Revises: 5c743d05b2cb
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6f892a019e42'
down_revision: Union[str, Sequence[str], None] = '5c743d05b2cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_corpus_chunks_embedding_hnsw
        ON corpus_chunks
        USING hnsw (embedding vector_cosine_ops)
        WHERE embedding IS NOT NULL;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_corpus_chunks_embedding_hnsw;")
