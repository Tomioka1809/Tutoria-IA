"""Evaluacion del RAG contra el golden set v2.

El runner anterior mide precision, cobertura y pertinencia con heuristicas
lexicas sobre el corpus heredado, y su golden set esta congelado por hashes en
verify_evaluation_integrity. Este es un runner aparte para el v2.

La diferencia de fondo es que ahora se puede medir el acierto a nivel de
articulo. El golden set siempre pidio "Art. 15 - Reglamento de Tutoria" en
articulos_referencia, pero el corpus era una parafrasis sin articulado y esa
metrica era imposible de satisfacer por construccion. Tras la extraccion desde
los PDF, cada fragmento lleva su documento y su articulo, asi que la cita se
puede verificar.

Metricas:

- acierto_articulo   : el articulo esperado esta entre los recuperados
- acierto_documento  : el documento esperado esta entre los recuperados
- cobertura_palabras : proporcion de palabras clave presentes en lo recuperado
- abstencion         : para fuera de alcance, que NO se recupere nada

Los casos en estado pendiente_documento se excluyen: su fuente todavia no esta
en el corpus y contarlos como fallo de recuperacion confundiria una brecha
documental con un problema de busqueda.

Uso:
    python -m tests.run_eval_v2                    # solo recuperacion (barato)
    python -m tests.run_eval_v2 --con-generacion   # incluye respuestas del LLM
"""
import argparse
import asyncio
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

import app.infrastructure.database.base  # noqa: F401,E402
from app.application.dtos.rag_dtos import RAGRetrievalPolicy  # noqa: E402
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter  # noqa: E402
from app.infrastructure.config.config import settings  # noqa: E402
from app.infrastructure.database.repositories.corpus_repository import CorpusRepository  # noqa: E402
from app.infrastructure.database.session import SessionLocal  # noqa: E402
from scripts.audit_corpus_coverage import cargar_casos  # noqa: E402

FUERA_DE_ALCANCE = "NO_APLICA"
RE_ARTICULO = re.compile(r"Art\.?\s*(\d+)", re.IGNORECASE)


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto).casefold())
    limpio = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", limpio)).strip()


def partir_cita(cita: str) -> tuple[str | None, str]:
    """Separa "Art. 14 num. 2 - Reglamento de Tutoria" en ("Art. 14", documento)."""
    m = RE_ARTICULO.search(cita)
    articulo = f"Art. {m.group(1)}" if m else None
    documento = cita.split("-", 1)[1].strip() if "-" in cita else cita.strip()
    return articulo, documento


def documento_coincide(esperado: str, recuperado: str | None) -> bool:
    """Compara por terminos significativos: las redacciones no son identicas."""
    if not recuperado:
        return False
    terminos = {t for t in normalizar(esperado).split() if len(t) >= 5}
    if not terminos:
        return False
    objetivo = normalizar(recuperado)
    return sum(1 for t in terminos if t in objetivo) / len(terminos) >= 0.5


async def documentos_sin_indexar() -> list[str]:
    """Documentos del corpus que no tienen ni un fragmento en el indice.

    Una ingesta cortada por cuota puede dejar documentos enteros fuera, y
    entonces las metricas miden la ingesta y no la recuperacion.
    """
    from sqlalchemy import distinct, select

    from app.infrastructure.database.models.corpus_chunk import CorpusChunk
    from scripts.ingest_corpus import CORPUS_DIR

    if not os.path.isdir(CORPUS_DIR):
        return []

    esperados = {
        n.removesuffix(".json") for n in os.listdir(CORPUS_DIR) if n.endswith(".json")
    }
    async with SessionLocal() as db:
        res = await db.execute(select(distinct(CorpusChunk.source)))
        indexados = {s for (s,) in res.all() if s}

    return sorted(esperados - indexados)


