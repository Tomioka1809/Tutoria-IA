import asyncio
import json
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.models.corpus_chunk import CorpusChunk
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter
from app.infrastructure.config.config import settings
from app.infrastructure.database.models.motivational_quote import MotivationalQuote

def dict_to_text(d):
    parts = []
    for k, v in d.items():
        if isinstance(v, list):
            # If list of strings
            if all(isinstance(x, str) for x in v):
                parts.append(f"{k}: {', '.join(v)}")
            else:
                parts.append(f"{k}: {v}")
        elif isinstance(v, dict):
            parts.append(f"{k}: {dict_to_text(v)}")
        else:
            parts.append(f"{k}: {v}")
    return ". ".join(parts)

async def seed_database():
    print("Starting database seeding for pgvector RAG...")
    
    corpus_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
        "corpus"
    )
    
    if not os.path.exists(corpus_dir):
        print(f"Error: {corpus_dir} not found.")
        return

    # Initialize Gemini Adapter for embeddings
    llm = GeminiAdapter(api_key=settings.GEMINI_API_KEY)
    
    chunks_to_insert = []
    
    for filename in os.listdir(corpus_dir):
        if not filename.endswith(".json"):
            continue
            
        filepath = os.path.join(corpus_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading {filename}. Skipping.")
                continue
                
            if isinstance(data, list):
                # Array of objects
                for item in data:
                    if not isinstance(item, dict): continue
                    
                    if "pregunta" in item and "respuesta" in item:
                        text = f"Pregunta: {item['pregunta']} Respuesta: {item['respuesta']}"
                    elif "termino" in item and "definicion" in item:
                        text = f"Glosario - {item['termino']}: {item['definicion']}"
                    else:
                        text = dict_to_text(item)
                        
                    source = item.get("fuente", filename)
                    chunks_to_insert.append({"source": source, "text": text})
                    
            elif isinstance(data, dict):
                # Dictionary containing different sections
                general_info = []
                for k in ["universidad", "nombre_completo", "reglamento", "organo_responsable", "documento"]:
                    if k in data:
                        general_info.append(f"{k}: {data[k]}")
                if "base_legal" in data and isinstance(data["base_legal"], list):
                    general_info.append(f"base legal: {', '.join(data['base_legal'])}")
                
                if general_info:
                    chunks_to_insert.append({"source": filename, "text": ". ".join(general_info)})
                
                for key, value in data.items():
                    if key in ["universidad", "nombre_completo", "reglamento", "organo_responsable", "documento", "base_legal"]:
                        continue
                        
                    if isinstance(value, list):
                        if len(value) > 0 and isinstance(value[0], dict):
                            for item in value:
                                if "pregunta" in item and "respuesta" in item:
                                    text = f"Pregunta: {item['pregunta']} Respuesta: {item['respuesta']}"
                                elif "termino" in item and "definicion" in item:
                                    text = f"Glosario - {item['termino']}: {item['definicion']}"
                                else:
                                    text = f"{key}: {dict_to_text(item)}"
                                source = item.get("fuente", filename)
                                chunks_to_insert.append({"source": source, "text": text})
                        else:
                            text = f"{key}: {', '.join(str(v) for v in value)}"
                            chunks_to_insert.append({"source": filename, "text": text})
                            
                    elif isinstance(value, dict):
                        # Chunk each sub-section if it's large, or the whole dict
                        # Since it could be deeply nested, dict_to_text helps flatten it
                        text = f"{key}: {dict_to_text(value)}"
                        chunks_to_insert.append({"source": filename, "text": text})
                        
                    else:
                        text = f"{key}: {value}"
                        chunks_to_insert.append({"source": filename, "text": text})

    async with SessionLocal() as db:
        # Check if already seeded - maybe we want to drop or ignore
        # Since we modified the seed, we might want to allow re-seeding or just check as before
        result = await db.execute(select(CorpusChunk).limit(1))
        if result.scalars().first():
            print("Database is already seeded. If you want to re-seed, drop the tables first.")
            return

        print(f"Generating embeddings for {len(chunks_to_insert)} chunks...")
        for i, chunk_data in enumerate(chunks_to_insert):
            text = chunk_data["text"]
            source = chunk_data["source"]
            print(f"Processing chunk {i+1}/{len(chunks_to_insert)}...")
            
            # Compute embedding
            try:
                embedding = await llm.compute_embedding(text)
                await asyncio.sleep(0.8)  # Prevent hitting Gemini API 429 rate limit (100 requests/min)
            except Exception as e:
                print(f"Failed to compute embedding for chunk: {e}")
                continue
            
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
