"""Convierte el portal de la Escuela Profesional a fragmentos del corpus.

El corpus cubria la norma universitaria pero no la escuela concreta a la que
pertenece quien pregunta. Cinco consultas frecuentes no tenian de donde salir:
mision y vision de la carrera, quienes son sus autoridades, cuando es su
aniversario, que circulos de estudio existen y que eventos organiza.

Nada de esto es articulado, asi que ningun fragmento lleva numero de articulo y
todos quedan en el nivel de autoridad mas bajo. Es lo correcto: el portal es
fuente oficial de la escuela para su propia identidad, pero no desplaza a un
reglamento cuando ambos hablan del mismo tema.

Cada hito historico y el circulo de estudios si citan la resolucion que los
respalda, porque el portal la publica y sin ella la respuesta no es verificable.

Uso:
    python -m scripts.extract_escuela
    python -m scripts.extract_escuela --dry-run
"""
import argparse
import json
import os
import re
import sys
import unicodedata

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app.application.dtos.corpus_dtos import (  # noqa: E402
    DocumentoCorpus,
    Fragmento,
    Procedencia,
    TipoDocumento,
)

ESCUELA = "Escuela Profesional de Ingeniería Informática y de Sistemas UNSAAC"


def slug(texto: str) -> str:
    """Identificador estable: sin tildes, sin parentesis y sin espacios.

    El id viaja a la base como `fragment_id` y es la clave de la ingesta
    incremental, asi que conviene que sea ASCII y estable entre corridas.
    """
    nfkd = unicodedata.normalize("NFKD", str(texto).casefold())
    limpio = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", limpio).strip("-")[:50] or "s"


def encabezado(*ruta: str) -> str:
    """Prefijo jerarquico que vuelve autocontenido al fragmento."""
    return " > ".join((ESCUELA, *ruta))


def frag(id_: str, titulo: str, cuerpo: str, seccion: list[str], claves: list[str]) -> Fragmento:
    return Fragmento(
        id=f"escuela_informatica#{id_}",
        titulo=titulo,
        texto=f"{encabezado(titulo)}\n{cuerpo}",
        seccion=["escuela_informatica", *seccion],
        palabras_clave=claves,
    )


# El portal dice "Escuela Profesional"; el estudiante dice "la carrera". Medido,
# "cual es la vision de la carrera" quedaba a distancia 0.364 -fuera del umbral
# calibrado de 0.34- y ademas sin coincidencia lexica, porque la palabra
# "carrera" no aparecia en el texto. Ambos fragmentos nombran ahora las dos
# formas, en vez de aflojar un umbral que se calibro contra el golden set.
def fragmento_mision(datos: dict) -> Fragmento:
    return frag(
        "mision",
        "Misión de la Escuela Profesional",
        "¿Cuál es la misión de la carrera? La misión de la carrera de Ingeniería Informática y de "
        f'Sistemas de la UNSAAC, es decir de la {ESCUELA}, es: "{datos["mision"]}"',
        ["identidad_academica"],
        ["misión", "carrera", "ingeniería informática"],
    )


def fragmento_vision(datos: dict) -> Fragmento:
    return frag(
        "vision",
        "Visión de la Escuela Profesional",
        "¿Cuál es la visión de la carrera? La visión de la carrera de Ingeniería Informática y de "
        f'Sistemas de la UNSAAC, es decir de la {ESCUELA}, es: "{datos["vision"]}"',
        ["identidad_academica"],
        ["visión", "carrera", "ingeniería informática"],
    )


def fragmento_historia(datos: dict) -> Fragmento:
    hitos = datos["resena_historica"]["hitos"]
    lineas = [
        f"- {h['fecha']}: {h['hecho']} ({h['resolucion']})." for h in hitos
    ]
    return frag(
        "resena-historica",
        "Reseña histórica de la Escuela Profesional",
        "La carrera de Ingeniería Informática y de Sistemas de la UNSAAC recorrió estos hitos:\n\n"
        + "\n".join(lineas),
        ["identidad_academica"],
        ["historia", "creación", "reapertura", "fundación"],
    )


def fragmento_aniversario(datos: dict) -> Fragmento:
    a = datos["aniversario"]
    creacion = datos["resena_historica"]["hitos"][0]
    reapertura = next(h for h in datos["resena_historica"]["hitos"] if "Reapertura" in h["hecho"])

    celebraciones = "; ".join(
        f"{c['edicion']} ({c['fecha']})" for c in a["celebraciones_documentadas"]
    )
    # Medido: "cuando es el aniversario de la carrera" quedaba a distancia 0.394
    # y el umbral calibrado corta en 0.34, asi que el sistema se abstenia con la
    # respuesta indexada. El fragmento arranca ahora con la formulacion que usa
    # el estudiante -"la carrera", no "la Escuela Profesional"- en vez de
    # aflojar un umbral que se calibro contra el golden set.
    return frag(
        "aniversario",
        "Aniversario de la carrera de Ingeniería Informática y de Sistemas",
        "¿Cuándo es el aniversario de la carrera? La carrera de Ingeniería Informática y de "
        f"Sistemas de la UNSAAC celebra su aniversario en {a['mes_de_celebracion']}. "
        f"El portal de la escuela declara como fecha de creación el {creacion['fecha']} "
        f"({creacion['resolucion']}) y como fecha de reapertura el {reapertura['fecha']} "
        f"({reapertura['resolucion']}). Celebraciones documentadas: {celebraciones}. "
        f"{a['advertencia']}",
        ["identidad_academica", "aniversario"],
        ["aniversario", "cumpleaños", "fundación", "diciembre"],
    )


