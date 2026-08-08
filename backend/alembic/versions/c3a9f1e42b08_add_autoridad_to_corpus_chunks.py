"""add_autoridad_to_corpus_chunks

Jerarquiza las fuentes del corpus.

La evaluacion mostro que los documentos heredados sin procedencia verificable
desplazan al articulado oficial: ante "que oficina se encarga del bienestar", el
Art. 245 del Estatuto -la respuesta correcta- quedaba en la posicion 15 de 20,
detras de cinco fragmentos de parafrasis. Con limit=6 nunca llegaba al LLM.

La similitud semantica sola no distingue una norma citable de un resumen no
verificado que dice algo parecido, asi que la jerarquia tiene que ser un dato
explicito del fragmento.

Revision ID: c3a9f1e42b08
Revises: b2f8d3c15e47
Create Date: 2026-08-02

"""
from alembic import op
import sqlalchemy as sa


revision = 'c3a9f1e42b08'
down_revision = 'b2f8d3c15e47'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 3 = fragmento normativo citable por articulo
    # 2 = documento oficial con resolucion declarada
    # 1 = resto (glosario, preguntas frecuentes, parafrasis heredada)
    op.add_column(
        'corpus_chunks',
        sa.Column('autoridad', sa.SmallInteger(), nullable=False, server_default='1'),
    )
    op.create_index('ix_corpus_chunks_autoridad', 'corpus_chunks', ['autoridad'])


def downgrade() -> None:
    op.drop_index('ix_corpus_chunks_autoridad', table_name='corpus_chunks')
    op.drop_column('corpus_chunks', 'autoridad')
