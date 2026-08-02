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
    "rof": {
        "archivo": "ROF2019_UNSAAC.pdf",
        "documento": "Reglamento de Organización y Funciones UNSAAC",
        "tipo": TipoDocumento.REGLAMENTO,
        "resolucion": "Resolución Nro. CU-210-2019-UNSAAC",
        "anio": 2019,
        "base_legal": [],
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


def partir_por_oraciones(parrafo: str, presupuesto: int) -> list[str]:
    """Ultimo recurso para un parrafo unico mas largo que el limite.

    Se corta en el punto final mas cercano y no a mitad de caracter, para no
    partir una frase normativa por la mitad.
    """
    if len(parrafo) <= presupuesto:
        return [parrafo]

    piezas, actual = [], ""
    for oracion in re.split(r"(?<=\.)\s+", parrafo):
        if actual and len(actual) + len(oracion) + 1 > presupuesto:
            piezas.append(actual)
            actual = oracion
        else:
            actual = f"{actual} {oracion}".strip()
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
    lineas = limpiar(texto.splitlines())

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

        articulos = extraer_articulos(texto_de_pdf(ruta))
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