def fragmento_autoridades(datos: dict) -> Fragmento:
    lineas = []
    for c in datos["autoridades"]["cargos"]:
        telefono = f", teléfono {c['telefono']}" if c.get("telefono") else ""
        lineas.append(f"- {c['ambito']} — {c['cargo']}: {c['nombre']} ({c['correo']}{telefono}).")

    return frag(
        "autoridades",
        "Autoridades de Ingeniería Informática y de Sistemas",
        "Las autoridades que dirigen la carrera de Ingeniería Informática y de Sistemas de la "
        "UNSAAC son:\n\n" + "\n".join(lineas),
        ["autoridades"],
        ["autoridades", "director", "decano", "jefe de departamento"],
    )


def fragmentos_docentes(datos: dict) -> list[Fragmento]:
    """Un fragmento por categoria docente.

    Se parte por la categoria que usa el propio portal y no por longitud: la
    consulta real es "quien dicta en la escuela" o "cual es el correo de X", y
    ambas se resuelven dentro de una categoria.
    """
    fragmentos = []
    for grupo in datos["equipo_docente"]:
        categoria = grupo["categoria"]
        clave = slug(categoria)
        lineas = [f"- {d['nombre']} ({d['correo']})." for d in grupo["docentes"]]
        fragmentos.append(
            frag(
                f"docentes-{clave}",
                f"Equipo docente: {categoria.lower()}",
                f"{categoria} del Departamento Académico de Ingeniería Informática de la UNSAAC "
                f"({len(grupo['docentes'])} docentes):\n\n" + "\n".join(lineas),
                ["equipo_docente"],
                ["docentes", "profesores", "correo"],
            )
        )
    return fragmentos


def fragmentos_circulos(datos: dict) -> list[Fragmento]:
    fragmentos = []
    for circulo in datos["circulos_de_estudio"]:
        clave = slug(circulo["nombre"])
        subgrupos = (
            " Subgrupos: " + " ".join(circulo["subgrupos"]) if circulo.get("subgrupos") else ""
        )
        # Que es y que se propone van separados: "que circulos de estudio hay"
        # y "que hace el ACM" son consultas distintas y el fragmento unico
        # (1655 caracteres) respondia mal a las dos.
        # El ambito se declara porque no todos son de la escuela: uno es de la
        # facultad y esta abierto a sus cinco escuelas. Decir que es "de la
        # carrera" seria pasarse de lo que dice la fuente.
        pertenencia = (
            "cuenta con el círculo de estudios"
            if circulo.get("ambito") == "carrera"
            else "puede participar en el círculo de estudios de su facultad"
        )
        # Mismo caso que el aniversario: "que circulos de estudio hay en la
        # carrera" quedaba a 0.371, fuera del umbral de 0.34.
        fragmentos.append(
            frag(
                f"circulo-{clave}",
                f"Círculo de estudios {circulo['nombre']}",
                "¿Qué círculos de estudio hay en la carrera? La carrera de Ingeniería Informática "
                f"y de Sistemas de la UNSAAC {pertenencia} "
                f"{circulo['nombre']}, reconocido mediante {circulo['resolucion']}. "
                f"{circulo['fundacion']}{subgrupos}",
                ["circulos_de_estudio"],
                ["círculo de estudios", "ACM", "grupo estudiantil"],
            )
        )
        objetivos = "\n".join(f"- {o}" for o in circulo["objetivos"])
        fragmentos.append(
            frag(
                f"circulo-{clave}-objetivos",
                f"Misión, visión y objetivos del círculo de estudios {circulo['nombre']}",
                f"Misión de {circulo['nombre']}: {circulo['mision']}\n"
                f"Visión: {circulo['vision']}\n"
                f"Objetivos:\n{objetivos}",
                ["circulos_de_estudio"],
                ["círculo de estudios", "ACM", "objetivos"],
            )
        )

    for org in datos["organizaciones_estudiantiles"]:
        fragmentos.append(
            frag(
                f"organizacion-{slug(org['nombre'])}",
                org["nombre"],
                f"{org['descripcion']} {org['base_legal']}",
                ["organizaciones_estudiantiles"],
                ["centro federado", "gremio", "representación estudiantil"],
            )
        )

    return fragmentos


