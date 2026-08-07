"""Fase 1 - Convierte el corpus heredado al esquema unico de DocumentoCorpus.

No inventa contenido normativo: reorganiza el texto que ya existe y deja
explicito lo que falta (articulo nulo, resolucion nula) para que la Fase 2 tenga
una lista de trabajo verificable en vez de una impresion.

Dos cambios de fondo respecto del formato heredado:

1. La granularidad deja de depender de la forma del JSON. Antes, un dict de 3760
   bytes con nueve subclaves se convertia en UN solo fragmento, y su embedding
   quedaba como centroide de nueve temas distintos. Ahora se desciende hasta que
   el fragmento entra en el limite de tamano.
2. Las secciones conversacionales (saludos, despedidas) se separan del contenido
   institucional en vez de indexarse junto al articulado.

Uso:
    python -m scripts.convert_corpus
    python -m scripts.convert_corpus --salida corpus_estructurado --dry-run
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from typing import Any

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app.application.dtos.corpus_dtos import (  # noqa: E402
    MAX_CARACTERES_TEXTO,
    SECCIONES_NO_NORMATIVAS,
    DocumentoCorpus,
    Fragmento,
    Procedencia,
    TipoDocumento,
)

CORPUS_ORIGEN = os.path.join(BACKEND_DIR, "corpus")

# Claves de nivel superior que describen el documento, no su contenido.
CLAVES_METADATO = {
    "universidad",
    "nombre_completo",
    "reglamento",
    "documento",
    "organo_responsable",
    "base_legal",
    "resolucion",
    "escuela_profesional",
}

TIPOS_POR_ARCHIVO = {
    "cronograma_academico.json": TipoDocumento.CRONOGRAMA,
    "glosario.json": TipoDocumento.GLOSARIO,
    "malla_curricular_2017.json": TipoDocumento.MALLA,
    "malla_curricular_2025.json": TipoDocumento.MALLA,
    "preguntas_frecuentes.json": TipoDocumento.FAQ,
    "reglamento_intercambio_estudiantil.json": TipoDocumento.REGLAMENTO,
    "reglamento_tutoria.json": TipoDocumento.REGLAMENTO,
    "servicios_biblioteca.json": TipoDocumento.REGLAMENTO,
    "servicios_bienestar.json": TipoDocumento.SERVICIO,
}

# Documentos heredados que quedaron reemplazados por una fuente con articulado.
# Sin esta lista, volver a correr la conversion los resucita y deshace en
# silencio dos decisiones ya tomadas: el reglamento de intercambio no declaraba
# resolucion y tenia 12/12 fragmentos sin articulo, y la malla 2017 heredada se
# rehizo desde la imagen oficial en malla_2017.json.
DOCUMENTOS_RETIRADOS = {
    "reglamento_intercambio_estudiantil.json": "reemplazado por reglamento_movilidad_academica (CU-349-2026)",
    "malla_curricular_2017.json": "reemplazado por malla_2017.json, transcrito de la imagen oficial",
}

# Fragmentos que quedaron superados por articulado real. Al ser parafrasis sin
# fuente competian con el y le ganaban: medido, "que servicios de apoyo ofrece
# la universidad" devolvia cuatro fragmentos de servicios_bienestar y dejaba
# fuera el articulo del Estatuto que responde la pregunta.
#
# Se retira solo lo que ya es citable en otro documento. Lo que no esta en la
# norma -el examen medico del ingresante, el uso del estadio, la orientacion
# ante el estres- se conserva, que es la razon por la que el documento sigue.
FRAGMENTOS_SUPERADOS = {
    "servicios_bienestar.json": {
        "finalidad-y-objetivos": "Estatuto Art. 245-246",
        "estructura-de-servicios-unidad-de-salud-y-psicopedagogia": "ROF Art. 108-109",
        "estructura-de-servicios-unidad-de-comedor-universitario": "ROF Art. 110-111 y Estatuto Art. 252",
        "estructura-de-servicios-unidad-de-asistencia-social": "ROF Art. 106-107",
        "estructura-de-servicios-unidad-de-deportes-y-recreacion": "ROF Art. 114-115",
        "beneficiarios": "Estatuto Art. 247",
        "preguntas-frecuentes-como-puedo-acceder-al-comedor-universitario": "becas_y_comedor y Estatuto Art. 252",
        "preguntas-frecuentes-la-universidad-otorga-algun-tipo-de-beca": "becas_y_comedor y Reglamento del Instituto de Idiomas Art. 108-109",
    },
}

# Titulos oficiales para los archivos cuyo metadato heredado no identifica el
# documento (declaran solo el nombre de la universidad).
TITULOS_EXPLICITOS = {
    "reglamento_intercambio_estudiantil.json": "Reglamento de Intercambio Estudiantil y Movilidad Academica OCRI UNSAAC",
    "servicios_bienestar.json": "Servicios de Bienestar Universitario y Comedor UNSAAC",
    "preguntas_frecuentes.json": "Preguntas Frecuentes Generales UNSAAC",
}


def slug(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(texto).casefold())
    limpio = "".join(c for c in nfkd if not unicodedata.combining(c))
    limpio = re.sub(r"[^a-z0-9]+", "-", limpio)
    return limpio.strip("-")[:60] or "s"


def humanizar(clave: str) -> str:
    texto = str(clave).replace("_", " ").strip()
    # Las etiquetas tomadas de preguntas o terminos ya vienen redactadas; solo se
    # capitalizan las claves tecnicas del JSON.
    return texto if texto[:1].isupper() or "?" in texto else texto.capitalize()


def etiqueta_de_item(item: Any, indice: int) -> str:
    """Etiqueta legible para un elemento de lista.

    Se usa el texto real (pregunta, termino, nombre) y no su slug, porque la
    etiqueta termina como encabezado dentro del texto que se embebe: un slug
    truncado degradaria el vector del fragmento.
    """
    if isinstance(item, dict):
        for clave in ("pregunta", "termino", "nombre", "titulo"):
            valor = item.get(clave)
            if isinstance(valor, str) and valor.strip():
                return valor.strip()
    return str(indice)


def render(valor: Any) -> str:
    """Convierte un valor JSON en prosa plana, sin llaves ni comillas."""
    if isinstance(valor, dict):
        return ". ".join(f"{humanizar(k)}: {render(v)}" for k, v in valor.items())
    if isinstance(valor, list):
        if all(not isinstance(x, (dict, list)) for x in valor):
            return ", ".join(str(x) for x in valor)
        return " | ".join(render(x) for x in valor)
    return str(valor)


def descomponer(clave: str, valor: Any, ruta: list[str]) -> list[tuple[list[str], str]]:
    """Desciende hasta que cada fragmento entra en el limite de tamano.

    Devuelve pares (ruta_de_seccion, texto). Se corta el descenso cuando el valor
    ya cabe, cuando deja de ser un contenedor, o cuando dividirlo mas produciria
    fragmentos sin contexto suficiente.
    """
    ruta_actual = ruta + [clave]
    texto = render(valor)

    # El limite se mide sobre el texto final, que incluye el encabezado de ruta
    # anadido despues por texto_de_fragmento.
    presupuesto = MAX_CARACTERES_TEXTO - len(" > ".join(humanizar(p) for p in ruta_actual)) - 1

    if len(texto) <= presupuesto or not isinstance(valor, (dict, list)):
        return [(ruta_actual, texto)]

    resultado: list[tuple[list[str], str]] = []
    if isinstance(valor, dict):
        for k, v in valor.items():
            resultado.extend(descomponer(k, v, ruta_actual))
    else:
        for i, item in enumerate(valor):
            # Los elementos de lista se etiquetan por su contenido cuando es
            # posible, para que la seccion siga siendo legible.
            resultado.extend(descomponer(etiqueta_de_item(item, i), item, ruta_actual))
    return resultado


def texto_de_fragmento(ruta: list[str], texto: str) -> str:
    """Antepone la ruta como encabezado para que el fragmento sea autocontenido.

    Un fragmento aislado como "veinticinco (25) estudiantes" no es recuperable;
    con su ruta delante si lo es.
    """
    encabezado = " > ".join(humanizar(p) for p in ruta)
    return f"{encabezado}\n{texto}"


def convertir(nombre: str, datos: Any) -> DocumentoCorpus:
    tipo = TIPOS_POR_ARCHIVO.get(nombre, TipoDocumento.SERVICIO)

    if isinstance(datos, dict):
        titulo = TITULOS_EXPLICITOS.get(nombre) or datos.get("documento") or datos.get("reglamento")
        if not titulo or titulo == datos.get("universidad"):
            titulo = TITULOS_EXPLICITOS.get(nombre, nombre)
        resolucion = datos.get("resolucion")
        if not resolucion and isinstance(datos.get("reglamento"), str) and "Resoluci" in datos["reglamento"]:
            resolucion = datos["reglamento"]
        base_legal = datos.get("base_legal") or []
    else:
        titulo = TITULOS_EXPLICITOS.get(nombre, nombre)
        resolucion, base_legal = None, []

    anio = None
    m = re.search(r"\b(19\d\d|20\d\d)\b", nombre)
    if m:
        anio = int(m.group(1))

    procedencia = Procedencia(
        documento=str(titulo),
        tipo=tipo,
        resolucion=str(resolucion) if resolucion else None,
        anio=anio,
        base_legal=[str(b) for b in base_legal] if isinstance(base_legal, list) else [],
    )

    pares: list[tuple[list[str], str]] = []
    if isinstance(datos, dict):
        for clave, valor in datos.items():
            if clave in CLAVES_METADATO:
                continue
            pares.extend(descomponer(clave, valor, []))
    elif isinstance(datos, list):
        for i, item in enumerate(datos):
            pares.extend(descomponer(etiqueta_de_item(item, i), item, []))

    base_id = nombre.removesuffix(".json")
    superados = FRAGMENTOS_SUPERADOS.get(nombre, {})
    fragmentos: list[Fragmento] = []
    usados: set[str] = set()

    for ruta, texto in pares:
        if not texto.strip():
            continue
        sufijo = "-".join(slug(p) for p in ruta)
        if sufijo in superados:
            continue
        fid = f"{base_id}#{sufijo}"
        if fid in usados:
            n = 2
            while f"{fid}-{n}" in usados:
                n += 1
            fid = f"{fid}-{n}"
        usados.add(fid)

        fragmentos.append(
            Fragmento(
                id=fid,
                titulo=" > ".join(humanizar(p) for p in ruta),
                texto=texto_de_fragmento(ruta, texto),
                seccion=ruta,
                articulo=None,
            )
        )

    return DocumentoCorpus(procedencia=procedencia, fragmentos=fragmentos)


def tiene_articulado(ruta: str) -> bool:
    """True si el archivo ya fue extraido de un PDF y trae numeros de articulo.

    Protege el resultado de la Fase 2: volver a correr la conversion pisaria el
    articulado real con la parafrasis heredada, que es justamente lo que se
    estaba corrigiendo.
    """
    if not os.path.exists(ruta):
        return False
    try:
        with open(ruta, encoding="utf-8") as fh:
            datos = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return False
    return any(f.get("articulo") for f in datos.get("fragmentos", []))


def main() -> int:
    parser = argparse.ArgumentParser(description="Convierte el corpus heredado al esquema unico")
    parser.add_argument("--salida", default="corpus_estructurado")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--forzar", action="store_true",
        help="Sobrescribe incluso los documentos ya extraidos de PDF (destructivo)",
    )
    args = parser.parse_args()

    destino = os.path.join(BACKEND_DIR, args.salida)
    if not args.dry_run:
        os.makedirs(destino, exist_ok=True)

    total_frag = total_conv = 0
    print(f"{'archivo':44s} {'tipo':11s} {'frag':>5s} {'convers':>8s} {'p50':>5s} {'max':>6s}")
    print("-" * 86)

    for nombre in sorted(os.listdir(CORPUS_ORIGEN)):
        if not nombre.endswith(".json"):
            continue
        if nombre in DOCUMENTOS_RETIRADOS:
            print(f"{nombre:44s} {'retirado':11s} {DOCUMENTOS_RETIRADOS[nombre]}")
            continue
        with open(os.path.join(CORPUS_ORIGEN, nombre), encoding="utf-8") as fh:
            datos = json.load(fh)

        doc = convertir(nombre, datos)
        institucionales = [f for f in doc.fragmentos if not f.es_conversacional]
        conversacionales = [f for f in doc.fragmentos if f.es_conversacional]

        # Las plantillas de chat salen del documento institucional: no son norma y
        # no deben competir por los slots de recuperacion.
        doc = DocumentoCorpus(procedencia=doc.procedencia, fragmentos=institucionales)

        largos = sorted(len(f.texto) for f in institucionales) or [0]
        p50 = largos[len(largos) // 2]
        print(
            f"{nombre:44s} {doc.procedencia.tipo.value:11s} {len(institucionales):>5d} "
            f"{len(conversacionales):>8d} {p50:>5d} {max(largos):>6d}"
        )
        total_frag += len(institucionales)
        total_conv += len(conversacionales)

        if not args.dry_run:
            ruta_salida = os.path.join(destino, nombre)
            if not args.forzar and tiene_articulado(ruta_salida):
                print(f"{'':44s} {'':11s} omitido: ya extraido del PDF con articulado")
                continue
            with open(ruta_salida, "w", encoding="utf-8") as fh:
                json.dump(doc.model_dump(mode="json"), fh, ensure_ascii=False, indent=2)

    print("-" * 86)
    print(f"{'TOTAL':44s} {'':11s} {total_frag:>5d} {total_conv:>8d}")
    print(f"\nFragmentos conversacionales excluidos del corpus institucional: {total_conv}")
    if not args.dry_run:
        print(f"Escrito en {destino}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
