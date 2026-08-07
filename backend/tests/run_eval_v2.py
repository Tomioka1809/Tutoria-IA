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

Metricas (definidas en scripts.metricas_rag; ver documentacion/08_metricas_evaluacion.md):

- acierto_articulo   : el articulo esperado esta entre los recuperados
- acierto_documento  : el documento esperado esta entre los recuperados
- cobertura_palabras : proporcion de palabras clave presentes en lo recuperado
- precision/recall/F1@k, MRR, nDCG@k : calidad del ordenamiento
- abstencion         : matriz de confusion de la decision de callarse
- exactitud_citas    : con --con-generacion, si los articulos que nombra la
                       respuesta estaban en el contexto entregado
- latencia           : de la recuperacion, sin el embedding ni la generacion

Los casos en estado pendiente_documento se excluyen: su fuente todavia no esta
en el corpus y contarlos como fallo de recuperacion confundiria una brecha
documental con un problema de busqueda.

Las citas se guardan **en orden de recuperacion**. Antes se guardaban como un
conjunto ordenado alfabeticamente, lo que destruia el rango y hacia imposible
calcular MRR o nDCG a posteriori sobre un informe ya generado.

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
import time
from datetime import datetime, timezone

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

import app.infrastructure.database.base  # noqa: F401,E402
from app.application.dtos.rag_dtos import RAGRetrievalPolicy  # noqa: E402
from app.infrastructure.adapters.gemini_adapter import GeminiAdapter  # noqa: E402
from app.infrastructure.config.config import settings  # noqa: E402
from app.infrastructure.database.repositories.corpus_repository import CorpusRepository  # noqa: E402
from app.application.use_cases.chat_use_cases import detectar_institucion_externa  # noqa: E402
from app.infrastructure.database.session import SessionLocal  # noqa: E402
from scripts.audit_corpus_coverage import cargar_casos  # noqa: E402
from scripts.metricas_rag import (  # noqa: E402
    confusion_abstencion,
    curva_recall_media,
    documento_coincide,
    f1,
    media,
    ndcg_at_k,
    partir_cita,
    percentil,
    posicion_primer_acierto,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    relevancias,
    normalizar,
    techo_precision_at_k,
)

FUERA_DE_ALCANCE = "NO_APLICA"

# Se recupera mas hondo que el limite de produccion para poder calcular las
# curvas @k de una sola pasada. No altera las metricas de titular: la busqueda
# arma la lista completa ordenada y recorta al final (ver search_similar), asi
# que el top-6 de una consulta con limit=20 es identico al de una con limit=6.
K_METRICAS = 20

