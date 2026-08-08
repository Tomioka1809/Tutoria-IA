"""add_fragment_identity_to_corpus_chunks

Da identidad estable y procedencia citable a cada chunk, para que la ingesta
pueda ser incremental: sin fragment_id y content_hash hay que borrar y reembeber
el corpus completo para agregar un solo documento.

Las columnas son nullable porque los chunks ya sembrados con el esquema anterior
no los tienen; la ingesta nueva los completa.

Revision ID: a1c4e7b90d21
Revises: 6f892a019e42
Create Date: 2026-08-02

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1c4e7b90d21'
down_revision = '6f892a019e42'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('corpus_chunks', sa.Column('fragment_id', sa.String(length=255), nullable=True))
    op.add_column('corpus_chunks', sa.Column('content_hash', sa.String(length=64), nullable=True))
    op.add_column('corpus_chunks', sa.Column('documento', sa.String(length=255), nullable=True))
    op.add_column('corpus_chunks', sa.Column('articulo', sa.String(length=32), nullable=True))

    op.create_index('ix_corpus_chunks_fragment_id', 'corpus_chunks', ['fragment_id'], unique=True)
    op.create_index('ix_corpus_chunks_content_hash', 'corpus_chunks', ['content_hash'])


def downgrade() -> None:
    op.drop_index('ix_corpus_chunks_content_hash', table_name='corpus_chunks')
    op.drop_index('ix_corpus_chunks_fragment_id', table_name='corpus_chunks')

    op.drop_column('corpus_chunks', 'articulo')
    op.drop_column('corpus_chunks', 'documento')
    op.drop_column('corpus_chunks', 'content_hash')
    op.drop_column('corpus_chunks', 'fragment_id')