def fragmentos_eventos(datos: dict) -> list[Fragmento]:
    """Un fragmento indice mas uno por evento.

    Juntar los cinco eventos en un solo fragmento daba 2126 caracteres y diluia
    su embedding entre un concurso de programacion, uno de IA, un seminario de
    infraestructura y una charla de movilidad, que no se parecen entre si. El
    indice queda para la consulta generica ("que eventos hay en la carrera") y
    cada evento responde por su nombre.
    """
    # El indice nombra el tipo de cada evento y no solo su nombre: "CUSCONTEST"
    # suelto no le dice nada a quien pregunta que concursos hay en la carrera.
    nombres = ", ".join(f"{e['nombre']} ({e['tipo'].lower()})" for e in datos["eventos"])
    indice = frag(
        "eventos",
        "Eventos habituales de la carrera de Ingeniería Informática y de Sistemas",
        "La Escuela Profesional y sus organizaciones estudiantiles convocan de forma habitual "
        f"estos eventos: {nombres}. Las fechas de cada edición se publican en el portal de la "
        "escuela y cambian en cada convocatoria.",
        ["eventos"],
        ["eventos", "actividades", "concursos", "carrera"],
    )

    detalle = [
        frag(
            f"evento-{slug(e['nombre'])}",
            f"Evento: {e['nombre']}",
            f"{e['nombre']} es un/a {e['tipo'].lower()} de la carrera de Ingeniería Informática y "
            f"de Sistemas de la UNSAAC. {e['descripcion']} Periodicidad: {e['periodicidad']} "
            f"Última edición documentada: {e['edicion_documentada']}",
            ["eventos"],
            [e["nombre"], e["tipo"]],
        )
        for e in datos["eventos"]
    ]

    return [indice, *detalle]


def fragmento_acreditacion(datos: dict) -> Fragmento:
    a = datos["acreditacion"]
    return frag(
        "acreditacion",
        "Acreditación de la Escuela Profesional",
        f"La {ESCUELA} cuenta con acreditación de {a['acreditadora']}, vigente {a['vigencia']}. "
        f"La escuela se encuentra {a['estado']}.",
        ["acreditacion"],
        ["acreditación", "ICACIT", "calidad"],
    )


def fragmento_contacto(datos: dict) -> Fragmento:
    c = datos["contacto"]
    return frag(
        "contacto",
        "Contacto de la Escuela Profesional",
        f"Correo de la Escuela Profesional: {c['correo']}. Dirección: {c['direccion']}. "
        f"Teléfonos de la Facultad de Ingeniería Eléctrica, Electrónica, Informática y Mecánica: "
        f"{c['telefono_facultad']}.",
        ["contacto"],
        ["contacto", "correo", "teléfono", "dirección"],
    )


def fragmento_mallas(datos: dict) -> Fragmento:
    lineas = []
    for m in datos["mallas_publicadas"]:
        resolucion = f", aprobada por {m['resolucion']}" if m.get("resolucion") else ""
        lineas.append(f"- Malla curricular {m['plan']} ({m['formato']}){resolucion}: {m['url']}")
    return frag(
        "mallas-publicadas",
        "Mallas curriculares publicadas por la Escuela Profesional",
        "La Escuela Profesional publica tres mallas curriculares en su portal. La vigente para "
        "los ingresantes es la 2025; las anteriores siguen publicadas porque hay estudiantes que "
        "cursan bajo ellas:\n\n" + "\n".join(lineas),
        ["malla_curricular"],
        ["malla curricular", "plan de estudios", "2017", "2025", "1997"],
    )


def construir(datos: dict) -> DocumentoCorpus:
    procedencia = Procedencia(
        documento=f"Portal institucional de la {ESCUELA}",
        tipo=TipoDocumento.SERVICIO,
        anio=2026,
        url=datos["fuente"]["url"],
        base_legal=["Estatuto de la UNSAAC", "Ley Universitaria 30220"],
    )

    fragmentos = [
        fragmento_mision(datos),
        fragmento_vision(datos),
        fragmento_historia(datos),
        fragmento_aniversario(datos),
        fragmento_autoridades(datos),
        *fragmentos_docentes(datos),
        *fragmentos_circulos(datos),
        *fragmentos_eventos(datos),
        fragmento_acreditacion(datos),
        fragmento_mallas(datos),
        fragmento_contacto(datos),
    ]

    return DocumentoCorpus(procedencia=procedencia, fragmentos=fragmentos)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convierte el portal de la escuela a fragmentos")
    parser.add_argument("--json", default="corpus_fuentes/escuela_informatica.json")
    parser.add_argument("--salida", default="corpus_estructurado")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with open(os.path.join(BACKEND_DIR, args.json), encoding="utf-8") as fh:
        datos = json.load(fh)

    doc = construir(datos)
    docentes = sum(len(g["docentes"]) for g in datos["equipo_docente"])
    print(f"fragmentos : {len(doc.fragmentos)}")
    print(f"docentes   : {docentes}")
    print(f"eventos    : {len(datos['eventos'])}")

    largos = [(len(f.texto), f.id) for f in doc.fragmentos]
    print(f"texto max  : {max(largos)[0]} chars ({max(largos)[1]})")

    if not args.dry_run:
        destino = os.path.join(BACKEND_DIR, args.salida)
        os.makedirs(destino, exist_ok=True)
        ruta = os.path.join(destino, "escuela_informatica.json")
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(doc.model_dump(mode="json"), fh, ensure_ascii=False, indent=2)
        print(f"\nEscrito en {ruta}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
