"""Convierte la guia de becas y comedor a fragmentos del corpus.

Dos preguntas frecuentes no tenian respuesta utilizable. "Que becas existen en
la universidad" solo enganchaba una FAQ sin fuente que decia que la Unidad de
Asistencia Social "promueve y tramita becas", sin nombrar ni una. "Como obtengo
el comedor" respondia que hay una evaluacion socioeconomica, y omitia lo unico
que el estudiante necesita hacer: reservar el cupo en el sistema de Bienestar.

Este documento es un indice, no una fuente nueva: cada fragmento nombra la norma
o el documento oficial del que sale lo que afirma, y el articulado citado ya esta
indexado por separado. Por eso ningun fragmento lleva numero de articulo propio y
todos quedan en el nivel de autoridad mas bajo: ante la misma consulta, el
Estatuto o el ROF deben ganarle a este resumen.

Uso:
    python -m scripts.extract_becas_comedor
    python -m scripts.extract_becas_comedor --dry-run
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

DOCUMENTO = "Guía de becas, apoyos económicos y comedor universitario UNSAAC"


def slug(texto: str) -> str:
    limpio = texto.lower()
    for viejo, nuevo in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")):
        limpio = limpio.replace(viejo, nuevo)
    return "".join(c if c.isalnum() else "-" for c in limpio).strip("-")[:50]


def frag(id_: str, titulo: str, cuerpo: str, seccion: list[str], claves: list[str]) -> Fragmento:
    return Fragmento(
        id=f"becas_y_comedor#{id_}",
        titulo=titulo,
        texto=f"{DOCUMENTO} > {titulo}\n{cuerpo}",
        seccion=["becas_y_comedor", *seccion],
        palabras_clave=claves,
    )


def fragmentos_indice(datos: dict) -> list[Fragmento]:
    """Indice separado en becas propias y externas.

    Se parte en dos porque la distincion importa al responder: una la otorga la
    Universidad y se tramita en Bienestar, la otra la concursa el Estado y la
    UNSAAC solo asesora. Ademas, junto daba 1606 caracteres.
    """
    propias = [b for b in datos["becas"] if b["ambito"] == "UNSAAC"]
    externas = [b for b in datos["becas"] if b["ambito"] == "externa"]

    return [
        frag(
            "que-becas-existen",
            "Qué becas y apoyos económicos otorga la UNSAAC",
            "Estos son los apoyos económicos y becas que la UNSAAC otorga con recursos propios:\n\n"
            + "\n".join(f"- {b['nombre']}: {b['que_cubre']}" for b in propias)
            # Sin esta linea, quien lea solo este fragmento concluye que estas
            # son todas las becas a las que puede postular, y no lo son.
            + "\n\nAparte de estas, los estudiantes de la UNSAAC pueden postular a becas del "
            "Estado que administra PRONABEC y que la Universidad no otorga.",
            ["indice"],
            ["becas", "apoyo económico", "beneficios", "subvención"],
        ),
        frag(
            "becas-externas",
            "Becas del Estado a las que pueden postular los estudiantes de la UNSAAC",
            "Además de sus propios apoyos, los estudiantes de la UNSAAC pueden postular a becas "
            "que administra PRONABEC (MINEDU) y que no otorga la Universidad. La Oficina de "
            "Cooperación y Relaciones Internacionales (OCRI) brinda asesoría gratuita para "
            "postular:\n\n"
            + "\n".join(f"- {b['nombre']}: {b['que_cubre']}" for b in externas),
            ["indice"],
            ["becas", "PRONABEC", "Beca 18", "Beca Permanencia", "OCRI"],
        ),
    ]


def fragmentos_becas(datos: dict) -> list[Fragmento]:
    fragmentos = []
    for beca in datos["becas"]:
        origen = (
            "Es un beneficio que otorga la propia UNSAAC."
            if beca["ambito"] == "UNSAAC"
            else "No la otorga la UNSAAC: es una beca del Estado."
        )
        fragmentos.append(
            frag(
                f"beca-{slug(beca['nombre'])}",
                beca["nombre"],
                f"{origen} Qué cubre: {beca['que_cubre']} "
                f"A quién está dirigida: {beca['dirigido_a']} "
                f"Cómo se obtiene: {beca['como_se_obtiene']} "
                f"Fundamento: {'; '.join(beca['fundamento'])}.",
                ["becas"],
                ["beca", beca["nombre"]],
            )
        )
    return fragmentos


def fragmentos_comedor(datos: dict) -> list[Fragmento]:
    c = datos["comedor"]
    reserva = c["reserva_de_cupo"]
    cobertura = c["cobertura_2026_i"]

    acceso = frag(
        "comedor-quien-accede",
        "Quién puede acceder al comedor universitario",
        f"{c['naturaleza']} {c['prioridad']} {c['quien_evalua']} "
        f"Fundamento: {'; '.join(c['fundamento'])}.",
        ["comedor"],
        ["comedor", "alimentación", "invicto", "caso social"],
    )

    pasos = "\n".join(f"{i}. {p}" for i, p in enumerate(reserva["pasos"], 1))
    tramite = frag(
        "comedor-como-reservar-cupo",
        "Cómo obtener el comedor universitario: reserva de cupo",
        "Para comer en el comedor universitario hay que reservar el cupo en el "
        f"{reserva['sistema']}, en {reserva['url']}. Pasos:\n\n{pasos}\n\n"
        f"{reserva['condiciones']} Soporte técnico: {reserva['soporte']} "
        f"Fuente: {reserva['manual']} ({reserva['manual_url']}).",
        ["comedor", "tramite"],
        ["comedor", "reservar cupo", "bienestar", "código de estudiante"],
    )

    escala = frag(
        "comedor-cobertura",
        "Cobertura del comedor universitario en el semestre 2026-I",
        f"{cobertura['beneficiarios']} El servicio se implementa en las sedes de "
        f"{cobertura['sedes']} {cobertura['advertencia']} "
        f"Fuente: portal institucional UNSAAC ({cobertura['url']}).",
        ["comedor"],
        ["comedor", "cupos", "raciones", "sedes"],
    )

    return [acceso, tramite, escala]


def construir(datos: dict) -> DocumentoCorpus:
    procedencia = Procedencia(
        documento=DOCUMENTO,
        tipo=TipoDocumento.SERVICIO,
        anio=2026,
        url=datos["comedor"]["reserva_de_cupo"]["url"],
        base_legal=[
            "Estatuto de la UNSAAC, Art. 244-255",
            "ROF UNSAAC 2024 (AU-008-2024), Art. 104-115",
            "Reglamento del Instituto de Idiomas (CU-281-2020)",
            "Reglamento para Uso de Vivienda Estudiantil (CU-372-2020)",
            "Reglamento para el Otorgamiento de Subvenciones Económicas (CU-667-2025)",
        ],
    )

    fragmentos = [
        *fragmentos_indice(datos),
        *fragmentos_becas(datos),
        *fragmentos_comedor(datos),
    ]

    return DocumentoCorpus(procedencia=procedencia, fragmentos=fragmentos)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convierte la guía de becas y comedor")
    parser.add_argument("--json", default="corpus_fuentes/becas_y_comedor.json")
    parser.add_argument("--salida", default="corpus_estructurado")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(os.path.join(BACKEND_DIR, args.json), encoding="utf-8") as fh:
        datos = json.load(fh)

    doc = construir(datos)
    print(f"becas      : {len(datos['becas'])}")
    print(f"fragmentos : {len(doc.fragmentos)}")
    largos = [(len(f.texto), f.id) for f in doc.fragmentos]
    print(f"texto max  : {max(largos)[0]} chars ({max(largos)[1]})")

    if not args.dry_run:
        destino = os.path.join(BACKEND_DIR, args.salida)
        os.makedirs(destino, exist_ok=True)
        ruta = os.path.join(destino, "becas_y_comedor.json")
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(doc.model_dump(mode="json"), fh, ensure_ascii=False, indent=2)
        print(f"\nEscrito en {ruta}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
