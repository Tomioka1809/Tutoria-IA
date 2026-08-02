"""Valida la transcripcion de una malla curricular antes de incorporarla.

La malla 2017 solo existe como imagen, asi que su transcripcion viene de afuera.
Antes de meterla al corpus hay que comprobarla contra las invariantes que la
propia imagen declara, porque una transcripcion con creditos mal leidos es peor
que no tenerla: el chatbot afirmaria con confianza un dato falso.

La imagen de la malla 2017 declara sus totales: ciclo I con 21 creditos, ciclos
II al X con 22 cada uno, 62 asignaturas y 219 creditos. Eso hace la
transcripcion autoverificable.

Uso:
    python -m scripts.validate_malla --json malla_2017_transcrita.json
"""
import argparse
import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

CATEGORIAS = {
    "estudios_generales",
    "estudios_especificos",
    "estudios_especialidad",
    "actividades_extracurriculares",
    "practicas_pre_profesionales",
}

# Totales que la propia imagen de la malla declara en su encabezado.
CREDITOS_POR_CICLO_2017 = {1: 21, **{c: 22 for c in range(2, 11)}}
TOTAL_ASIGNATURAS_2017 = 62
TOTAL_CREDITOS_2017 = 219


def validar(datos: dict, esperado_ciclos: dict, total_asig: int, total_cred: int) -> list[str]:
    errores: list[str] = []

    ciclos = datos.get("ciclos")
    if not isinstance(ciclos, list) or not ciclos:
        return ["El JSON no tiene una lista 'ciclos' con contenido."]

    vistos_codigo: dict[str, int] = {}
    suma_cursos = suma_creditos = 0

    for ciclo in ciclos:
        n = ciclo.get("ciclo")
        cursos = ciclo.get("cursos") or []
        if not isinstance(n, int):
            errores.append(f"Ciclo sin numero valido: {n!r}")
            continue

        suma = 0
        for curso in cursos:
            codigo = str(curso.get("codigo", "")).strip()
            creditos = curso.get("creditos")

            if not codigo:
                errores.append(f"Ciclo {n}: curso sin codigo ({curso.get('nombre')!r})")
            elif codigo in vistos_codigo:
                errores.append(f"Codigo duplicado {codigo} (ciclos {vistos_codigo[codigo]} y {n})")
            else:
                vistos_codigo[codigo] = n

            if not isinstance(creditos, int) or creditos <= 0:
                errores.append(f"Ciclo {n}, {codigo}: creditos invalidos ({creditos!r})")
            else:
                suma += creditos

            categoria = curso.get("categoria")
            if categoria not in CATEGORIAS:
                errores.append(f"Ciclo {n}, {codigo}: categoria desconocida ({categoria!r})")

            if not isinstance(curso.get("requisitos"), list):
                errores.append(f"Ciclo {n}, {codigo}: 'requisitos' debe ser una lista")

        declarado = ciclo.get("creditos_totales")
        if declarado is not None and suma != declarado:
            errores.append(f"Ciclo {n}: los cursos suman {suma} pero declara {declarado}")

        esperado = esperado_ciclos.get(n)
        if esperado is not None and suma != esperado:
            errores.append(f"Ciclo {n}: suma {suma} creditos, la imagen indica {esperado}")

        suma_cursos += len(cursos)
        suma_creditos += suma

    faltantes = sorted(set(esperado_ciclos) - {c.get("ciclo") for c in ciclos})
    if faltantes:
        errores.append(f"Faltan ciclos: {faltantes}")

    if suma_cursos != total_asig:
        errores.append(f"Total de asignaturas: {suma_cursos}, la imagen indica {total_asig}")
    if suma_creditos != total_cred:
        errores.append(f"Total de creditos: {suma_creditos}, la imagen indica {total_cred}")

    # Un requisito que apunta a un codigo inexistente suele ser un error de lectura.
    for ciclo in ciclos:
        for curso in ciclo.get("cursos") or []:
            for req in curso.get("requisitos") or []:
                if req not in vistos_codigo:
                    errores.append(
                        f"Ciclo {ciclo.get('ciclo')}, {curso.get('codigo')}: "
                        f"requisito {req} no corresponde a ningun curso de la malla"
                    )

    return errores


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida una malla curricular transcrita")
    parser.add_argument("--json", required=True, help="Archivo JSON con la transcripcion")
    parser.add_argument("--total-asignaturas", type=int, default=TOTAL_ASIGNATURAS_2017)
    parser.add_argument("--total-creditos", type=int, default=TOTAL_CREDITOS_2017)
    args = parser.parse_args()

    with open(os.path.expanduser(args.json), encoding="utf-8") as fh:
        datos = json.load(fh)

    errores = validar(datos, CREDITOS_POR_CICLO_2017, args.total_asignaturas, args.total_creditos)

    print("=" * 74)
    print("VALIDACION DE LA MALLA TRANSCRITA")
    print("=" * 74)

    if not errores:
        cursos = sum(len(c.get("cursos") or []) for c in datos["ciclos"])
        print(f"\n  OK: {len(datos['ciclos'])} ciclos, {cursos} asignaturas, "
              f"{args.total_creditos} creditos.")
        print("  La transcripcion cuadra con los totales que declara la imagen.")
        return 0

    print(f"\n  {len(errores)} problema(s):\n")
    for e in errores:
        print(f"    - {e}")
    print("\n  No incorporar al corpus hasta corregir: un credito mal leido se")
    print("  convierte en una respuesta falsa dicha con confianza.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
