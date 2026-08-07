"""Fase 2 - Extrae articulado real desde los PDF oficiales al esquema unico.

La Fase 1 dejo 83 fragmentos normativos sin numero de articulo porque el corpus
heredado era una parafrasis tematica que habia perdido el articulado. Este script
lo recupera de la fuente: parte cada documento por articulo, de modo que una
respuesta pueda citarse como "Art. 14 num. 2 - Reglamento de Tutoria".

Requiere pdftotext (poppler). Los PDF no viven en el repositorio; se indica su
ubicacion con --pdf-dir.

Uso:
    python -m scripts.extract_pdf_corpus --pdf-dir ~/Downloads/"coupus de pdfs"
    python -m scripts.extract_pdf_corpus --pdf-dir ... --solo reglamento_tutoria
"""
import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from app.application.dtos.corpus_dtos import (  # noqa: E402
    MAX_CARACTERES_TEXTO,
    DocumentoCorpus,
    Fragmento,
    Procedencia,
    TipoDocumento,
)

# Un articulo suelto ("Art. 2 Base Legal: Ley 30220") no aporta contexto propio;
# se fusiona con el siguiente para no reintroducir micro-fragmentos.
MIN_CARACTERES_ARTICULO = 60

DOCUMENTOS = {
    "reglamento_tutoria": {
        "archivo": "ReglamentoTutoriaAcademica.pdf",
        "documento": "Reglamento de Tutoría Académica UNSAAC",
        "tipo": TipoDocumento.REGLAMENTO,
        "resolucion": "Resolución Nro. CU-0220-2017-UNSAAC de 24.05.2017",
        "anio": 2017,
        "base_legal": ["Ley Universitaria 30220, Art. 87.5", "Estatuto de la UNSAAC, Art. 195.5"],
    },
    "reglamento_academico": {
        "archivo": "000_RegAcademicoUNSAAC2017(CU-093-2017-UNSAAC).pdf",
        "documento": "Reglamento Académico UNSAAC",
        "tipo": TipoDocumento.REGLAMENTO,
        "resolucion": "Resolución Nro. CU-0359-2015-UNSAAC, modificada por CU-093-2017-UNSAAC",
        "anio": 2017,
        "base_legal": ["Art. 88° del Estatuto Universitario"],
    },
    "estatuto": {
        "archivo": "EstatutoUniversitario_UNSAAC.pdf",
        "documento": "Estatuto Universitario UNSAAC",
        "tipo": TipoDocumento.REGLAMENTO,
        "resolucion": "Estatuto aprobado por la Asamblea Universitaria UNSAAC",
        "anio": 2015,
        "base_legal": ["Ley Universitaria 30220"],
    },
    # El ROF 2019 quedo superado. Se indexa el vigente: citar la version derogada
    # es peor que no citar, porque la respuesta se ve fundamentada y no lo esta.
    "rof": {
        "archivo": "ROF2024_UNSAAC.pdf",
        "documento": "Reglamento de Organización y Funciones UNSAAC",
        "tipo": TipoDocumento.REGLAMENTO,
        "resolucion": "Resolución Nro. AU-008-2024-UNSAAC, que modifica la CU-393-2023-UNSAAC",
        "anio": 2024,
        "base_legal": [
            "Resolución de Secretaría de Gestión Pública N° 003-2018-PCM/SGP",
            "Resolución Ministerial N° 588-2019-MINEDU",
        ],
    },
    "reglamento_vivienda_estudiantil": {
        "archivo": "CU-372-2020-reglamento-vivienda-estudiantil.pdf",
        "documento": "Reglamento para Uso de Vivienda Estudiantil UNSAAC",
        "tipo": TipoDocumento.REGLAMENTO,
        "resolucion": "Resolución Nro. CU-372-2020-UNSAAC de 05.11.2020",
        "anio": 2020,
        "base_legal": ["Ley Universitaria 30220", "Estatuto de la UNSAAC"],
    },
    # Unica norma publicada de la UNSAAC que articula becas de estudio para
    # estudiantes de pregrado (Cap. XII, Art. 108-118). Sin ella, "que becas
    # existen" solo se podia responder desde parafrasis sin fuente.
    "reglamento_idiomas": {
        "archivo": "CU-281-2020-reglamento-instituto-idiomas.pdf",
        "documento": "Reglamento del Instituto de Idiomas UNSAAC",
        "tipo": TipoDocumento.REGLAMENTO,
        "resolucion": "Resolución Nro. CU-281-2020-UNSAAC de 13.08.2020",
        "anio": 2020,
        "base_legal": ["Ley Universitaria 30220", "Estatuto de la UNSAAC"],
    },
    # Los dos siguientes son escaneos sin capa de texto. Se parten desde el
    # Markdown que produce el OCR en espanol (docling), no desde el PDF.
    "reglamento_movilidad_academica": {
        "archivo": "es_ocr/CU-349-2026-reglamento-movilidad-academica.md",
        "documento": "Reglamento del Programa de Movilidad Académica Estudiantil y Docente UNSAAC",
        "tipo": TipoDocumento.REGLAMENTO,
        "resolucion": "Resolución Nro. CU-349-2026-UNSAAC de 07.07.2026 (REGL 01-2026-OCRI-UNSAAC)",
        "anio": 2026,
        "base_legal": ["Ley Universitaria 30220", "Estatuto de la UNSAAC"],
    },
    "reglamento_subvenciones": {
        "archivo": "es_ocr/CU-667-2025-reglamento-subvenciones-economicas.md",
        "documento": "Reglamento para el Otorgamiento de Subvenciones Económicas UNSAAC",
        "tipo": TipoDocumento.REGLAMENTO,
        "resolucion": "Resolución Nro. CU-667-2025-UNSAAC",
        "anio": 2025,
        "base_legal": ["Ley Universitaria 30220", "Estatuto de la UNSAAC"],
    },
}