async def evaluar_caso(caso: dict, llm, repo, policy: RAGRetrievalPolicy, generar: bool) -> dict:
    citas = [str(a) for a in caso.get("articulos_referencia", [])]
    es_fuera = any(FUERA_DE_ALCANCE in c.upper() for c in citas)

    embedding = await llm.compute_embedding(caso["pregunta"])
    chunks = await repo.search_similar(
        embedding,
        limit=policy.limit,
        query_text=caso["pregunta"],
        max_cosine_distance=policy.max_cosine_distance,
        keyword_fallback_limit=policy.keyword_fallback_limit,
        candidatos_por_rama=policy.candidatos_por_rama,
        rrf_k=policy.rrf_k,
        min_ts_rank=policy.min_ts_rank,
    )

    resultado = {
        "id": caso["id"],
        "dominio": caso.get("dominio", "general"),
        "categoria": caso.get("categoria"),
        "pregunta": caso["pregunta"],
        "fuera_de_alcance": es_fuera,
        "chunks_recuperados": len(chunks),
        "citas_recuperadas": sorted({
            f"{c.articulo} - {c.documento}" if c.articulo else (c.documento or "?")
            for c in chunks
        })[:6],
    }

    if es_fuera:
        # Correcto es no recuperar nada: asi el caso de uso se abstiene sin
        # depender de que el prompt convenza al LLM de callarse.
        resultado["abstencion_correcta"] = len(chunks) == 0
        return resultado

    articulos_recuperados = {c.articulo for c in chunks if c.articulo}
    documentos_recuperados = [c.documento for c in chunks]

    esperados = [partir_cita(c) for c in citas]
    con_articulo = [a for a, _ in esperados if a]

    resultado["acierto_articulo"] = (
        any(a in articulos_recuperados for a in con_articulo) if con_articulo else None
    )
    resultado["acierto_documento"] = any(
        any(documento_coincide(doc, rec) for rec in documentos_recuperados)
        for _, doc in esperados
    )

    palabras = [str(p) for p in caso.get("palabras_clave_esperadas", [])]
    texto = normalizar(" ".join(c.text for c in chunks))
    halladas = [p for p in palabras if normalizar(p) in texto]
    resultado["cobertura_palabras"] = round(len(halladas) / len(palabras), 4) if palabras else None
    resultado["palabras_faltantes"] = [p for p in palabras if p not in halladas]

    if generar:
        contexto = "\n\n".join(
            f"[{c.documento or 'Fuente'} {c.articulo or ''}]\n{c.text}" for c in chunks
        )
        resultado["respuesta"] = await llm.generate_response(
            system_instruction=(
                "Eres TutorIA, asistente de la UNSAAC. Responde solo con los fragmentos dados. "
                "Si no alcanzan, di que no cuentas con informacion suficiente.\n\n" + contexto
            ),
            history=[],
            user_message=caso["pregunta"],
        )

    return resultado


