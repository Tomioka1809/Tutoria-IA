"""Fase 4 - Calibra el peso del reordenamiento por autoridad.

peso_autoridad se fijo en 0.5 porque funcionaba en la consulta con la que se
diagnostico el problema. Es exactamente el mismo error que tenia el umbral de
distancia en 0.45: un valor que anda en un caso y nadie midio en el resto.

El barrido es barato porque cada pregunta se embebe UNA sola vez y despues se
reutiliza para todos los pesos: el reordenamiento opera sobre candidatos ya
recuperados, sin volver a llamar a Gemini. Asi el barrido completo cuesta lo
mismo que una corrida de evaluacion.

Se reportan las tres metricas juntas porque el reordenamiento puede mejorar el
acierto de articulo y a la vez degradar el de documento: subir un articulo muy
autorizado pero de otro documento desplazaria al correcto fuera del limite.

Uso:
    python -m scripts.calibrar_peso_autoridad
    python -m scripts.calibrar_peso_autoridad --json informe.json
"""
import argparse
import asyncio
import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

import app.infrastructure.database.base  # noqa: F401,E402
from app.application.dtos.rag_dtos import RAGRetrievalPolicy  # noqa: E402
from app.application.use_cases.chat_use_cases import detectar_institucion_externa  # noqa: E402
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter  # noqa: E402
from app.infrastructure.config.config import settings  # noqa: E402
from app.infrastructure.database.repositories.corpus_repository import CorpusRepository  # noqa: E402
from app.infrastructure.database.session import SessionLocal  # noqa: E402
from scripts.audit_corpus_coverage import cargar_casos  # noqa: E402
from tests.run_eval_v2 import (  # noqa: E402
    FUERA_DE_ALCANCE,
    documento_coincide,
    partir_cita,
)

PESOS = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.0]


async def preparar_casos(casos: list[dict], llm) -> list[dict]:
    """Embebe cada pregunta una vez y devuelve los casos evaluables.

    Los casos fuera de alcance y los cortados por institucion no participan del
    barrido: su resultado no depende del reordenamiento, que solo cambia el
    orden de candidatos ya recuperados.
    """
    preparados: list[dict] = []
    for caso in casos:
        citas = [str(a) for a in caso.get("articulos_referencia", [])]
        if any(FUERA_DE_ALCANCE in c.upper() for c in citas):
            continue
        if detectar_institucion_externa(caso["pregunta"]):
            continue

        embedding = await llm.compute_embedding(caso["pregunta"])
        esperados = [partir_cita(c) for c in citas]
        preparados.append({
            "id": caso["id"],
            "dominio": caso.get("dominio", "general"),
            "pregunta": caso["pregunta"],
            "embedding": embedding,
            "articulos_esperados": [a for a, _ in esperados if a],
            "documentos_esperados": [d for _, d in esperados],
        })
    return preparados


async def medir_peso(preparados: list[dict], repo, policy: RAGRetrievalPolicy, peso: float) -> dict:
    aciertos_art = evaluables_art = aciertos_doc = 0
    fallos: list[int] = []

    for caso in preparados:
        chunks = await repo.search_similar(
            caso["embedding"],
            limit=policy.limit,
            query_text=caso["pregunta"],
            max_cosine_distance=policy.max_cosine_distance,
            keyword_fallback_limit=policy.keyword_fallback_limit,
            candidatos_por_rama=policy.candidatos_por_rama,
            rrf_k=policy.rrf_k,
            min_ts_rank=policy.min_ts_rank,
            peso_autoridad=peso,
        )

        articulos = {c.articulo for c in chunks if c.articulo}
        documentos = [c.documento for c in chunks]

        if caso["articulos_esperados"]:
            evaluables_art += 1
            if any(a in articulos for a in caso["articulos_esperados"]):
                aciertos_art += 1
            else:
                fallos.append(caso["id"])

        if any(any(documento_coincide(d, r) for r in documentos)
               for d in caso["documentos_esperados"]):
            aciertos_doc += 1

    return {
        "peso": peso,
        "acierto_articulo": round(aciertos_art / evaluables_art, 4) if evaluables_art else None,
        "aciertos_articulo": aciertos_art,
        "evaluables_articulo": evaluables_art,
        "acierto_documento": round(aciertos_doc / len(preparados), 4) if preparados else None,
        "aciertos_documento": aciertos_doc,
        "casos": len(preparados),
        "fallos_articulo": fallos,
    }