# "Art. 14°" en el reglamento de tutoria, "Artículo 244°" en el resto.
RE_ARTICULO = re.compile(
    r"^[ \t]*(?:Art[íi]culo|Art\.)\s*(\d+)\s*[°ºo]?\s*[.\-]?\s*(.*)$",
    re.IGNORECASE,
)
RE_JERARQUIA = re.compile(
    r"^[ \t]*(T[ÍI]TULO|CAP[ÍI]TULO|Cap[íi]tulo|T[íi]tulo)\s+([IVXLC]+)\b(.*)$"
)
# Subnumerales tipo "13.1" o listas "a." que dan puntos de corte naturales.
RE_SUBITEM = re.compile(r"^[ \t]*(\d+\.\d+\.?|[a-z]\.|\d+\.)\s+\S")


def slug(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(texto).casefold())
    limpio = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", limpio).strip("-")[:60] or "s"


def texto_de_pdf(ruta: str) -> str:
    salida = subprocess.run(
        ["pdftotext", "-layout", ruta, "-"],
        capture_output=True, text=True, check=True,
    )
    return salida.stdout


# El OCR no deja saltos de pagina, asi que el mueble de pagina se detecta por
# repeticion. El umbral separa la mueble (16-20 apariciones, una por pagina) del
# contenido que legitimamente se repite (4 como maximo en los documentos vistos).
MIN_REPETICIONES_MUEBLE_OCR = 8
RE_IMAGEN_EMBEBIDA = re.compile(r"!\[[^\]]*\]\([^)]*\)")
RE_SEPARADOR_TABLA = re.compile(r"^\s*\|[\s|:-]*\|\s*$")


def texto_de_markdown(contenido: str) -> str:
    """Normaliza el Markdown de un OCR al texto plano que espera el parser.

    Tres estorbos propios de esta fuente: las imagenes van embebidas en base64
    (2.44 MB de los 2.5 MB del reglamento de movilidad), el encabezado de cada
    pagina sale como fila de tabla repetida, y los titulos llevan '#', que
    impide que RE_ARTICULO reconozca "## Artículo 1°".
    """
    contenido = RE_IMAGEN_EMBEBIDA.sub("", contenido)

    lineas = contenido.splitlines()
    conteo: dict[str, int] = {}
    for linea in lineas:
        norm = _normalizar(linea)
        if norm:
            conteo[norm] = conteo.get(norm, 0) + 1
    mueble = {k for k, v in conteo.items() if v >= MIN_REPETICIONES_MUEBLE_OCR}

    limpias: list[str] = []
    for linea in lineas:
        norm = _normalizar(linea)
        if norm in mueble or RE_SEPARADOR_TABLA.match(linea):
            continue
        # "## Artículo 1°. - Objeto" -> "Artículo 1°. - Objeto"
        limpias.append(re.sub(r"^\s*#{1,6}\s*", "", linea))
    return "\n".join(limpias)