def informar(resultados: list[dict]) -> dict:
    en_alcance = [r for r in resultados if not r["fuera_de_alcance"]]
    fuera = [r for r in resultados if r["fuera_de_alcance"]]

    con_art = [r for r in en_alcance if r.get("acierto_articulo") is not None]
    aciertos_art = sum(1 for r in con_art if r["acierto_articulo"])
    aciertos_doc = sum(1 for r in en_alcance if r.get("acierto_documento"))
    cobertura = [r["cobertura_palabras"] for r in en_alcance if r.get("cobertura_palabras") is not None]
    abstenciones = sum(1 for r in fuera if r.get("abstencion_correcta"))

    print("=" * 74)
    print("EVALUACION DEL RAG - GOLDEN SET V2")
    print("=" * 74)
    print(f"\n{'id':>5} {'dominio':22s} {'art':>4} {'doc':>4} {'palabras':>9}  faltantes")
    print("-" * 74)
    for r in sorted(en_alcance, key=lambda x: (x["dominio"], x["id"])):
        art = "-" if r.get("acierto_articulo") is None else ("ok" if r["acierto_articulo"] else "NO")
        doc = "ok" if r.get("acierto_documento") else "NO"
        cob = f"{r['cobertura_palabras']:.0%}" if r.get("cobertura_palabras") is not None else "-"
        faltan = ", ".join(r.get("palabras_faltantes", [])[:2]) or "-"
        print(f"{r['id']:>5} {r['dominio']:22s} {art:>4} {doc:>4} {cob:>9}  {faltan[:24]}")

    print(f"\n{'-' * 74}\nFUERA DE ALCANCE (correcto = no recuperar nada)\n{'-' * 74}")
    for r in sorted(fuera, key=lambda x: x["id"]):
        estado = "abstiene" if r.get("abstencion_correcta") else f"FALLA ({r['chunks_recuperados']} chunks)"
        print(f"{r['id']:>5} {estado}")

    dominios = sorted({r["dominio"] for r in en_alcance})
    print(f"\n{'-' * 74}\nPOR DOMINIO\n{'-' * 74}")
    print(f"{'dominio':22s} {'casos':>6} {'articulo':>9} {'documento':>10}")
    for d in dominios:
        dr = [r for r in en_alcance if r["dominio"] == d]
        dc = [r for r in dr if r.get("acierto_articulo") is not None]
        a = f"{sum(1 for r in dc if r['acierto_articulo'])}/{len(dc)}" if dc else "-"
        doc = f"{sum(1 for r in dr if r.get('acierto_documento'))}/{len(dr)}"
        print(f"{d:22s} {len(dr):>6} {a:>9} {doc:>10}")

    resumen = {
        "casos_en_alcance": len(en_alcance),
        "acierto_articulo": round(aciertos_art / len(con_art), 4) if con_art else None,
        "acierto_documento": round(aciertos_doc / len(en_alcance), 4) if en_alcance else None,
        "cobertura_palabras_media": round(sum(cobertura) / len(cobertura), 4) if cobertura else None,
        "abstencion_fuera_de_alcance": round(abstenciones / len(fuera), 4) if fuera else None,
    }

    print(f"\n{'=' * 74}\nRESUMEN\n{'=' * 74}")
    print(f"  Acierto de articulo   : {aciertos_art}/{len(con_art)}"
          f" ({resumen['acierto_articulo']:.0%})" if con_art else "  Acierto de articulo   : -")
    print(f"  Acierto de documento  : {aciertos_doc}/{len(en_alcance)}"
          f" ({resumen['acierto_documento']:.0%})")
    print(f"  Cobertura de palabras : {resumen['cobertura_palabras_media']:.0%}")
    print(f"  Abstencion correcta   : {abstenciones}/{len(fuera)}")
    return resumen


async def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluacion del RAG contra el golden set v2")
    parser.add_argument("--set", dest="conjunto", default="v2")
    parser.add_argument("--con-generacion", action="store_true")
    parser.add_argument("--json", dest="salida")
    args = parser.parse_args()

    if not settings.GEMINI_API_KEY:
        raise SystemExit("Falta GEMINI_API_KEY.")

    casos = [c for c in cargar_casos(args.conjunto) if c.get("estado") != "pendiente_documento"]
    policy = RAGRetrievalPolicy()
    llm = GeminiAdapter(api_key=settings.GEMINI_API_KEY, allow_embedding_fallback=False)

    sin_indexar = await documentos_sin_indexar()
    if sin_indexar:
        print("=" * 74)
        print("ADVERTENCIA: EL INDICE ESTA INCOMPLETO")
        print("=" * 74)
        print("  Los siguientes documentos no tienen ningun fragmento indexado, asi")
        print("  que un fallo de recuperacion sobre ellos NO indica un problema de")
        print("  busqueda. Completar la ingesta antes de interpretar las metricas:")
        for doc in sin_indexar:
            print(f"    - {doc}")
        print()

    resultados: list[dict] = []
    async with SessionLocal() as db:
        repo = CorpusRepository(db)
        for caso in casos:
            try:
                resultados.append(
                    await evaluar_caso(caso, llm, repo, policy, args.con_generacion)
                )
            except Exception as exc:
                # Un corte de cuota no invalida lo ya medido: se registra y se
                # informa cuantos casos quedaron sin evaluar.
                print(f"  caso {caso['id']}: interrumpido ({type(exc).__name__})")
                break

    if not resultados:
        print("No se evaluo ningun caso.")
        return 1

    resumen = informar(resultados)
    if len(resultados) < len(casos):
        print(f"\n  ATENCION: {len(casos) - len(resultados)} casos sin evaluar (corte de cuota).")

    if args.salida:
        payload = {
            "generado_utc": datetime.now(timezone.utc).isoformat(),
            "golden_set": args.conjunto,
            "politica": policy.model_dump(),
            "casos_evaluados": len(resultados),
            "casos_totales": len(casos),
            "resumen": resumen,
            "detalle": resultados,
        }
        with open(args.salida, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(f"\n  Informe guardado en {args.salida}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
