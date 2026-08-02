"""Fase 3 - Ingesta incremental del corpus estructurado a pgvector.

Reemplaza a seed.py, que borraba corpus_chunks entero y regeneraba todos los
embeddings. Con mas de mil fragmentos eso significa gastar la cuota completa de
Gemini cada vez que se agrega un documento.

Aca cada fragmento tiene identidad estable (fragment_id) y hash de contenido, de
modo que solo se embebe lo que es nuevo o cambio. Agregar un reglamento cuesta
sus propios fragmentos y nada mas.

La otra diferencia importante es que la ingesta es estricta: si Gemini falla, el
proceso se detiene en vez de guardar el pseudo-embedding por hash MD5 del
fallback. Un vector basura almacenado es indistinguible de uno real y degrada la
busqueda en silencio, que es peor que una siembra incompleta y visible.

Uso:
    python -m scripts.ingest_corpus --dry-run
    python -m scripts.ingest_corpus
    python -m scripts.ingest_corpus --forzar     # reembebe todo
"""
import argparse
import asyncio
import hashlib
import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import delete, select  # noqa: E402

import app.infrastructure.database.base  # noqa: F401,E402  registra los modelos
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter  # noqa: E402
from app.infrastructure.config.config import settings  # noqa: E402
from app.infrastructure.database.models.corpus_chunk import CorpusChunk  # noqa: E402
from app.infrastructure.database.session import SessionLocal  # noqa: E402

CORPUS_DIR = os.path.join(BACKEND_DIR, "corpus_estructurado")

# Los fragmentos se indexan como documento; la consulta del usuario se embebe
# como consulta. Ver LLMPort.compute_embedding.
TASK_TYPE_INDEXACION = "RETRIEVAL_DOCUMENT"


def hash_contenido(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def cargar_fragmentos() -> list[dict]:
    """Aplana el corpus estructurado en fragmentos listos para indexar."""
    if not os.path.isdir(CORPUS_DIR):
        raise SystemExit(f"No existe {CORPUS_DIR}. Corre antes los scripts de extraccion.")

    fragmentos: list[dict] = []
    for nombre in sorted(os.listdir(CORPUS_DIR)):
        if not nombre.endswith(".json"):
            continue
        with open(os.path.join(CORPUS_DIR, nombre), encoding="utf-8") as fh:
            datos = json.load(fh)

        procedencia = datos.get("procedencia") or {}
        documento = procedencia.get("documento") or nombre

        for frag in datos.get("fragmentos", []):
            texto = (frag.get("texto") or "").strip()
            if not texto:
                continue
            fragmentos.append({
                "fragment_id": frag["id"],
                "texto": texto,
                "hash": hash_contenido(texto),
                "documento": documento,
                "articulo": frag.get("articulo"),
                "source": nombre.removesuffix(".json"),
            })

    return fragmentos


def clasificar(
    fragmentos: list[dict],
    existentes: dict[str, str],
    forzar: bool = False,
) -> tuple[list[dict], list[dict], list[str]]:
    """Separa los fragmentos en (nuevos, modificados, obsoletos).

    Un fragmento cuyo hash no cambio conserva su embedding: ese es el ahorro que
    permite agregar un documento sin reembeber el corpus entero.
    """
    ids = {f["fragment_id"] for f in fragmentos}

    if forzar:
        return list(fragmentos), [], sorted(set(existentes) - ids)

    nuevos = [f for f in fragmentos if f["fragment_id"] not in existentes]
    modificados = [
        f for f in fragmentos
        if f["fragment_id"] in existentes and existentes[f["fragment_id"]] != f["hash"]
    ]
    obsoletos = sorted(set(existentes) - ids)
    return nuevos, modificados, obsoletos


async def ingestar(dry_run: bool = False, forzar: bool = False, limite: int | None = None) -> int:
    fragmentos = cargar_fragmentos()
    if not fragmentos:
        print("El corpus estructurado no tiene fragmentos.")
        return 1

    ids = {f["fragment_id"] for f in fragmentos}
    if len(ids) != len(fragmentos):
        raise SystemExit("Hay fragment_id duplicados entre documentos; corregir antes de ingestar.")

    async with SessionLocal() as db:
        res = await db.execute(select(CorpusChunk.fragment_id, CorpusChunk.content_hash))
        existentes = {fid: h for fid, h in res.all() if fid}

    nuevos, modificados, obsoletos = clasificar(fragmentos, existentes, forzar=forzar)

    a_embeber = nuevos + modificados
    if limite:
        a_embeber = a_embeber[:limite]

    print("=" * 70)
    print("INGESTA INCREMENTAL DEL CORPUS")
    print("=" * 70)
    print(f"  fragmentos en el corpus : {len(fragmentos)}")
    print(f"  ya indexados            : {len(existentes)}")
    print(f"  nuevos                  : {len(nuevos)}")
    print(f"  modificados             : {len(modificados)}")
    print(f"  obsoletos (se borran)   : {len(obsoletos)}")
    print(f"  embeddings a generar    : {len(a_embeber)}")

    if dry_run:
        print("\n  (dry-run: no se llama a Gemini ni se escribe en la base)")
        return 0

    if not a_embeber and not obsoletos:
        print("\n  Nada que hacer: el indice ya esta al dia.")
        return 0

    if not settings.GEMINI_API_KEY:
        raise SystemExit("Falta GEMINI_API_KEY: la ingesta no puede generar embeddings.")

    # Estricto a proposito: ante un fallo de Gemini se corta en vez de almacenar
    # el pseudo-embedding del fallback, que envenena la busqueda sin dejar rastro.
    llm = GeminiAdapter(api_key=settings.GEMINI_API_KEY, allow_embedding_fallback=False)

    async with SessionLocal() as db:
        if obsoletos:
            await db.execute(delete(CorpusChunk).where(CorpusChunk.fragment_id.in_(obsoletos)))
            await db.commit()
            print(f"\n  Eliminados {len(obsoletos)} fragmentos que ya no estan en el corpus.")

        for i, frag in enumerate(a_embeber, 1):
            embedding = await llm.compute_embedding(frag["texto"], task_type=TASK_TYPE_INDEXACION)

            res = await db.execute(
                select(CorpusChunk).where(CorpusChunk.fragment_id == frag["fragment_id"])
            )
            chunk = res.scalars().first()
            if chunk is None:
                chunk = CorpusChunk(fragment_id=frag["fragment_id"])
                db.add(chunk)

            chunk.text_content = frag["texto"]
            chunk.content_hash = frag["hash"]
            chunk.documento = frag["documento"]
            chunk.articulo = frag["articulo"]
            chunk.source = frag["source"]
            chunk.embedding = embedding

            if i % 25 == 0 or i == len(a_embeber):
                await db.commit()
                print(f"  {i}/{len(a_embeber)} fragmentos indexados")

        await db.commit()

    print("\n  Ingesta completa.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingesta incremental del corpus estructurado")
    parser.add_argument("--dry-run", action="store_true", help="Solo informa que haria")
    parser.add_argument("--forzar", action="store_true", help="Reembebe todo el corpus")
    parser.add_argument("--limite", type=int, help="Procesa como maximo N fragmentos")
    args = parser.parse_args()

    return asyncio.run(ingestar(dry_run=args.dry_run, forzar=args.forzar, limite=args.limite))


if __name__ == "__main__":
    raise SystemExit(main())