def texto_de_fuente(ruta: str) -> str:
    """Texto plano del documento, venga de un PDF con capa de texto o de un OCR.

    Un PDF escaneado no tiene nada que extraer con pdftotext, asi que su fuente
    es el Markdown del OCR. El articulado se parsea igual en ambos casos: lo que
    cambia es de donde sale el texto, no como se parte.
    """
    if ruta.lower().endswith(".md"):
        with open(ruta, encoding="utf-8") as fh:
            return texto_de_markdown(fh.read())
    return texto_de_pdf(ruta)


# Encabezado/pie que se repite en cada pagina. Filtrar solo por frecuencia no
# sirve: en texto justificado una linea corta como "Universidad." tambien se
# repite y es contenido. Lo que distingue a la mueble de pagina es su posicion,
# asi que se busca unicamente en los bordes de cada pagina.
LINEAS_BORDE_INSPECCIONADAS = 3
FRACCION_PAGINAS_BOILERPLATE = 0.3
RE_PIE_PAGINA = re.compile(r"^\s*(.*\bP[áa]gina\s*\d+\s*|\s*\d{1,3}\s*)$", re.IGNORECASE)


def _normalizar(linea: str) -> str:
    return re.sub(r"\s+", " ", linea).strip()


def quitar_encabezados_y_pies(texto: str) -> str:
    """Quita el encabezado y el pie que se repiten pagina a pagina.

    Sin esto el pie queda dentro del cuerpo del articulo y entra al embedding:
    el Art. 104 del ROF terminaba con "OFICINA DE PLANEAMIENTO... Pagina 54".
    """
    paginas = texto.split("\f")
    if len(paginas) < 3:
        return texto

    # Candidata: linea que aparece en el borde de una fraccion alta de paginas.
    conteo: dict[str, int] = {}
    for pagina in paginas:
        lineas = [l for l in pagina.splitlines() if l.strip()]
        borde = lineas[:LINEAS_BORDE_INSPECCIONADAS] + lineas[-LINEAS_BORDE_INSPECCIONADAS:]
        for norm in {_normalizar(l) for l in borde}:
            conteo[norm] = conteo.get(norm, 0) + 1

    minimo = max(2, int(len(paginas) * FRACCION_PAGINAS_BOILERPLATE))
    boilerplate = {k for k, v in conteo.items() if v >= minimo and k}

    def es_mueble(linea: str) -> bool:
        norm = _normalizar(linea)
        if not norm:
            return False
        return norm in boilerplate or bool(RE_PIE_PAGINA.fullmatch(norm))

    limpias: list[str] = []
    for pagina in paginas:
        lineas = pagina.splitlines()
        # Se pela el bloque contiguo del borde y se corta en la primera linea que
        # no es mueble. Marcar por ventana fija recortaba contenido en paginas
        # cortas, donde "los ultimos tres renglones" ya son cuerpo del articulo.
        ini = 0
        while ini < len(lineas) and (not lineas[ini].strip() or es_mueble(lineas[ini])):
            ini += 1
        fin = len(lineas)
        while fin > ini and (not lineas[fin - 1].strip() or es_mueble(lineas[fin - 1])):
            fin -= 1
        limpias.extend(lineas[ini:fin])
    return "\n".join(limpias)


def limpiar(lineas: list[str]) -> list[str]:
    """Quita numeros de pagina sueltos y saltos de formulario."""
    limpias = []
    for linea in lineas:
        l = linea.replace("\f", " ").rstrip()
        if re.fullmatch(r"\s*\d{1,3}\s*", l):
            continue
        limpias.append(l)
    return limpias


def unir_parrafo(lineas: list[str]) -> str:
    """Une lineas envueltas respetando los cortes de subnumeral y de parrafo."""
    partes: list[str] = []
    buffer: list[str] = []

    def volcar():
        if buffer:
            partes.append(" ".join(w.strip() for w in buffer if w.strip()))
            buffer.clear()

    for linea in lineas:
        if not linea.strip():
            volcar()
            continue
        if RE_SUBITEM.match(linea):
            volcar()
        buffer.append(linea)
    volcar()
    return "\n".join(p for p in partes if p)


