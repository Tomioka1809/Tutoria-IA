"""Fase 2 - Convierte el calendario academico a fragmentos del corpus.

El calendario solo existe escaneado, asi que la fuente es el Markdown que produce
docling con OCR en espanol (--ocr-engine easyocr --ocr-lang es). El OCR por
defecto de docling usa modelos chinos y pega las palabras
("Matriculadeestudiantesregulares"), de modo que el idioma debe indicarse
explicitamente.

Cada actividad se convierte en una linea "actividad: fechas" y se agrupan por
bloques del calendario, para que una consulta como "cuando me matriculo" caiga
sobre el fragmento correcto.

Uso:
    python -m scripts.extract_calendario --md .../es_ocr/CRONOGRAMA-CV-2026-CU-014-2026C.md
"""
import argparse
import json
import os
import re
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app.application.dtos.corpus_dtos import (  # noqa: E402
    MAX_CARACTERES_TEXTO,
    DocumentoCorpus,
    Fragmento,
    Procedencia,
    TipoDocumento,
)

MESES = "enero|febrero|marzo|abril|mayo|junio|julio|agosto|setiembre|septiembre|octubre|noviembre|diciembre"
RE_FECHA = re.compile(rf"\b(?:{MESES})\b", re.IGNORECASE)
RE_SEPARADOR = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
RE_RUIDO = re.compile(r"^[\W\d]*$")


def celdas(linea: str) -> list[str]:
    if not linea.strip().startswith("|"):
        return []
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def parsear(md: str) -> list[dict]:
    """Devuelve [{actividad, fechas}] a partir de la tabla del calendario."""
    filas: list[dict] = []
    vistas: set[tuple[str, str]] = set()

    for linea in md.splitlines():
        if "data:image" in linea or RE_SEPARADOR.match(linea):
            continue
        cols = celdas(linea)
        if len(cols) < 2:
            continue

        # La ultima columna con nombre de mes es la de fechas; la actividad es la
        # celda de texto mas larga entre las anteriores. docling duplica columnas
        # cuando la tabla trae celdas combinadas, por eso no se indexa por posicion.
        fechas = next((c for c in reversed(cols) if RE_FECHA.search(c)), "")
        if not fechas:
            continue

        candidatas = [c for c in cols if c != fechas and not RE_RUIDO.match(c)]
        if not candidatas:
            continue
        actividad = max(candidatas, key=len)

        actividad = re.sub(r"\s+", " ", actividad).strip()
        fechas = re.sub(r"\s+", " ", fechas).strip()
        if actividad.upper().startswith("NOTA"):
            continue

        clave = (actividad.casefold(), fechas.casefold())
        if clave in vistas:
            continue
        vistas.add(clave)
        filas.append({"actividad": actividad, "fechas": fechas})

    return filas


def construir(filas: list[dict], anio: int, resolucion: str) -> DocumentoCorpus:
    procedencia = Procedencia(
        documento=f"Calendario Académico {anio} UNSAAC",
        tipo=TipoDocumento.CRONOGRAMA,
        resolucion=resolucion,
        anio=anio,
    )

    encabezado = (
        f"Calendario Académico {anio} de la UNSAAC, aprobado por {resolucion}. "
        "Fechas oficiales de actividades académicas."
    )

    fragmentos: list[Fragmento] = []
    bloque: list[str] = []
    indice = 1

    def volcar():
        nonlocal bloque, indice
        if not bloque:
            return
        fragmentos.append(
            Fragmento(
                id=f"calendario_{anio}#bloque-{indice}",
                titulo=f"Calendario Académico {anio} - actividades ({indice})",
                texto=f"{encabezado}\n" + "\n".join(bloque),
                seccion=["calendario_academico", f"bloque_{indice}"],
            )
        )
        bloque = []
        indice += 1

    for fila in filas:
        linea = f"- {fila['actividad']}: {fila['fechas']}."
        largo_actual = len(encabezado) + sum(len(x) + 1 for x in bloque)
        if bloque and largo_actual + len(linea) > MAX_CARACTERES_TEXTO:
            volcar()
        bloque.append(linea)
    volcar()

    return DocumentoCorpus(procedencia=procedencia, fragmentos=fragmentos)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extrae el calendario academico desde Markdown OCR")
    parser.add_argument("--md", required=True)
    parser.add_argument("--anio", type=int, default=2026)
    parser.add_argument("--resolucion", default="Resolución Nro. CU-014-2026-UNSAAC")
    parser.add_argument("--salida", default="corpus_estructurado")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(os.path.expanduser(args.md), encoding="utf-8") as fh:
        filas = parsear(fh.read())

    if not filas:
        print("No se encontraron actividades con fecha en el Markdown.")
        return 1

    doc = construir(filas, args.anio, args.resolucion)
    print(f"actividades con fecha: {len(filas)}")
    print(f"fragmentos           : {len(doc.fragmentos)}\n")
    for fila in filas[:6]:
        print(f"  - {fila['actividad'][:58]:58s} {fila['fechas'][:34]}")
    if len(filas) > 6:
        print(f"  ... y {len(filas) - 6} mas")

    if not args.dry_run:
        destino = os.path.join(BACKEND_DIR, args.salida)
        os.makedirs(destino, exist_ok=True)
        ruta = os.path.join(destino, f"calendario_{args.anio}.json")
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(doc.model_dump(mode="json"), fh, ensure_ascii=False, indent=2)
        print(f"\nEscrito en {ruta}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
