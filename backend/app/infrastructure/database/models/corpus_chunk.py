from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.infrastructure.database.base_class import Base

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