def trocear_sin_puntos(unidad: str, presupuesto: int) -> list[str]:
    """Parte una unidad que excede el limite y no tiene puntos donde cortar.

    Las tablas del OCR llegan como una fila unica sin un solo punto final: el
    Art. 27 del reglamento de subvenciones daba un fragmento de 3033 caracteres,
    que diluye su embedding entre todos los conceptos de la tabla. Se corta
    primero por celda y, si aun no alcanza, por palabra.
    """
    if len(unidad) <= presupuesto:
        return [unidad]

    piezas: list[str] = []
    actual = ""
    for celda in re.split(r"\s*\|\s*", unidad):
        if not celda.strip():
            continue
        for palabra in celda.split(" ") if len(celda) > presupuesto else [celda]:
            if actual and len(actual) + len(palabra) + 1 > presupuesto:
                piezas.append(actual)
                actual = palabra
            else:
                actual = f"{actual} {palabra}".strip()
    if actual:
        piezas.append(actual)
    return piezas


def partir_por_oraciones(parrafo: str, presupuesto: int) -> list[str]:
    """Ultimo recurso para un parrafo unico mas largo que el limite.

    Se corta en el punto final mas cercano y no a mitad de caracter, para no
    partir una frase normativa por la mitad.
    """
    if len(parrafo) <= presupuesto:
        return [parrafo]

    piezas, actual = [], ""
    for oracion in re.split(r"(?<=\.)\s+", parrafo):
        # Una "oracion" mas larga que el presupuesto no se puede acomodar: hay
        # que trocearla o el fragmento sale del limite igual.
        for unidad in trocear_sin_puntos(oracion, presupuesto):
            if actual and len(actual) + len(unidad) + 1 > presupuesto:
                piezas.append(actual)
                actual = unidad
            else:
                actual = f"{actual} {unidad}".strip()
    if actual:
        piezas.append(actual)
    return piezas


def partir_articulo(cuerpo: str, presupuesto: int) -> list[str]:
    """Parte un articulo largo por sus parrafos, empaquetando hasta el limite."""
    if len(cuerpo) <= presupuesto:
        return [cuerpo]

    piezas: list[str] = []
    actual = ""
    for parrafo in cuerpo.split("\n"):
        if not parrafo.strip():
            continue
        for trozo in partir_por_oraciones(parrafo, presupuesto):
            if actual and len(actual) + len(trozo) + 1 > presupuesto:
                piezas.append(actual)
                actual = trozo
            else:
                actual = f"{actual}\n{trozo}" if actual else trozo
    if actual:
        piezas.append(actual)
    return piezas


def extraer_articulos(texto: str) -> list[dict]:
    """Devuelve [{numero, titulo, cuerpo, jerarquia}] en orden de aparicion."""
    lineas = limpiar(quitar_encabezados_y_pies(texto).splitlines())

    articulos: list[dict] = []
    # Titulo y capitulo se siguen por separado: anidarlos en una sola lista hacia
    # que un capitulo quedara colgando del anterior en documentos sin titulos.
    titulo_actual: str | None = None
    capitulo_actual: str | None = None
    actual: dict | None = None
    buffer: list[str] = []

    def jerarquia_actual() -> list[str]:
        return [x for x in (titulo_actual, capitulo_actual) if x]

    for linea in lineas:
        m_jer = RE_JERARQUIA.match(linea)
        if m_jer and not RE_ARTICULO.match(linea):
            etiqueta = f"{m_jer.group(1).title()} {m_jer.group(2)}".strip()
            resto = m_jer.group(3).strip(" .-")
            if resto:
                etiqueta = f"{etiqueta} - {resto}"
            if m_jer.group(1).upper().startswith("T"):
                titulo_actual = etiqueta
                capitulo_actual = None
            else:
                capitulo_actual = etiqueta
            continue

        m_art = RE_ARTICULO.match(linea)
        if m_art:
            if actual:
                actual["cuerpo"] = unir_parrafo(buffer)
                articulos.append(actual)
            actual = {
                "numero": int(m_art.group(1)),
                "titulo": m_art.group(2).strip(" .:-"),
                "jerarquia": jerarquia_actual(),
            }
            buffer = []
            # Cuando el titulo trae ya texto normativo, se conserva como cuerpo.
            continue

        if actual is not None:
            buffer.append(linea)

    if actual:
        actual["cuerpo"] = unir_parrafo(buffer)
        articulos.append(actual)

    return articulos