def informar(mediciones: list[dict]) -> float | None:
    print("=" * 72)
    print("CALIBRACION DEL PESO DE AUTORIDAD")
    print("=" * 72)
    print(f"\n{'peso':>6} {'articulo':>16} {'documento':>16}   casos que fallan")
    print("-" * 72)

    base_doc = mediciones[0]["aciertos_documento"] if mediciones else 0

    for m in mediciones:
        art = f"{m['aciertos_articulo']}/{m['evaluables_articulo']}"
        doc = f"{m['aciertos_documento']}/{m['casos']}"
        # Una caida en documento significa que el reordenamiento empezo a
        # desplazar al documento correcto fuera del limite.
        alerta = "  (!) documento cae" if m["aciertos_documento"] < base_doc else ""
        fallos = ", ".join(str(x) for x in m["fallos_articulo"][:4]) or "-"
        print(f"{m['peso']:>6.1f} {art:>16} {doc:>16}   {fallos}{alerta}")

    # Se elige el mejor acierto de articulo sin degradar el de documento, y ante
    # empate el peso mas bajo: menos intervencion sobre el ranking original.
    validos = [m for m in mediciones if m["aciertos_documento"] >= base_doc]
    if not validos:
        print("\n  Todo peso degrada el acierto de documento: conviene dejarlo en 0.")
        return 0.0

    mejor = max(validos, key=lambda m: (m["aciertos_articulo"], -m["peso"]))
    print(f"\n  RECOMENDADO: peso_autoridad = {mejor['peso']}")
    print(f"  articulo {mejor['aciertos_articulo']}/{mejor['evaluables_articulo']}, "
          f"documento {mejor['aciertos_documento']}/{mejor['casos']}")

    if mediciones[0]["aciertos_articulo"] == mejor["aciertos_articulo"]:
        print("  ATENCION: el reordenamiento no mejora el acierto frente a peso 0.")
    return mejor["peso"]


async def main() -> int:
    parser = argparse.ArgumentParser(description="Calibra el peso de autoridad")
    parser.add_argument("--set", dest="conjunto", default="v2")
    parser.add_argument("--json", dest="salida")
    args = parser.parse_args()

    if not settings.GEMINI_API_KEY:
        raise SystemExit("Falta GEMINI_API_KEY.")

    casos = [c for c in cargar_casos(args.conjunto) if c.get("estado") != "pendiente_documento"]
    policy = RAGRetrievalPolicy()
    llm = GeminiAdapter(api_key=settings.GEMINI_API_KEY, allow_embedding_fallback=False)

    async with SessionLocal() as db:
        repo = CorpusRepository(db)

        print(f"Embebiendo {len(casos)} preguntas (una sola vez para todo el barrido)...")
        try:
            preparados = await preparar_casos(casos, llm)
        except Exception as exc:
            raise SystemExit(f"No se pudieron preparar los casos: {type(exc).__name__}")

        if not preparados:
            raise SystemExit("No hay casos evaluables.")

        print(f"Barriendo {len(PESOS)} pesos sobre {len(preparados)} casos, sin mas llamadas a Gemini.\n")
        mediciones = [await medir_peso(preparados, repo, policy, p) for p in PESOS]

    recomendado = informar(mediciones)

    if args.salida:
        with open(args.salida, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "golden_set": args.conjunto,
                    "peso_recomendado": recomendado,
                    "peso_actual": policy.peso_autoridad,
                    "mediciones": mediciones,
                },
                fh, ensure_ascii=False, indent=2,
            )
        print(f"\n  Informe guardado en {args.salida}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