# "Art. 14", "Artículo 14°", "art 14": como el LLM redacte la cita.
RE_ARTICULO_TEXTO = re.compile(r"\bArt(?:[íi]culo)?\.?\s*(\d{1,3})", re.IGNORECASE)


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

    # El pipeline real corta antes de recuperar cuando la consulta apunta a otra
    # casa de estudios. Sin reproducirlo aca, la evaluacion mide el repositorio y
    # no el sistema, y marca como fallo un caso que en produccion se resuelve.
    institucion = detectar_institucion_externa(caso["pregunta"])
    if institucion:
        return {
            "id": caso["id"],
            "dominio": caso.get("dominio", "general"),
            "categoria": caso.get("categoria"),
            "pregunta": caso["pregunta"],
            "fuera_de_alcance": es_fuera,
            "chunks_recuperados": 0,
            "citas_recuperadas": [],
            "cortado_por_institucion": institucion,
            "abstencion_correcta": es_fuera,
        }

    embedding = await llm.compute_embedding(caso["pregunta"])

    inicio = time.perf_counter()
    chunks = await repo.search_similar(
        embedding,
        limit=K_METRICAS,
        query_text=caso["pregunta"],
        max_cosine_distance=policy.max_cosine_distance,
        keyword_fallback_limit=policy.keyword_fallback_limit,
        candidatos_por_rama=policy.candidatos_por_rama,
        rrf_k=policy.rrf_k,
        min_ts_rank=policy.min_ts_rank,
        peso_autoridad=policy.peso_autoridad,
    )
    latencia_ms = (time.perf_counter() - inicio) * 1000

    # Lo que ve el LLM en produccion es el top-`limit`, no los K_METRICAS que se
    # recuperan para las curvas.
    entregados = chunks[: policy.limit]

    resultado = {
        "id": caso["id"],
        "dominio": caso.get("dominio", "general"),
        "categoria": caso.get("categoria"),
        "pregunta": caso["pregunta"],
        "fuera_de_alcance": es_fuera,
        "chunks_recuperados": len(entregados),
        "latencia_recuperacion_ms": round(latencia_ms, 1),
        # En orden de recuperacion y sin deduplicar: ordenarlas alfabeticamente
        # -como se hacia antes- destruye el rango y con el, MRR y nDCG.
        "citas_recuperadas": [
            f"{c.articulo} - {c.documento}" if c.articulo else (c.documento or "?")
            for c in entregados
        ],
        "distancias": [
            round(c.cosine_distance, 4) if c.cosine_distance is not None else None
            for c in entregados
        ],
    }

    if es_fuera:
        # Correcto es no recuperar nada: asi el caso de uso se abstiene sin
        # depender de que el prompt convenza al LLM de callarse.
        resultado["abstencion_correcta"] = len(entregados) == 0
        return resultado

    esperados = [partir_cita(c) for c in citas]
    con_articulo = [a for a, _ in esperados if a]
    documentos_recuperados = [c.documento for c in entregados]

    # Relevancia estricta: articulo Y documento. La version anterior comparaba
    # el articulo suelto contra el conjunto recuperado, y "Art. 14" existe en
    # casi todos los reglamentos.
    rels = relevancias(entregados, citas)
    resultado["relevancias"] = rels
    resultado["acierto_articulo"] = any(rels) if con_articulo else None
    resultado["acierto_documento"] = any(
        any(documento_coincide(doc, rec) for rec in documentos_recuperados)
        for _, doc in esperados
    )

    # Se conserva el criterio laxo solo para poder informar cuantos casos
    # cambiaron al endurecer la medicion; no entra en ningun promedio.
    articulos_recuperados = {c.articulo for c in entregados if c.articulo}
    resultado["acierto_articulo_laxo"] = (
        any(a in articulos_recuperados for a in con_articulo) if con_articulo else None
    )

    k = policy.limit

    # El conjunto relevante se estima con los K_METRICAS recuperados (pooling):
    # es una cota inferior, porque podrian existir fragmentos relevantes por
    # debajo del rango 20. Contar citas esperadas en su lugar no sirve, porque
    # un articulo largo se parte en varios fragmentos y todos cubren la misma
    # cita.
    rels_hondo = relevancias(chunks, citas)
    total_relevantes = sum(rels_hondo)

    p_at_k = precision_at_k(rels, k)
    r_at_k = recall_at_k(entregados, citas, k)

    resultado["relevantes_en_pool"] = total_relevantes
    resultado["precision_at_k"] = round(p_at_k, 4)
    resultado["techo_precision_at_k"] = round(techo_precision_at_k(total_relevantes, k), 4)
    resultado["recall_at_k"] = round(r_at_k, 4)
    resultado["f1_at_k"] = round(f1(p_at_k, r_at_k), 4)
    resultado["reciprocal_rank"] = round(reciprocal_rank(rels), 4)
    resultado["posicion_primer_acierto"] = posicion_primer_acierto(rels)
    resultado["ndcg_at_k"] = round(ndcg_at_k(rels, total_relevantes, k), 4)

    # Curva de recall: sale gratis porque ya se recuperaron K_METRICAS.
    resultado["recall_por_k"] = {
        str(kk): round(recall_at_k(chunks, citas, kk), 4)
        for kk in range(1, min(K_METRICAS, len(chunks)) + 1)
    }
    resultado["posicion_primer_acierto_hondo"] = posicion_primer_acierto(rels_hondo)

    palabras = [str(p) for p in caso.get("palabras_clave_esperadas", [])]
    texto = normalizar(" ".join(c.text for c in entregados))
    halladas = [p for p in palabras if normalizar(p) in texto]
    resultado["cobertura_palabras"] = round(len(halladas) / len(palabras), 4) if palabras else None
    resultado["palabras_faltantes"] = [p for p in palabras if p not in halladas]

    if generar:
        contexto = "\n\n".join(
            f"[{c.documento or 'Fuente'} {c.articulo or ''}]\n{c.text}" for c in entregados
        )
        resultado["respuesta"] = await llm.generate_response(
            system_instruction=(
                "Eres TutorIA, asistente de la UNSAAC. Responde solo con los fragmentos dados. "
                "Si no alcanzan, di que no cuentas con informacion suficiente.\n\n" + contexto
            ),
            history=[],
            user_message=caso["pregunta"],
        )
        resultado.update(exactitud_de_citas(resultado["respuesta"], entregados))

    return resultado


