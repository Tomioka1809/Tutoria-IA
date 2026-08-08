"""Fase 3 - Calibra el umbral de distancia coseno contra el golden set.

max_cosine_distance estaba fijo en 0.45 sin evidencia detras. Una medicion en
vivo mostro que con ese valor una consulta fuera de alcance ("receta del cuy
chactado") recupera fragmentos y por lo tanto rompe la abstencion: el LLM recibe
contexto irrelevante en vez de que el caso de uso corte antes.

El script embebe cada pregunta del golden set, mide la distancia al fragmento mas
cercano y barre umbrales, reportando la tension real:

- recall en alcance: consultas respaldadas que SI recuperan algo;
- falsos positivos fuera de alcance: consultas que deberian abstenerse y no lo hacen.

El umbral recomendado es el mayor que mantiene los falsos positivos en cero.

Uso:
    python -m scripts.calibrar_umbral --set v2
"""
import argparse
import asyncio
import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import select  # noqa: E402

import app.infrastructure.database.base  # noqa: F401,E402
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter  # noqa: E402
from app.infrastructure.config.config import settings  # noqa: E402
from app.infrastructure.database.models.corpus_chunk import CorpusChunk  # noqa: E402
from app.infrastructure.database.session import SessionLocal  # noqa: E402
from scripts.audit_corpus_coverage import cargar_casos  # noqa: E402

FUERA_DE_ALCANCE = "NO_APLICA"
UMBRALES = [round(0.20 + 0.01 * i, 2) for i in range(31)]  # 0.20 a 0.50


async def medir(casos: list[dict]) -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
    """Devuelve (en_alcance, fuera_de_alcance) como [(id, distancia_minima)]."""
    if not settings.GEMINI_API_KEY:
        raise SystemExit("Falta GEMINI_API_KEY.")

    llm = GeminiAdapter(api_key=settings.GEMINI_API_KEY, allow_embedding_fallback=False)
    en_alcance: list[tuple[int, float]] = []
    fuera: list[tuple[int, float]] = []

    async with SessionLocal() as db:
        total = (await db.execute(select(CorpusChunk).limit(1))).scalars().first()
        if total is None:
            raise SystemExit("El corpus no tiene chunks indexados; corre antes ingest_corpus.")

        for caso in casos:
            # Las preguntas pendientes de documento no miden el umbral: su
            # documento fuente todavia no esta en el corpus.
            if caso.get("estado") == "pendiente_documento":
                continue

            citas = [str(a) for a in caso.get("articulos_referencia", [])]
            es_fuera = any(FUERA_DE_ALCANCE in c.upper() for c in citas)

            embedding = await llm.compute_embedding(caso["pregunta"])
            distancia = CorpusChunk.embedding.cosine_distance(embedding).label("d")
            res = await db.execute(
                select(distancia)
                .where(CorpusChunk.embedding.is_not(None))
                .order_by(distancia)
                .limit(1)
            )
            fila = res.first()
            if fila is None:
                continue

            par = (caso["id"], round(float(fila[0]), 4))
            (fuera if es_fuera else en_alcance).append(par)

    return en_alcance, fuera


def informar(en_alcance, fuera) -> float | None:
    print("=" * 72)
    print("CALIBRACION DEL UMBRAL DE DISTANCIA COSENO")
    print("=" * 72)

    if en_alcance:
        d = sorted(x[1] for x in en_alcance)
        print(f"\n  En alcance ({len(d)} casos)      min={d[0]}  mediana={d[len(d)//2]}  max={d[-1]}")
    if fuera:
        d = sorted(x[1] for x in fuera)
        print(f"  Fuera de alcance ({len(d)} casos) min={d[0]}  mediana={d[len(d)//2]}  max={d[-1]}")

    print(f"\n{'umbral':>7} {'recall en alcance':>18} {'falsos positivos':>18}")
    print("-" * 48)

    recomendado = None
    for u in UMBRALES:
        aciertos = sum(1 for _, dist in en_alcance if dist <= u)
        falsos = sum(1 for _, dist in fuera if dist <= u)
        recall = aciertos / len(en_alcance) if en_alcance else 0.0
        marca = ""
        if falsos == 0 and (recomendado is None or recall >= recomendado[1]):
            recomendado = (u, recall)
            marca = "  <-"
        print(f"{u:>7.2f} {recall:>17.0%} {falsos:>18}{marca}")

    if recomendado:
        print(f"\n  RECOMENDADO: max_cosine_distance = {recomendado[0]}")
        print(f"  Mantiene {recomendado[1]:.0%} de recall en alcance sin falsos positivos.")
        return recomendado[0]

    print("\n  No hay umbral que separe ambos grupos: revisar el corpus o el golden set.")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibra el umbral de distancia coseno")
    parser.add_argument("--set", dest="conjunto", default="v2")
    parser.add_argument("--json", dest="salida")
    args = parser.parse_args()

    casos = cargar_casos(args.conjunto)
    en_alcance, fuera = asyncio.run(medir(casos))
    recomendado = informar(en_alcance, fuera)

    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "golden_set": args.conjunto,
                    "umbral_recomendado": recomendado,
                    "en_alcance": en_alcance,
                    "fuera_de_alcance": fuera,
                },
                fh, ensure_ascii=False, indent=2,
            )
        print(f"\n  Informe guardado en {args.salida}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
