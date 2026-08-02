"""Fase 0 - Auditoria de cobertura documental del corpus.

Responde una sola pregunta, sin llamar a Gemini y sin tocar la base de datos:
para cada caso del golden set, el texto necesario para responderlo, ¿esta o no
esta en el corpus?

Esto define el techo alcanzable del RAG. Ninguna mejora de chunking, embeddings
o recuperacion puede superar la proporcion de casos cuyo contenido si existe,
asi que este numero debe medirse antes de optimizar la busqueda.

Uso:
    python -m scripts.audit_corpus_coverage
    python -m scripts.audit_corpus_coverage --set historico --json informe.json
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field, asdict
from typing import Any

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

CORPUS_DIR = os.path.join(BACKEND_DIR, "corpus")
DATASET_DIR = os.path.join(BACKEND_DIR, "tests", "dataset")

GOLDEN_SETS = {
    "oficial": "golden_set.json",
    "historico": "golden_set_32_historico.json",
}

# Umbrales de clasificacion sobre la proporcion de palabras clave halladas.
UMBRAL_CUBIERTO = 1.0
UMBRAL_PARCIAL = 0.5

# Marcador que el golden set usa para los casos que deben quedar sin respuesta.
FUERA_DE_ALCANCE = "NO_APLICA"


def normalizar(texto: str) -> str:
    """Replica la normalizacion del recuperador: minusculas, sin tildes, sin puntuacion.

    Debe coincidir con CorpusRepository._normalized_text para que la auditoria mida
    con el mismo criterio que usa la busqueda real.
    """
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto.casefold())
    limpio = "".join(c for c in nfkd if not unicodedata.combining(c))
    limpio = re.sub(r"[^\w\s]", " ", limpio)
    return re.sub(r"\s+", " ", limpio).strip()


@dataclass
class ResultadoCaso:
    id: int
    categoria: str
    pregunta: str
    veredicto: str
    ratio: float
    ratio_corpus: float = 0.0
    mejor_unidad: str = ""
    palabras_halladas: list[str] = field(default_factory=list)
    palabras_faltantes: list[str] = field(default_factory=list)
    documentos_citados: list[str] = field(default_factory=list)
    documentos_ausentes: list[str] = field(default_factory=list)
    articulos_citados: list[str] = field(default_factory=list)


def unidades_semanticas(datos: Any, archivo: str) -> list[tuple[str, str]]:
    """Divide un documento en las unidades que un chunk podria devolver.

    Se usa la seccion de primer nivel como unidad. Es una aproximacion generosa:
    si las palabras clave de un caso no co-ocurren ni siquiera dentro de una
    seccion entera, ningun fragmento mas pequeno podra responderlo.
    """
    unidades: list[tuple[str, str]] = []
    if isinstance(datos, dict):
        for clave, valor in datos.items():
            unidades.append((f"{archivo}#{clave}", json.dumps(valor, ensure_ascii=False)))
    elif isinstance(datos, list):
        for i, item in enumerate(datos):
            unidades.append((f"{archivo}[{i}]", json.dumps(item, ensure_ascii=False)))
    return unidades


def cargar_corpus() -> tuple[str, list[tuple[str, str]], dict[str, str]]:
    """Devuelve (texto_global_normalizado, unidades_normalizadas, titulos)."""
    if not os.path.isdir(CORPUS_DIR):
        raise SystemExit(f"No existe el directorio de corpus: {CORPUS_DIR}")

    partes: list[str] = []
    unidades: list[tuple[str, str]] = []
    titulos: dict[str, str] = {}

    for nombre in sorted(os.listdir(CORPUS_DIR)):
        if not nombre.endswith(".json"):
            continue
        ruta = os.path.join(CORPUS_DIR, nombre)
        with open(ruta, encoding="utf-8") as fh:
            datos = json.load(fh)

        partes.append(json.dumps(datos, ensure_ascii=False))
        for etiqueta, texto in unidades_semanticas(datos, nombre):
            unidades.append((etiqueta, normalizar(texto)))

        if isinstance(datos, dict):
            titulo = (
                datos.get("reglamento")
                or datos.get("documento")
                or datos.get("nombre_completo")
                or nombre
            )
        else:
            titulo = nombre
        titulos[nombre] = str(titulo)

    return normalizar(" ".join(partes)), unidades, titulos


def documento_presente(cita: str, titulos: dict[str, str]) -> bool:
    """Heuristica de correspondencia entre un documento citado y los del corpus.

    Se exige coincidencia de terminos significativos porque las citas del golden set
    y los titulos del corpus no usan la misma redaccion literal.
    """
    cita_norm = normalizar(cita)
    terminos = {t for t in cita_norm.split() if len(t) >= 5}
    if not terminos:
        return False

    for archivo, titulo in titulos.items():
        objetivo = normalizar(f"{archivo} {titulo}")
        coincidencias = sum(1 for t in terminos if t in objetivo)
        if coincidencias / len(terminos) >= 0.4:
            return True
    return False


def auditar_caso(
    caso: dict[str, Any],
    corpus_norm: str,
    unidades: list[tuple[str, str]],
    titulos: dict[str, str],
) -> ResultadoCaso:
    palabras = [str(p) for p in caso.get("palabras_clave_esperadas", [])]
    citas = [str(a) for a in caso.get("articulos_referencia", [])]

    base = ResultadoCaso(
        id=caso.get("id", -1),
        categoria=caso.get("categoria", "?"),
        pregunta=caso.get("pregunta", ""),
        veredicto="",
        ratio=0.0,
    )

    # Los casos fuera de alcance no se miden por cobertura: sus palabras clave
    # provienen del mensaje de rechazo esperado ("no tengo esa informacion"), no de
    # contenido del corpus, asi que compararlas contra el corpus no dice nada.
    if any(FUERA_DE_ALCANCE in c.upper() for c in citas):
        base.veredicto = "FUERA_DE_ALCANCE"
        return base

    # Cobertura global: la palabra aparece en algun lugar del corpus. Es una cota
    # superior optimista, porque puede aparecer en un contexto que no responde nada.
    halladas_global = [p for p in palabras if normalizar(p) in corpus_norm]
    ratio_corpus = len(halladas_global) / len(palabras) if palabras else 0.0

    # Cobertura real: cuantas palabras co-ocurren dentro de UNA MISMA unidad. Esto
    # modela lo que un fragmento recuperado puede efectivamente entregar al LLM.
    mejor_ratio, mejor_unidad, mejor_halladas = 0.0, "", []
    for etiqueta, texto in unidades:
        halladas = [p for p in palabras if normalizar(p) in texto]
        ratio = len(halladas) / len(palabras) if palabras else 0.0
        if ratio > mejor_ratio:
            mejor_ratio, mejor_unidad, mejor_halladas = ratio, etiqueta, halladas

    faltantes = [p for p in palabras if p not in mejor_halladas]

    if mejor_ratio >= UMBRAL_CUBIERTO:
        veredicto = "CUBIERTO"
    elif mejor_ratio >= UMBRAL_PARCIAL:
        veredicto = "PARCIAL"
    else:
        veredicto = "AUSENTE"

    base.veredicto = veredicto
    base.ratio = round(mejor_ratio, 4)
    base.ratio_corpus = round(ratio_corpus, 4)
    base.mejor_unidad = mejor_unidad
    base.palabras_halladas = mejor_halladas
    base.palabras_faltantes = faltantes
    base.documentos_citados = citas
    base.documentos_ausentes = [c for c in citas if not documento_presente(c, titulos)]
    base.articulos_citados = [c for c in citas if re.search(r"\bart\.?\s*\d+", c, re.IGNORECASE)]
    return base


def cargar_casos(nombre_set: str) -> list[dict[str, Any]]:
    ruta = os.path.join(DATASET_DIR, GOLDEN_SETS[nombre_set])
    with open(ruta, encoding="utf-8") as fh:
        datos = json.load(fh)
    if isinstance(datos, list):
        return datos
    for valor in datos.values():
        if isinstance(valor, list):
            return valor
    raise SystemExit(f"No se encontro una lista de casos en {ruta}")


def imprimir_informe(resultados: list[ResultadoCaso], titulos: dict[str, str]) -> dict[str, Any]:
    en_alcance = [r for r in resultados if r.veredicto != "FUERA_DE_ALCANCE"]
    fuera = [r for r in resultados if r.veredicto == "FUERA_DE_ALCANCE"]

    cubiertos = [r for r in en_alcance if r.veredicto == "CUBIERTO"]
    parciales = [r for r in en_alcance if r.veredicto == "PARCIAL"]
    ausentes = [r for r in en_alcance if r.veredicto == "AUSENTE"]

    print("=" * 78)
    print("FASE 0 - AUDITORIA DE COBERTURA DOCUMENTAL DEL CORPUS")
    print("=" * 78)
    print(f"\nDocumentos en el corpus: {len(titulos)}")
    for archivo, titulo in titulos.items():
        print(f"  - {archivo:44s} {titulo[:60]}")

    print(f"\n{'-' * 78}\nDETALLE POR CASO (en alcance)\n{'-' * 78}")
    print("  'unidad' = las palabras clave co-ocurren en una misma seccion (lo real).")
    print("  'disperso' = aparecen en el corpus pero repartidas (no respondible).\n")
    print(f"{'id':>4} {'categoria':10s} {'veredicto':9s} {'unidad':>7s} {'disperso':>9s}  faltantes")
    for r in sorted(en_alcance, key=lambda x: (x.veredicto, x.id)):
        faltan = ", ".join(r.palabras_faltantes[:3]) or "-"
        print(
            f"{r.id:>4} {r.categoria:10s} {r.veredicto:9s} {r.ratio:>7.0%} {r.ratio_corpus:>9.0%}  {faltan[:38]}"
        )

    dispersos = [r for r in en_alcance if r.ratio_corpus - r.ratio >= 0.34]
    if dispersos:
        print(f"\n{'-' * 78}\nFALSOS POSITIVOS POR DISPERSION\n{'-' * 78}")
        print("  El corpus contiene las palabras, pero en secciones sin relacion entre si.")
        for r in sorted(dispersos, key=lambda x: x.id):
            print(f"  id={r.id:<4} corpus={r.ratio_corpus:.0%} vs unidad={r.ratio:.0%}   mejor: {r.mejor_unidad}")

    if fuera:
        print(f"\n{'-' * 78}\nCASOS FUERA DE ALCANCE\n{'-' * 78}")
        print("  Excluidos de la cobertura: sus palabras clave son del mensaje de rechazo")
        print("  esperado, no contenido del corpus. Miden abstencion, no cobertura.")
        print(f"  ids: {', '.join(str(r.id) for r in sorted(fuera, key=lambda x: x.id))}")

    docs_faltantes: dict[str, list[int]] = {}
    for r in en_alcance:
        for d in r.documentos_ausentes:
            docs_faltantes.setdefault(d, []).append(r.id)

    if docs_faltantes:
        print(f"\n{'-' * 78}\nDOCUMENTOS CITADOS QUE NO EXISTEN EN EL CORPUS\n{'-' * 78}")
        for doc, ids in sorted(docs_faltantes.items()):
            print(f"  ids={str(ids):16s} {doc}")

    pendientes: dict[str, list[str]] = {}
    for r in en_alcance:
        if r.veredicto == "CUBIERTO":
            continue
        doc = r.documentos_citados[0] if r.documentos_citados else "(sin documento citado)"
        for palabra in r.palabras_faltantes:
            pendientes.setdefault(doc, []).append(f"id{r.id}: {palabra}")

    if pendientes:
        print(f"\n{'=' * 78}\nLISTA DE TRABAJO PARA FASE 2 (que extraer de cada documento fuente)\n{'=' * 78}")
        for doc, faltas in sorted(pendientes.items()):
            print(f"\n  {doc}")
            for f in faltas:
                print(f"      - {f}")

    con_articulo = [r for r in en_alcance if r.articulos_citados]
    total = len(en_alcance)
    techo = len(cubiertos) / total if total else 0.0

    print(f"\n{'=' * 78}\nRESUMEN\n{'=' * 78}")
    print(f"  Casos en alcance          : {total}")
    print(f"  CUBIERTO                  : {len(cubiertos)}")
    print(f"  PARCIAL                   : {len(parciales)}")
    print(f"  AUSENTE                   : {len(ausentes)}")
    print(f"\n  TECHO ALCANZABLE DEL RAG  : {techo:.1%}")
    print("  (ningun cambio en chunking, embeddings o recuperacion puede superarlo)")
    print(f"\n  Casos que citan articulado : {len(con_articulo)}/{total}")
    print(f"  Articulos en el corpus     : 0 (el corpus no tiene numeracion de articulos)")

    return {
        "casos_en_alcance": total,
        "cubierto": len(cubiertos),
        "parcial": len(parciales),
        "ausente": len(ausentes),
        "techo_alcanzable": round(techo, 4),
        "casos_que_citan_articulado": len(con_articulo),
        "documentos_citados_ausentes": docs_faltantes,
        "detalle": [asdict(r) for r in resultados],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditoria de cobertura documental del corpus")
    parser.add_argument("--set", dest="conjunto", choices=sorted(GOLDEN_SETS), default="oficial")
    parser.add_argument("--json", dest="salida_json", help="Ruta donde guardar el informe en JSON")
    args = parser.parse_args()

    corpus_norm, unidades, titulos = cargar_corpus()
    casos = cargar_casos(args.conjunto)
    resultados = [auditar_caso(c, corpus_norm, unidades, titulos) for c in casos]
    resumen = imprimir_informe(resultados, titulos)
    resumen["golden_set"] = args.conjunto

    if args.salida_json:
        with open(args.salida_json, "w", encoding="utf-8") as fh:
            json.dump(resumen, fh, ensure_ascii=False, indent=2)
        print(f"\nInforme guardado en {args.salida_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
