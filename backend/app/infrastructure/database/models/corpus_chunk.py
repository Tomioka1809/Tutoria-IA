from sqlalchemy import Computed, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.infrastructure.database.base_class import Base

# Expresion de la columna generada. Debe coincidir con la migracion
# b2f8d3c15e47; se declara aqui para que SQLAlchemy sepa que la calcula el motor
# y la excluya de los INSERT y UPDATE.
_EXPRESION_BUSQUEDA = (
    "setweight(to_tsvector('spanish', coalesce(documento, '')), 'A') || "
    "setweight(to_tsvector('spanish', coalesce(articulo, '')), 'A') || "
    "setweight(to_tsvector('spanish', coalesce(text_content, '')), 'B')"
)

class CorpusChunk(Base):
    __tablename__ = "corpus_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=True) # e.g., 'reglamento', 'glosario'
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    # Embeddings configured with output_dimensionality=768.
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=True)

    # Identidad estable del fragmento en el corpus estructurado
    # (p. ej. "reglamento_tutoria#art-14-1"). Permite reingestar de forma
    # incremental: sin esto habria que borrar y reembeber todo el corpus para
    # agregar un solo documento, gastando la cuota completa de Gemini.
    fragment_id: Mapped[str] = mapped_column(String(255), nullable=True, unique=True, index=True)
    # Hash del texto. Si no cambio, el embedding almacenado sigue siendo valido.
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    # Procedencia citable, para que la respuesta pueda referenciar la norma.
    documento: Mapped[str] = mapped_column(String(255), nullable=True)
    articulo: Mapped[str] = mapped_column(String(32), nullable=True)
    # Jerarquia de la fuente. La similitud semantica no distingue una norma
    # citable de una parafrasis no verificada que dice algo parecido, asi que
    # la distincion se guarda como dato del fragmento.
    autoridad: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default="1", index=True
    )
    # Espacio vectorial del que salio el embedding. Mezclar modelos vuelve las
    # distancias incomparables entre si y degrada la busqueda en silencio.
    modelo_embedding: Mapped[str] = mapped_column(String(64), nullable=True, index=True)

    # Indice de texto completo en espanol, con el titulo del fragmento pesado por
    # encima del cuerpo. La calcula Postgres, de modo que no puede quedar
    # desincronizada del texto.
    busqueda_ts: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(_EXPRESION_BUSQUEDA, persisted=True),
        nullable=True,
    )
