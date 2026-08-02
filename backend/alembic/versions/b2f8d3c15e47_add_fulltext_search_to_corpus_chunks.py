"""add_fulltext_search_to_corpus_chunks

Agrega busqueda de texto completo en espanol sobre el corpus.

El fallback por palabras clave actual usa LIKE '%termino%' sobre
lower(translate(...)), que no puede aprovechar ningun indice: cada consulta
recorre la tabla entera. Ademas no lematiza, de modo que "matricula" no encuentra
"matricularse".

La columna es generada y siempre almacenada, asi que se mantiene sola al insertar
o actualizar un chunk y no puede quedar desincronizada del texto.

Revision ID: b2f8d3c15e47
Revises: a1c4e7b90d21
Create Date: 2026-08-02

"""
from alembic import op


revision = 'b2f8d3c15e47'
down_revision = 'a1c4e7b90d21'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # El titulo del fragmento (documento > capitulo > articulo) va con mayor peso
    # que el cuerpo: una consulta por "reglamento de tutoria" debe favorecer al
    # documento correcto antes que a una mencion suelta dentro de otro texto.
    op.execute(
        """
        ALTER TABLE corpus_chunks
        ADD COLUMN busqueda_ts tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('spanish', coalesce(documento, '')), 'A') ||
            setweight(to_tsvector('spanish', coalesce(articulo, '')), 'A') ||
            setweight(to_tsvector('spanish', coalesce(text_content, '')), 'B')
        ) STORED;
        """
    )
    op.execute(
        "CREATE INDEX ix_corpus_chunks_busqueda_ts ON corpus_chunks USING GIN (busqueda_ts);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_corpus_chunks_busqueda_ts;")
    op.execute("ALTER TABLE corpus_chunks DROP COLUMN IF EXISTS busqueda_ts;")
