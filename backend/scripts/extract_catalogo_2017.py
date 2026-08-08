"""Convierte el catalogo oficial del plan 2017 a fragmentos del corpus.

`malla_2017.json` transcribe la *imagen* de la malla, y esa imagen deja quince
casilleros rotulados "ASIGNATURA DE ESPECIALIDAD" sin nombre ni codigo. Con solo
ese documento, "que cursos de especialidad puedo llevar en el plan 2017" no tiene
respuesta: el corpus sabe cuantos creditos son y en que ciclo van, pero no que
asignaturas son.

El catalogo del Centro de Computo si las nombra, porque es el registro contra el
que se matricula. De ahi salen ademas tres cosas que la imagen no dice: los
codigos de las actividades extracurriculares (IF060-IF066), el de la practica
pre profesional (IF020) y los creditos exigidos para egresar.

Los codigos del catalogo priman sobre los de la imagen cuando difieren -son los
que el estudiante escribe al matricularse-, pero la discrepancia se redacta en
un fragmento propio en vez de silenciarse: quien mira la malla colgada en la
escuela lee "ME359 ECUACIONES DIFERENCIALES" y el sistema debe poder explicarle
por que el catalogo dice otra cosa.

Uso:
    python -m scripts.extract_catalogo_2017
    python -m scripts.extract_catalogo_2017 --dry-run
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

ORDINALES = {
    1: "primer", 2: "segundo", 3: "tercer", 4: "cuarto", 5: "quinto",
    6: "sexto", 7: "séptimo", 8: "octavo", 9: "noveno", 10: "décimo",
}

CABECERA = "Plan de Estudios 2017 (catálogo oficial) - Ingeniería Informática y de Sistemas UNSAAC"


def redactar_requisito(requisito: str | None, nombres: dict[str, str]) -> str:
    """'IF450*IF480' -> 'requisito: IF450 ABSTRACCIÓN..., IF480 ADMINISTRACIÓN...'.

    El catalogo separa los prerrequisitos con '*'. Se expanden a nombre completo
    porque el estudiante pregunta por el curso, no por su clave.
    """
    if not requisito:
        return "sin requisitos"

    partes = []
    for pieza in requisito.split("*"):
        pieza = pieza.strip()
        partes.append(f"{pieza} {nombres[pieza]}" if pieza in nombres else pieza)
    return "requisito: " + ", ".join(partes)


def linea_de_curso(curso: dict, categorias: dict[str, str], nombres: dict[str, str]) -> str:
    categoria = categorias.get(curso["categoria"], curso["categoria"])
    return (
        f"- {curso['codigo']} {curso['nombre']}: {curso['creditos']} créditos "
        f"({categoria}), {redactar_requisito(curso.get('requisito'), nombres)}."
    )


def redactar_semestre(semestre: dict, categorias: dict, nombres: dict) -> str:
    n = semestre["numero"]
    cursos = semestre["cursos"]
    creditos = sum(c["creditos"] for c in cursos)
    ordinal = ORDINALES.get(n, f"{n}º")

    lineas = [
        f"{ordinal.capitalize()} semestre del plan de estudios 2017 de Ingeniería "
        f"Informática y de Sistemas UNSAAC según el catálogo del Centro de Cómputo: "
        f"{len(cursos)} asignaturas, {creditos} créditos.",
        "",
    ]
    lineas += [linea_de_curso(c, categorias, nombres) for c in cursos]
    return "\n".join(lineas)


def especialidad_por_semestre(datos: dict) -> list[dict]:
    return [
        curso
        for semestre in datos["semestres"]
        for curso in semestre["cursos"]
        if curso["categoria"] == "EEEP"
    ]


def construir(datos: dict) -> DocumentoCorpus:
    fuente = datos["fuente"]
    categorias = datos["categorias"]

    todos = [c for s in datos["semestres"] for c in s["cursos"]]
    todos += datos["electivos_y_complementarios"]
    nombres = {c["codigo"]: c["nombre"] for c in todos}

    procedencia = Procedencia(
        documento=CABECERA,
        tipo=TipoDocumento.MALLA,
        anio=2017,
        url=fuente["url"],
    )

    fragmentos = [
        Fragmento(
            id=f"plan_estudios_2017#semestre-{s['numero']}",
            titulo=f"{ORDINALES.get(s['numero'], s['numero']).capitalize()} semestre - Plan 2017",
            texto=f"{CABECERA} > {redactar_semestre(s, categorias, nombres)}",
            seccion=["plan_estudios_2017", f"semestre_{s['numero']}"],
            palabras_clave=[c["codigo"] for c in s["cursos"]],
        )
        for s in datos["semestres"]
    ]

    # Un indice compacto para "que asignaturas de especialidad hay" y un
    # fragmento por asignatura para "de que trata X" o "que requisito tiene X".
    # Listarlas todas con detalle en un solo fragmento daba 3614 caracteres y
    # metia treinta y siete temas distintos en un mismo embedding.
    en_semestre = especialidad_por_semestre(datos)
    ubicacion = {c["codigo"]: c for s in datos["semestres"] for c in s["cursos"]}
    semestre_de = {
        c["codigo"]: s["numero"] for s in datos["semestres"] for c in s["cursos"]
    }
    electivos = [c for c in datos["electivos_y_complementarios"] if c["categoria"] == "EEEP"]
    todas_especialidad = en_semestre + electivos

    # El indice va en dos partes, siguiendo la division del propio catalogo:
    # las que trae ubicadas en un semestre y las del bloque de electivos.
    # Juntas daban 1691 caracteres.
    fragmentos.append(
        Fragmento(
            id="plan_estudios_2017#especialidad-indice",
            titulo="Qué asignaturas de especialidad ofrece el plan 2017",
            texto=(
                f"{CABECERA} > Qué asignaturas de especialidad ofrece el plan 2017\n"
                # El chat reescribe la consulta como "malla curricular Plan 2017 ...".
                # Sin esta apertura, los fragmentos por ciclo de malla_2017 -que si
                # tienen esa forma- se llevaban los seis slots y la respuesta quedaba
                # en "la malla no las nombra", que es justo lo que habia que resolver.
                "¿Qué asignaturas de especialidad se llevan bajo la malla curricular 2017? "
                "¿Qué cursos electivos de especialidad hay en el plan 2017?\n"
                "El plan 2017 exige 45 créditos de estudios de especialidad. La imagen de la "
                'malla curricular los muestra como quince casilleros rotulados "ASIGNATURA DE '
                'ESPECIALIDAD" sin nombre. El catálogo del Centro de Cómputo sí los nombra: '
                f"ofrece {len(todas_especialidad)} asignaturas de especialidad en total. "
                f"Las {len(en_semestre)} que el catálogo ubica en un semestre concreto son:\n\n"
                + ", ".join(f"{c['codigo']} {c['nombre']}" for c in en_semestre)
                + "."
            ),
            seccion=["plan_estudios_2017", "asignaturas_de_especialidad"],
            palabras_clave=["asignatura de especialidad", "electivo", "EEEP", "45 créditos"],
        )
    )
    # Los electivos se listan en dos mitades: veintiseis nombres en un solo
    # fragmento pasaban de 1400 caracteres.
    mitad = (len(electivos) + 1) // 2
    for parte, bloque in enumerate((electivos[:mitad], electivos[mitad:]), 1):
        fragmentos.append(
            Fragmento(
                id=f"plan_estudios_2017#especialidad-indice-electivos-{parte}",
                titulo=f"Asignaturas de especialidad electivas del plan 2017 ({parte} de 2)",
                texto=(
                    f"{CABECERA} > Asignaturas de especialidad electivas ({parte} de 2)\n"
                    "¿Qué asignaturas electivas de especialidad se pueden llevar bajo la malla "
                    "curricular 2017?\n"
                    "Además de las que ubica en un semestre, el catálogo del plan 2017 ofrece "
                    f"{len(electivos)} asignaturas de especialidad en el bloque de cursos "
                    "electivos y/o complementarios, sin semestre fijo. El estudiante elige entre "
                    "ellas hasta completar los 45 créditos de estudios de especialidad. "
                    f"Parte {parte} de 2 de la lista:\n\n"
                    + ", ".join(f"{c['codigo']} {c['nombre']}" for c in bloque)
                    + "."
                ),
                seccion=["plan_estudios_2017", "asignaturas_de_especialidad"],
                palabras_clave=["electivo", "complementario", "EEEP", "45 créditos"],
            )
        )

    for curso in todas_especialidad:
        if curso["codigo"] in ubicacion:
            donde = (
                f"El catálogo la ubica en el semestre {semestre_de[curso['codigo']]} "
                "del plan de estudios."
            )
        else:
            donde = (
                "El catálogo la ofrece en el bloque de cursos electivos y/o complementarios, "
                "sin semestre fijo."
            )
        fragmentos.append(
            Fragmento(
                id=f"plan_estudios_2017#especialidad-{curso['codigo'].lower()}",
                titulo=f"{curso['codigo']} {curso['nombre']} - asignatura de especialidad, plan 2017",
                texto=(
                    f"{CABECERA} > Asignatura de especialidad {curso['codigo']}\n"
                    f"{curso['codigo']} {curso['nombre']} es una asignatura de especialidad "
                    f"(categoría EEEP) del plan de estudios 2017 de Ingeniería Informática y de "
                    f"Sistemas UNSAAC. Vale {curso['creditos']} créditos y tiene "
                    f"{redactar_requisito(curso.get('requisito'), nombres)}. {donde} "
                    "Cuenta para los 45 créditos de estudios de especialidad que exige el plan."
                ),
                seccion=["plan_estudios_2017", "asignaturas_de_especialidad"],
                palabras_clave=[curso["codigo"], curso["nombre"]],
            )
        )

    extracurriculares = [c for c in todos if c["categoria"] == "AEX"]
    fragmentos.append(
        Fragmento(
            id="plan_estudios_2017#actividades-extracurriculares",
            titulo="Actividades extracurriculares - Plan 2017",
            texto=(
                f"{CABECERA} > Actividades extracurriculares\n"
                "El plan 2017 exige 6 créditos de actividades extracurriculares, que se cursan "
                "en tres bloques de 2 créditos. La imagen de la malla los ubica en los ciclos 4, "
                "7 y 9 sin nombrarlos; el catálogo los identifica así:\n\n"
                + "\n".join(linea_de_curso(c, categorias, nombres) for c in extracurriculares)
            ),
            seccion=["plan_estudios_2017", "actividades_extracurriculares"],
            palabras_clave=["actividades extracurriculares", "música", "quechua", "danza", "teatro"],
        )
    )

    practicas = [c for c in todos if c["categoria"] == "PPP"]
    fragmentos.append(
        Fragmento(
            id="plan_estudios_2017#practicas-pre-profesionales",
            titulo="Prácticas pre profesionales - Plan 2017",
            texto=(
                f"{CABECERA} > Prácticas pre profesionales\n"
                "Las prácticas pre profesionales del plan 2017 valen 9 créditos y la imagen de la "
                'malla las ubica en el décimo ciclo con el código incompleto "IF". El catálogo '
                "del Centro de Cómputo las registra así:\n\n"
                + "\n".join(linea_de_curso(c, categorias, nombres) for c in practicas)
            ),
            seccion=["plan_estudios_2017", "practicas_pre_profesionales"],
            palabras_clave=["prácticas pre profesionales", "IF020"],
        )
    )

    egreso = datos["condicion_egresante"]
    totales = datos["totales_por_categoria"]
    fragmentos.append(
        Fragmento(
            id="plan_estudios_2017#creditos-y-egreso",
            titulo="Créditos totales y condición de egreso - Plan 2017",
            texto=(
                f"{CABECERA} > Créditos totales y condición de egreso\n"
                f"El plan de estudios 2017 de Ingeniería Informática y de Sistemas exige "
                f"{datos['total_creditos']} créditos para egresar, repartidos así: "
                + ", ".join(
                    f"{categorias.get(k, k)} {v} créditos"
                    for k, v in sorted(totales.items(), key=lambda kv: -kv[1])
                )
                + f". {egreso['nota_articulo_8']}: {egreso['creditos_minimos_articulo_8']} créditos. "
                f"Créditos mínimos exigidos para ser egresado: {egreso['creditos_para_egresar']}."
            ),
            seccion=["plan_estudios_2017", "creditos_y_egreso"],
            palabras_clave=["créditos", "egresar", "egresado", "219"],
        )
    )

    discrepancias = datos["discrepancias_con_la_malla"]
    fragmentos.append(
        Fragmento(
            id="plan_estudios_2017#discrepancias-de-codigo",
            titulo="Diferencias de código entre la imagen de la malla 2017 y el catálogo",
            texto=(
                f"{CABECERA} > Diferencias de código entre la imagen de la malla y el catálogo\n"
                "La imagen de la malla curricular 2017 publicada por la Escuela Profesional y el "
                "catálogo de asignaturas del Centro de Cómputo usan códigos distintos para cinco "
                "asignaturas. Vale el código del catálogo, que es el registro contra el que se "
                "matricula:\n\n"
                + "\n".join(
                    f"- {d['asignatura']}: el catálogo la registra como {d['codigo_catalogo']}; "
                    f"la imagen de la malla la muestra como {d['codigo_en_la_imagen']}."
                    + (f" {d['nota']}" if d.get("nota") else "")
                    for d in discrepancias
                )
            ),
            seccion=["plan_estudios_2017", "discrepancias"],
            palabras_clave=["código", "malla 2017", "catálogo"],
        )
    )

    return DocumentoCorpus(procedencia=procedencia, fragmentos=fragmentos)


def verificar(datos: dict) -> list[str]:
    """Comprueba el catalogo contra los totales que el propio catalogo declara.

    Igual que con la malla: una transcripcion con un credito mal leido es peor
    que no tenerla, porque el sistema afirmaria un dato falso con confianza.
    """
    errores: list[str] = []

    todos = [c for s in datos["semestres"] for c in s["cursos"]]
    todos += datos["electivos_y_complementarios"]

    vistos: dict[str, int] = {}
    for c in todos:
        if c["codigo"] in vistos:
            errores.append(f"Código duplicado: {c['codigo']}")
        vistos[c["codigo"]] = 1

    # Solo las categorias con oferta cerrada se pueden sumar contra el total
    # declarado. EEEP no: el catalogo ofrece mas creditos de especialidad de los
    # 45 que se exigen, porque el estudiante elige.
    for categoria in ("EG", "EGT", "OEES", "PPP"):
        suma = sum(c["creditos"] for c in todos if c["categoria"] == categoria)
        declarado = datos["totales_por_categoria"][categoria]
        if suma != declarado:
            errores.append(
                f"Categoría {categoria}: los cursos suman {suma} créditos "
                f"pero el catálogo declara {declarado}"
            )

    suma_total = sum(datos["totales_por_categoria"].values())
    if suma_total != datos["total_creditos"]:
        errores.append(
            f"Las categorías suman {suma_total} créditos pero se declaran "
            f"{datos['total_creditos']}"
        )

    return errores


def main() -> int:
    parser = argparse.ArgumentParser(description="Convierte el catálogo 2017 a fragmentos")
    parser.add_argument("--json", default="corpus/fuentes/catalogo_2017.json")
    parser.add_argument("--salida", default="corpus/estructurado")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ruta_origen = os.path.join(BACKEND_DIR, args.json)
    with open(ruta_origen, encoding="utf-8") as fh:
        datos = json.load(fh)

    errores = verificar(datos)
    if errores:
        print(f"El catálogo no valida ({len(errores)} problemas):")
        for e in errores:
            print(f"  - {e}")
        return 1

    doc = construir(datos)
    print(f"semestres  : {len(datos['semestres'])}")
    print(f"electivos  : {len(datos['electivos_y_complementarios'])}")
    print(f"fragmentos : {len(doc.fragmentos)}")

    if not args.dry_run:
        destino = os.path.join(BACKEND_DIR, args.salida)
        os.makedirs(destino, exist_ok=True)
        ruta = os.path.join(destino, "plan_estudios_2017.json")
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(doc.model_dump(mode="json"), fh, ensure_ascii=False, indent=2)
        print(f"\nEscrito en {ruta}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