def exactitud_de_citas(respuesta: str, chunks) -> dict:
    """Que proporcion de los articulos que nombra la respuesta estaba en el contexto.

    Es una comprobacion determinista, sin juez LLM: el sistema responde citando
    articulado, y un numero de articulo inventado es la alucinacion mas costosa
    que puede cometer, porque suena verificable. No mide si la cita sostiene lo
    que se afirma -eso pide faithfulness con juez-, solo si existia entre los
    fragmentos entregados.
    """
    citados = {f"Art. {m}" for m in RE_ARTICULO_TEXTO.findall(respuesta or "")}
    disponibles = {c.articulo for c in chunks if c.articulo}
    if not citados:
        return {"citas_en_respuesta": 0, "citas_soportadas": 0, "exactitud_citas": None}
    soportadas = citados & disponibles
    return {
        "citas_en_respuesta": len(citados),
        "citas_soportadas": len(soportadas),
        "citas_inventadas": sorted(citados - disponibles),
        "exactitud_citas": round(len(soportadas) / len(citados), 4),
    }


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

    # --- Metricas de ranking -------------------------------------------------
    rrs = [r["reciprocal_rank"] for r in en_alcance if "reciprocal_rank" in r]
    ndcgs = [r["ndcg_at_k"] for r in en_alcance if "ndcg_at_k" in r]
    precisiones = [r["precision_at_k"] for r in en_alcance if "precision_at_k" in r]
    techos = [r["techo_precision_at_k"] for r in en_alcance if "techo_precision_at_k" in r]
    recalls = [r["recall_at_k"] for r in en_alcance if "recall_at_k" in r]
    efes = [r["f1_at_k"] for r in en_alcance if "f1_at_k" in r]
    latencias = [r["latencia_recuperacion_ms"] for r in resultados if "latencia_recuperacion_ms" in r]

    # --- Abstencion como clasificador ----------------------------------------
    # Un caso "se abstuvo" si no le llego evidencia, sea porque no se recupero
    # nada o porque la guarda institucional corto antes.
    casos_abstencion = [
        {
            "fuera_de_alcance": r["fuera_de_alcance"],
            "se_abstuvo": r["chunks_recuperados"] == 0 or bool(r.get("cortado_por_institucion")),
        }
        for r in resultados
    ]
    abstencion = confusion_abstencion(casos_abstencion)

    # --- Curva de recall agregada --------------------------------------------
    curva = curva_recall_media(resultados, k_max=K_METRICAS)

    print(f"\n{'-' * 74}\nRECUPERACION (ordenamiento)\n{'-' * 74}")
    print(f"  MRR                   : {media(rrs):.3f}" if rrs else "  MRR: -")
    print(f"  nDCG@{6:<17}: {media(ndcgs):.3f}" if ndcgs else "")
    if precisiones:
        print(f"  Precision@k media     : {media(precisiones):.3f}"
              f"  (techo {media(techos):.3f})")
    if recalls:
        print(f"  Recall@k media        : {media(recalls):.3f}")
        print(f"  F1@k media            : {media(efes):.3f}")

    print(f"\n{'-' * 74}\nABSTENCION COMO CLASIFICADOR (positivo = se abstiene)\n{'-' * 74}")
    print(f"  {'':16s} {'se abstuvo':>12s} {'respondio':>12s}")
    print(f"  {'fuera de alcance':16s} {abstencion['tp']:>12d} {abstencion['fn']:>12d}")
    print(f"  {'en alcance':16s} {abstencion['fp']:>12d} {abstencion['tn']:>12d}")
    print(f"  precision {abstencion['precision']:.3f}   recall {abstencion['recall']:.3f}"
          f"   F1 {abstencion['f1']:.3f}   accuracy {abstencion['accuracy']:.3f}")
    if abstencion["tp"] + abstencion["fn"] < 10:
        print(f"  AVISO: solo {abstencion['tp'] + abstencion['fn']} casos fuera de alcance."
              " El F1 de abstencion no es concluyente con esta muestra.")

    if latencias:
        print(f"\n{'-' * 74}\nLATENCIA DE RECUPERACION (sin generacion)\n{'-' * 74}")
        print(f"  p50 {percentil(latencias, 50):.0f} ms    p95 {percentil(latencias, 95):.0f} ms"
              f"    max {max(latencias):.0f} ms")

    # Al endurecer la relevancia (articulo Y documento) algunos casos que antes
    # se daban por acertados dejan de estarlo. Se informan uno por uno: es un
    # cambio en la medicion, no en el sistema.
    laxos = [
        r for r in en_alcance
        if r.get("acierto_articulo_laxo") and not r.get("acierto_articulo")
    ]
    if laxos:
        print(f"\n{'-' * 74}\nCASOS QUE PERDIA LA MEDICION LAXA\n{'-' * 74}")
        print("  Recuperaban el numero de articulo correcto pero de otro documento.")
        for r in laxos:
            print(f"    id={r['id']:<5} {r['pregunta'][:58]}")

    resumen = {
        "casos_en_alcance": len(en_alcance),
        "acierto_articulo": round(aciertos_art / len(con_art), 4) if con_art else None,
        "acierto_documento": round(aciertos_doc / len(en_alcance), 4) if en_alcance else None,
        "cobertura_palabras_media": round(sum(cobertura) / len(cobertura), 4) if cobertura else None,
        "abstencion_fuera_de_alcance": round(abstenciones / len(fuera), 4) if fuera else None,
        "mrr": round(media(rrs), 4) if rrs else None,
        "ndcg_at_k": round(media(ndcgs), 4) if ndcgs else None,
        "precision_at_k": round(media(precisiones), 4) if precisiones else None,
        "techo_precision_at_k": round(media(techos), 4) if techos else None,
        "recall_at_k": round(media(recalls), 4) if recalls else None,
        "f1_at_k": round(media(efes), 4) if efes else None,
        "abstencion": abstencion,
        "curva_recall_por_k": curva,
        "latencia_recuperacion_ms": {
            "p50": round(percentil(latencias, 50), 1) if latencias else None,
            "p95": round(percentil(latencias, 95), 1) if latencias else None,
            "max": round(max(latencias), 1) if latencias else None,
        },
        "casos_perdidos_por_medicion_estricta": [r["id"] for r in laxos],
    }

    exactitudes = [
        r["exactitud_citas"] for r in en_alcance if r.get("exactitud_citas") is not None
    ]
    if exactitudes:
        resumen["exactitud_citas"] = round(media(exactitudes), 4)
        inventadas = sorted({c for r in en_alcance for c in r.get("citas_inventadas", [])})
        resumen["citas_inventadas"] = inventadas
        print(f"\n{'-' * 74}\nGENERACION\n{'-' * 74}")
        print(f"  Exactitud de citas    : {media(exactitudes):.1%}"
              f"  ({len(exactitudes)} respuestas con articulos citados)")
        if inventadas:
            print(f"  Articulos citados que no estaban en el contexto: {', '.join(inventadas)}")

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
