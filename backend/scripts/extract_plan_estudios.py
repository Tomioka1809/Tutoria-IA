"""Fase 2 - Convierte el plan de estudios tabular a fragmentos del corpus.

El plan de estudios no tiene articulado: es una tabla por semestre con codigo,
asignatura, creditos, horas y requisitos. El extractor de articulado no sirve
aca, asi que este script parte del Markdown que produce docling (que preserva
las tablas y une bien las celdas multilinea) y arma un fragmento por semestre.

El fragmento se redacta en prosa ademas de la tabla porque la pregunta real del
estudiante es "que cursos llevo en el tercer semestre", y una fila suelta como
"IFI02 | 4 | 3 | 2" no se parece a esa consulta en el espacio de embeddings.

Uso:
    python -m scripts.extract_plan_estudios --md ~/Downloads/"coupus de pdfs"/plan-estudios-semestralizado-ing-informatica-2025.md
"""
import argparse
import json
import os
import re
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app.application.dtos.corpus_dtos import (  # noqa: E402
    DocumentoCorpus,
    Fragmento,
    Procedencia,
    TipoDocumento,
)

ORDINALES = {
    "PRIMER": 1, "SEGUNDO": 2, "TERCER": 3, "CUARTO": 4, "QUINTO": 5,
    "SEXTO": 6, "SEPTIMO": 7, "SÉPTIMO": 7, "OCTAVO": 8, "NOVENO": 9, "DECIMO": 10,
    "DÉCIMO": 10,
}
RE_SEMESTRE = re.compile(
    r"^\s*(" + "|".join(ORDINALES) + r")\s+SEMESTRE\s*$", re.IGNORECASE
)
RE_FILA = re.compile(r"^\s*\|(.+)\|\s*$")
RE_SEPARADOR = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
RE_TOTAL = re.compile(r"Total\s+Cr\.?\s*(\d+)", re.IGNORECASE)


def celdas(linea: str) -> list[str]:
    m = RE_FILA.match(linea)
    if not m:
        return []
    return [c.strip() for c in m.group(1).split("|")]


def parsear(md: str) -> list[dict]:
    """Devuelve [{semestre, numero, cursos:[...], total_creditos}]."""
    semestres: list[dict] = []
    actual: dict | None = None
    encabezado: list[str] | None = None

    for linea in md.splitlines():
        m_sem = RE_SEMESTRE.match(linea.strip())
        if m_sem:
            nombre = m_sem.group(1).upper()
            actual = {
                "semestre": f"{nombre.capitalize()} semestre",
                "numero": ORDINALES[nombre],
                "cursos": [],
                "total_creditos": None,
            }
            semestres.append(actual)
            encabezado = None
            continue

        if actual is None:
            continue

        m_total = RE_TOTAL.search(linea)
        if m_total:
            actual["total_creditos"] = int(m_total.group(1))
            continue

        if RE_SEPARADOR.match(linea):
            continue

        cols = celdas(linea)
        if not cols:
            continue

        if encabezado is None and any(c.upper() == "COD" for c in cols):
            encabezado = [c.upper() for c in cols]
            continue

        if encabezado and len(cols) == len(encabezado):
            fila = dict(zip(encabezado, cols))
            if not fila.get("COD"):
                continue
            actual["cursos"].append({
                "codigo": fila.get("COD", ""),
                "nombre": fila.get("ASIGNATURA", ""),
                "creditos": fila.get("CR", ""),
                "horas_teoricas": fila.get("HT", ""),
                "horas_practicas": fila.get("HP", ""),
                "requisitos": [r for r in (fila.get("REQ1", ""), fila.get("REQ2", "")) if r],
            })

    return [s for s in semestres if s["cursos"]]


def redactar(sem: dict, plan: str) -> str:
    """Redacta el semestre en prosa, no solo como tabla.

    La consulta del estudiante es en lenguaje natural; una tabla cruda se parece
    poco a esa pregunta al momento de comparar embeddings.
    """
    total = sem["total_creditos"]
    cabecera = (
        f"{sem['semestre']} del Plan de Estudios {plan} de Ingeniería Informática "
        f"y de Sistemas UNSAAC ({len(sem['cursos'])} asignaturas"
        + (f", {total} créditos en total" if total else "")
        + ")."
    )

    lineas = [cabecera, ""]
    for c in sem["cursos"]:
        req = f", requisitos: {', '.join(c['requisitos'])}" if c["requisitos"] else ", sin requisitos"
        lineas.append(
            f"- {c['codigo']} {c['nombre']}: {c['creditos']} créditos "
            f"({c['horas_teoricas']} horas teóricas, {c['horas_practicas']} prácticas){req}."
        )
    return "\n".join(lineas)


def construir(semestres: list[dict], plan: str) -> DocumentoCorpus:
    procedencia = Procedencia(
        documento=f"Plan de Estudios {plan} - Ingeniería Informática y de Sistemas UNSAAC",
        tipo=TipoDocumento.MALLA,
        anio=int(plan) if plan.isdigit() else None,
    )

    fragmentos = [
        Fragmento(
            id=f"plan_estudios_{plan}#semestre-{s['numero']}",
            titulo=f"{s['semestre']} - Plan {plan}",
            texto=redactar(s, plan),
            seccion=["plan_de_estudios", f"semestre_{s['numero']}"],
        )
        for s in semestres
    ]

    total_cursos = sum(len(s["cursos"]) for s in semestres)
    creditos = [s["total_creditos"] for s in semestres if s["total_creditos"]]
    if creditos:
        fragmentos.append(
            Fragmento(
                id=f"plan_estudios_{plan}#resumen",
                titulo=f"Resumen del Plan de Estudios {plan}",
                texto=(
                    f"El Plan de Estudios {plan} de Ingeniería Informática y de Sistemas "
                    f"de la UNSAAC comprende {len(semestres)} semestres, {total_cursos} "
                    f"asignaturas y {sum(creditos)} créditos en total. "
                    + " ".join(
                        f"{s['semestre']}: {s['total_creditos']} créditos."
                        for s in semestres if s["total_creditos"]
                    )
                ),
                seccion=["plan_de_estudios", "resumen"],
            )
        )

    return DocumentoCorpus(procedencia=procedencia, fragmentos=fragmentos)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extrae el plan de estudios desde Markdown")
    parser.add_argument("--md", required=True, help="Markdown producido por docling")
    parser.add_argument("--plan", default="2025")
    parser.add_argument("--salida", default="corpus/estructurado")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(os.path.expanduser(args.md), encoding="utf-8") as fh:
        md = fh.read()

    semestres = parsear(md)
    if not semestres:
        print("No se encontraron tablas de semestre en el Markdown.")
        return 1

    doc = construir(semestres, args.plan)

    print(f"{'semestre':22s} {'cursos':>7s} {'creditos':>9s}")
    print("-" * 42)
    for s in semestres:
        print(f"{s['semestre']:22s} {len(s['cursos']):>7d} {str(s['total_creditos'] or '-'):>9s}")
    print("-" * 42)
    print(f"{'TOTAL':22s} {sum(len(s['cursos']) for s in semestres):>7d} "
          f"{sum(s['total_creditos'] or 0 for s in semestres):>9d}")
    print(f"\nfragmentos: {len(doc.fragmentos)}")

    if not args.dry_run:
        destino = os.path.join(BACKEND_DIR, args.salida)
        os.makedirs(destino, exist_ok=True)
        ruta = os.path.join(destino, f"plan_estudios_{args.plan}.json")
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(doc.model_dump(mode="json"), fh, ensure_ascii=False, indent=2)
        print(f"Escrito en {ruta}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
