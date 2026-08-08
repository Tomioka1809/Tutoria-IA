"""Fase 2 - Convierte una malla curricular transcrita a fragmentos del corpus.

La malla 2017 solo existe como imagen, asi que su transcripcion se valida con
scripts.validate_malla antes de llegar aca: las sumas por ciclo y los totales
que la propia imagen declara la vuelven autoverificable.

Igual que con el plan de estudios, cada ciclo se redacta en prosa. La consulta
real es "que cursos llevo en sexto ciclo del plan 2017", y una fila de tabla no
se parece a esa pregunta al comparar embeddings.

Uso:
    python -m scripts.extract_malla --json malla_2017.json --plan 2017
"""
import argparse
import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app.application.dtos.corpus_dtos import (  # noqa: E402
    DocumentoCorpus,
    Fragmento,
    Procedencia,
    TipoDocumento,
)
from scripts.validate_malla import (  # noqa: E402
    CREDITOS_POR_CICLO_2017,
    TOTAL_ASIGNATURAS_2017,
    TOTAL_CREDITOS_2017,
    validar,
)

ORDINALES = {
    1: "primer", 2: "segundo", 3: "tercer", 4: "cuarto", 5: "quinto",
    6: "sexto", 7: "séptimo", 8: "octavo", 9: "noveno", 10: "décimo",
}

ETIQUETA_CATEGORIA = {
    "estudios_generales": "estudios generales",
    "estudios_especificos": "estudios específicos",
    "estudios_especialidad": "estudios de especialidad",
    "actividades_extracurriculares": "actividades extracurriculares",
    "practicas_pre_profesionales": "prácticas pre profesionales",
}


def redactar_ciclo(ciclo: dict, plan: str, nombres: dict[str, str]) -> str:
    n = ciclo["ciclo"]
    ordinal = ORDINALES.get(n, f"{n}º")
    cursos = ciclo["cursos"]

    # El chat reescribe la consulta del estudiante anteponiendole "malla
    # curricular Plan <anio>" (ver reconstruct_query). Medido, esa consulta
    # devolvia seis fragmentos del plan 2025 y ninguno del 2017, porque las FAQ
    # del 2025 estan redactadas literalmente como "¿Que cursos se llevan en el N
    # semestre bajo la malla curricular 2025?" y el ciclo de 2017 no se parecia
    # a esa forma. El ano solo no basta para inclinar el embedding.
    lineas = [
        f"¿Qué cursos se llevan en el {ordinal} semestre bajo la malla curricular {plan}? "
        f"¿Qué cursos llevo en el {ordinal} ciclo del plan {plan}?",
        f"{ordinal.capitalize()} ciclo (semestre {n}) de la malla curricular {plan} de "
        f"Ingeniería Informática y de Sistemas UNSAAC: {len(cursos)} asignaturas, "
        f"{ciclo['creditos_totales']} créditos.",
        "",
    ]

    for c in cursos:
        # Los requisitos se expresan con nombre ademas del codigo: el estudiante
        # pregunta por el curso, no por su clave.
        if c["requisitos"]:
            reqs = ", ".join(
                f"{r} {nombres[r]}" if r in nombres else r for r in c["requisitos"]
            )
            req_txt = f", requisito: {reqs}"
        else:
            req_txt = ", sin requisitos"

        categoria = ETIQUETA_CATEGORIA.get(c["categoria"], c["categoria"])
        codigo = "" if c["codigo"].startswith(("ELECTIVO", "EXTRA")) else f"{c['codigo']} "

        # Cinco asignaturas llevan en la imagen un codigo que el catalogo del
        # Centro de Computo no reconoce. Responder solo con el de la imagen le
        # da al estudiante una clave con la que no puede matricularse, asi que
        # el fragmento entrega las dos y dice cual vale.
        catalogo = c.get("codigo_catalogo")
        aclaracion = (
            f" Ojo: el catálogo del Centro de Cómputo la registra como {catalogo}, "
            "que es el código con el que se matricula."
            if catalogo
            else ""
        )
        lineas.append(
            f"- {codigo}{c['nombre']}: {c['creditos']} créditos ({categoria}){req_txt}.{aclaracion}"
        )

    # La imagen rotula quince casilleros "ASIGNATURA DE ESPECIALIDAD" y tres
    # "ACTIVIDADES EXTRACURRICULARES" sin nombrarlos. Recuperado aisladamente,
    # ese ciclo no responde "que curso llevo": remite al catalogo, que si los
    # nombra, en vez de dejar al lector con el casillero en blanco.
    sin_nombrar = [c for c in cursos if c["codigo"].startswith(("ELECTIVO", "EXTRA"))]
    if sin_nombrar:
        lineas += [
            "",
            "La imagen de la malla no nombra estas asignaturas de especialidad ni las "
            "actividades extracurriculares: solo indica cuántos créditos ocupan. Sus nombres y "
            f"códigos están en el catálogo de asignaturas del Plan Curricular {plan}.",
        ]

    return "\n".join(lineas)


