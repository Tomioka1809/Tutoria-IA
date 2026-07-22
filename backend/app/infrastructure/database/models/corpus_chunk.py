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
