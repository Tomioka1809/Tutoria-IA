import asyncio
import json
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models.corpus_chunk import CorpusChunk
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter
from app.infrastructure.config.config import settings

async def seed_database():
    print("Starting database seeding for pgvector RAG...")
    
    corpus_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "corpus.json"
    )
    
    if not os.path.exists(corpus_path):
        print(f"Error: {corpus_path} not found.")
        return

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)

    # Initialize Gemini Adapter for embeddings
    llm = GeminiAdapter(api_key=settings.GEMINI_API_KEY)
    
    # Extract meaningful chunks from corpus.json
    chunks_to_insert = []
    
    # 1. General University Info
    uni_info = f"{corpus_data.get('universidad')} ({corpus_data.get('nombre_completo')}): {corpus_data.get('reglamento')}. Base legal: {', '.join(corpus_data.get('base_legal', []))}"
    chunks_to_insert.append({"source": "informacion_general", "text": uni_info})
    
    # 2. Tutoria Universitaria
    tutoria = corpus_data.get("tutoria_universitaria", {})
    if tutoria:
        chunks_to_insert.append({
            "source": "tutoria_definicion",
            "text": f"Definición de tutoría: {tutoria.get('definicion')} Características: {tutoria.get('caracter')}"
        })
        for tipo in tutoria.get("tipos_de_tutoria", []):
            chunks_to_insert.append({
                "source": "tipo_tutoria",
                "text": f"Tipo de Tutoría {tipo['tipo']}: {tipo['descripcion']}. Dimensiones: {', '.join(tipo['dimensiones'])}"
            })
            
    # 3. Preguntas Frecuentes
    for faq in corpus_data.get("preguntas_frecuentes", []):
        chunks_to_insert.append({
            "source": "faq",
            "text": f"Pregunta: {faq['pregunta']} Respuesta: {faq['respuesta']}"
        })
        
    # 4. Servicios y Glosario
    for key, svc in corpus_data.get("servicios_universitarios", {}).items():
        chunks_to_insert.append({
            "source": f"servicio_{key}",
            "text": f"Servicio {key.replace('_', ' ')}: {svc.get('descripcion')}"
        })

    for term, definition in corpus_data.get("glosario", {}).items():
        chunks_to_insert.append({
            "source": "glosario",
            "text": f"Glosario - {term}: {definition}"
        })

    async with SessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(CorpusChunk).limit(1))
        if result.scalars().first():
            print("Database is already seeded with corpus chunks.")
            return

        print(f"Generating embeddings for {len(chunks_to_insert)} chunks...")
        for i, chunk_data in enumerate(chunks_to_insert):
            text = chunk_data["text"]
            source = chunk_data["source"]
            print(f"Processing chunk {i+1}/{len(chunks_to_insert)}...")
            
            # Compute embedding
            embedding = await llm.compute_embedding(text)
            
            # Save to db
            chunk_db = CorpusChunk(
                source=source,
                text_content=text,
                embedding=embedding
            )
            db.add(chunk_db)
            
        await db.commit()
        print("Database seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_database())
