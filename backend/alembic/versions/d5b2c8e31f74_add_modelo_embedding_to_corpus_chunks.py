"""add_modelo_embedding_to_corpus_chunks

Registra con que modelo se genero cada embedding.

Cambiar la API key es inocuo -los vectores viven en la base y no llevan marca de
la cuenta-, pero cambiar el MODELO no lo es: los vectores viejos y los nuevos
quedarian en espacios distintos y las distancias entre unos y otros dejarian de
significar algo. La busqueda se degradaria sin que nada fallara, que es el peor
modo de falla posible.

Sin esta columna no habia forma de detectar la mezcla.

Revision ID: d5b2c8e31f74
Revises: c3a9f1e42b08
Create Date: 2026-08-02

"""
from alembic import op
import sqlalchemy as sa


revision = 'd5b2c8e31f74'
down_revision = 'c3a9f1e42b08'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'corpus_chunks',
        sa.Column('modelo_embedding', sa.String(length=64), nullable=True),
    )
    op.create_index(
        'ix_corpus_chunks_modelo_embedding', 'corpus_chunks', ['modelo_embedding']
    )

    # Los chunks ya sembrados salieron todos de gemini-embedding-2 a 768
    # dimensiones, que es el unico modelo que el adaptador uso hasta ahora.
    op.execute(
        "UPDATE corpus_chunks SET modelo_embedding = 'gemini-embedding-2@768' "
        "WHERE embedding IS NOT NULL AND modelo_embedding IS NULL;"
    )


def downgrade() -> None:
    op.drop_index('ix_corpus_chunks_modelo_embedding', table_name='corpus_chunks')
    op.drop_column('corpus_chunks', 'modelo_embedding')