def construir(datos: dict, plan: str) -> DocumentoCorpus:
    # La transcripcion declara de que imagen sale. Sin la URL, una respuesta
    # sobre la malla no se puede contrastar contra la fuente que la origina.
    procedencia = Procedencia(
        documento=f"Malla Curricular {plan} - Ingeniería Informática y de Sistemas UNSAAC",
        tipo=TipoDocumento.MALLA,
        anio=int(plan) if plan.isdigit() else None,
        url=datos.get("url_fuente"),
    )

    nombres = {
        c["codigo"]: c["nombre"]
        for ciclo in datos["ciclos"]
        for c in ciclo["cursos"]
    }

    fragmentos = [
        Fragmento(
            id=f"malla_{plan}#ciclo-{ciclo['ciclo']}",
            titulo=f"{ORDINALES.get(ciclo['ciclo'], ciclo['ciclo']).capitalize()} ciclo - Malla {plan}",
            texto=redactar_ciclo(ciclo, plan, nombres),
            seccion=["malla_curricular", f"ciclo_{ciclo['ciclo']}"],
        )
        for ciclo in datos["ciclos"]
    ]

    por_categoria: dict[str, int] = {}
    for ciclo in datos["ciclos"]:
        for c in ciclo["cursos"]:
            por_categoria[c["categoria"]] = por_categoria.get(c["categoria"], 0) + c["creditos"]

    desglose = ". ".join(
        f"{ETIQUETA_CATEGORIA.get(k, k).capitalize()}: {v} créditos"
        for k, v in sorted(por_categoria.items(), key=lambda kv: -kv[1])
    )

    fragmentos.append(
        Fragmento(
            id=f"malla_{plan}#resumen",
            titulo=f"Resumen de la malla curricular {plan}",
            texto=(
                f"La malla curricular {plan} de Ingeniería Informática y de Sistemas de la "
                f"UNSAAC comprende {len(datos['ciclos'])} ciclos, "
                f"{datos['total_asignaturas']} asignaturas y {datos['total_creditos']} créditos "
                f"necesarios para completar el plan de estudios. "
                f"Créditos por categoría: {desglose}. "
                + " ".join(
                    f"Ciclo {c['ciclo']}: {c['creditos_totales']} créditos."
                    for c in datos["ciclos"]
                )
            ),
            seccion=["malla_curricular", "resumen"],
        )
    )

    return DocumentoCorpus(procedencia=procedencia, fragmentos=fragmentos)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convierte una malla transcrita a fragmentos")
    parser.add_argument("--json", required=True)
    parser.add_argument("--plan", default="2017")
    parser.add_argument("--salida", default="corpus/estructurado")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(os.path.expanduser(args.json), encoding="utf-8") as fh:
        datos = json.load(fh)

    # No se incorpora una transcripcion que no cuadre: un credito mal leido se
    # convierte en una respuesta falsa dicha con confianza.
    if args.plan == "2017":
        errores = validar(datos, CREDITOS_POR_CICLO_2017, TOTAL_ASIGNATURAS_2017, TOTAL_CREDITOS_2017)
        if errores:
            print(f"La transcripcion no valida ({len(errores)} problemas):")
            for e in errores:
                print(f"  - {e}")
            return 1

    doc = construir(datos, args.plan)
    print(f"ciclos     : {len(datos['ciclos'])}")
    print(f"asignaturas: {datos['total_asignaturas']}")
    print(f"creditos   : {datos['total_creditos']}")
    print(f"fragmentos : {len(doc.fragmentos)}")

    if not args.dry_run:
        destino = os.path.join(BACKEND_DIR, args.salida)
        os.makedirs(destino, exist_ok=True)
        ruta = os.path.join(destino, f"malla_{args.plan}.json")
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(doc.model_dump(mode="json"), fh, ensure_ascii=False, indent=2)
        print(f"\nEscrito en {ruta}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