def construir_documento(clave: str, cfg: dict, articulos: list[dict]) -> DocumentoCorpus:
    procedencia = Procedencia(
        documento=cfg["documento"],
        tipo=cfg["tipo"],
        resolucion=cfg["resolucion"],
        anio=cfg.get("anio"),
        base_legal=cfg.get("base_legal", []),
    )

    fragmentos: list[Fragmento] = []
    usados: set[str] = set()
    pendiente: dict | None = None

    for art in articulos:
        titulo_art = art["titulo"] or f"Artículo {art['numero']}"
        cuerpo = art.get("cuerpo", "").strip()

        # Un articulo demasiado corto se arrastra al siguiente en vez de quedar
        # como fragmento sin contexto recuperable.
        if pendiente:
            cuerpo = f"{pendiente['encabezado']}\n{pendiente['cuerpo']}\n\n{cuerpo}".strip()
            art = {**art, "arrastra": pendiente["etiqueta"]}
            pendiente = None

        etiqueta_art = f"Art. {art['numero']}"
        encabezado_partes = art["jerarquia"] + [f"{etiqueta_art} - {titulo_art}"]
        encabezado = f"{procedencia.documento} > " + " > ".join(encabezado_partes)

        if len(cuerpo) < MIN_CARACTERES_ARTICULO:
            pendiente = {"encabezado": encabezado, "cuerpo": cuerpo, "etiqueta": etiqueta_art}
            continue

        presupuesto = MAX_CARACTERES_TEXTO - len(encabezado) - 1
        piezas = partir_articulo(cuerpo, max(presupuesto, 200))

        for i, pieza in enumerate(piezas):
            sufijo = f"-{i + 1}" if len(piezas) > 1 else ""
            fid = f"{clave}#art-{art['numero']}{sufijo}"
            if fid in usados:
                n = 2
                while f"{fid}-{n}" in usados:
                    n += 1
                fid = f"{fid}-{n}"
            usados.add(fid)

            fragmentos.append(
                Fragmento(
                    id=fid,
                    titulo=f"{etiqueta_art} - {titulo_art}",
                    texto=f"{encabezado}\n{pieza}",
                    seccion=art["jerarquia"] + [slug(titulo_art)],
                    articulo=etiqueta_art,
                )
            )

    if pendiente and fragmentos:
        # El ultimo articulo corto se anexa al fragmento previo.
        ultimo = fragmentos[-1]
        fragmentos[-1] = ultimo.model_copy(
            update={"texto": f"{ultimo.texto}\n\n{pendiente['encabezado']}\n{pendiente['cuerpo']}"}
        )

    return DocumentoCorpus(procedencia=procedencia, fragmentos=fragmentos)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extrae articulado desde los PDF oficiales")
    parser.add_argument("--pdf-dir", required=True, help="Carpeta con los PDF oficiales")
    parser.add_argument("--salida", default="corpus_estructurado")
    parser.add_argument("--solo", help="Procesar un solo documento por clave")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    pdf_dir = os.path.expanduser(args.pdf_dir)
    destino = os.path.join(BACKEND_DIR, args.salida)
    os.makedirs(destino, exist_ok=True)

    claves = [args.solo] if args.solo else list(DOCUMENTOS)
    print(f"{'documento':30s} {'arts':>5s} {'frag':>5s} {'p50':>5s} {'max':>6s}  rango")
    print("-" * 82)

    total = 0
    for clave in claves:
        cfg = DOCUMENTOS.get(clave)
        if not cfg:
            print(f"  clave desconocida: {clave}")
            continue
        ruta = os.path.join(pdf_dir, cfg["archivo"])
        if not os.path.exists(ruta):
            print(f"{clave:30s} FALTA el PDF: {cfg['archivo']}")
            continue

        articulos = extraer_articulos(texto_de_fuente(ruta))
        doc = construir_documento(clave, cfg, articulos)

        largos = sorted(len(f.texto) for f in doc.fragmentos) or [0]
        nums = [int(f.articulo.split()[-1]) for f in doc.fragmentos if f.articulo]
        rango = f"Art. {min(nums)}-{max(nums)}" if nums else "-"
        print(
            f"{clave:30s} {len(articulos):>5d} {len(doc.fragmentos):>5d} "
            f"{largos[len(largos) // 2]:>5d} {max(largos):>6d}  {rango}"
        )
        total += len(doc.fragmentos)

        if not args.dry_run:
            with open(os.path.join(destino, f"{clave}.json"), "w", encoding="utf-8") as fh:
                json.dump(doc.model_dump(mode="json"), fh, ensure_ascii=False, indent=2)

    print("-" * 82)
    print(f"{'TOTAL':30s} {'':>5s} {total:>5d}")
    if not args.dry_run:
        print(f"\nEscrito en {destino}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
