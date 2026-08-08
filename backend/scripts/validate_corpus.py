"""Fase 1 - Valida el corpus estructurado contra el esquema unico.

Define el criterio de cierre de la Fase 2: mientras queden errores, el corpus no
puede sostener la metrica de cobertura del golden set, que se expresa en
articulos ("Art. 15 - Reglamento de Tutoria").

    python -m scripts.validate_corpus              # informe, siempre sale 0
    python -m scripts.validate_corpus --estricto   # sale 1 si hay errores
"""
import argparse
import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from pydantic import ValidationError  # noqa: E402

from app.application.dtos.corpus_dtos import (  # noqa: E402
    MAX_CARACTERES_TEXTO,
    MIN_CARACTERES_TEXTO,
    DocumentoCorpus,
    TipoDocumento,
)


def validar_directorio(directorio: str) -> tuple[list[str], list[str], dict]:
    errores: list[str] = []
    avisos: list[str] = []
    stats = {"documentos": 0, "fragmentos": 0, "sin_articulo": 0, "conversacionales": 0}

    if not os.path.isdir(directorio):
        return [f"No existe el directorio {directorio}"], [], stats

    for nombre in sorted(os.listdir(directorio)):
        if not nombre.endswith(".json"):
            continue
        ruta = os.path.join(directorio, nombre)
        with open(ruta, encoding="utf-8") as fh:
            crudo = json.load(fh)

        try:
            doc = DocumentoCorpus.model_validate(crudo)
        except ValidationError as exc:
            errores.append(f"{nombre}: no cumple el esquema -> {exc.error_count()} problema(s)")
            for e in exc.errors()[:3]:
                errores.append(f"    {'.'.join(str(x) for x in e['loc'])}: {e['msg']}")
            continue

        stats["documentos"] += 1
        stats["fragmentos"] += len(doc.fragmentos)

        es_reglamento = doc.procedencia.tipo == TipoDocumento.REGLAMENTO

        if es_reglamento and not doc.procedencia.resolucion:
            errores.append(
                f"{nombre}: es un reglamento y no declara la resolucion que lo aprueba."
            )

        sin_articulo = doc.fragmentos_sin_articulo
        if sin_articulo:
            stats["sin_articulo"] += len(sin_articulo)
            errores.append(
                f"{nombre}: {len(sin_articulo)}/{len(doc.fragmentos)} fragmentos normativos "
                "sin numero de articulo."
            )

        for f in doc.fragmentos:
            if f.es_conversacional:
                stats["conversacionales"] += 1
                avisos.append(f"{nombre}: fragmento conversacional indexado -> {f.id}")
            largo = len(f.texto)
            if largo < MIN_CARACTERES_TEXTO:
                avisos.append(f"{nombre}: fragmento de {largo} chars (min {MIN_CARACTERES_TEXTO}) -> {f.id}")
            elif largo > MAX_CARACTERES_TEXTO:
                avisos.append(f"{nombre}: fragmento de {largo} chars (max {MAX_CARACTERES_TEXTO}) -> {f.id}")

    return errores, avisos, stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida el corpus estructurado")
    parser.add_argument("--directorio", default="corpus/estructurado")
    parser.add_argument("--estricto", action="store_true", help="Sale con codigo 1 si hay errores")
    parser.add_argument("--max-avisos", type=int, default=10)
    args = parser.parse_args()

    directorio = os.path.join(BACKEND_DIR, args.directorio)
    errores, avisos, stats = validar_directorio(directorio)

    print("=" * 78)
    print("FASE 1 - VALIDACION DEL CORPUS ESTRUCTURADO")
    print("=" * 78)
    print(f"\n  documentos            : {stats['documentos']}")
    print(f"  fragmentos            : {stats['fragmentos']}")
    print(f"  sin articulo (norm.)  : {stats['sin_articulo']}")
    print(f"  conversacionales      : {stats['conversacionales']}")

    if errores:
        print(f"\n{'-' * 78}\nERRORES ({len(errores)}) - pendientes de la Fase 2\n{'-' * 78}")
        for e in errores:
            print(f"  {e}")

    if avisos:
        print(f"\n{'-' * 78}\nAVISOS ({len(avisos)})\n{'-' * 78}")
        for a in avisos[: args.max_avisos]:
            print(f"  {a}")
        if len(avisos) > args.max_avisos:
            print(f"  ... y {len(avisos) - args.max_avisos} mas")

    print(f"\n{'=' * 78}")
    if errores:
        print(f"RESULTADO: {len(errores)} error(es). El corpus aun no puede citar articulado.")
    else:
        print("RESULTADO: el corpus cumple el esquema y es citable por articulo.")
    print("=" * 78)

    return 1 if (errores and args.estricto) else 0


if __name__ == "__main__":
    raise SystemExit(main())
