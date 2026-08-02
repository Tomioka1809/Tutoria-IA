"""Esquema unico del corpus documental (Fase 1).

Los nueve archivos originales usaban cuatro estructuras distintas, sin numeracion
de articulos y con procedencia opcional. Eso hacia imposible medir la metrica de
cobertura del golden set, que se expresa en articulos ("Art. 15 - Reglamento de
Tutoria"), y obligaba al chunker a adivinar la granularidad a partir de la forma
del JSON.

Este modulo fija el contrato: un documento declara su procedencia y se descompone
en fragmentos explicitos. El fragmento es la unidad de recuperacion, de modo que
el chunker deja de inferirla y pasa a respetarla.
"""
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

# Un fragmento demasiado corto no aporta contexto recuperable; uno demasiado largo
# diluye su embedding entre varios temas. Los limites se aplican como advertencia
# en el validador, no como error, para no bloquear la conversion inicial.
MIN_CARACTERES_TEXTO = 80
MAX_CARACTERES_TEXTO = 1200

# Secciones conversacionales que no son contenido institucional y no deben quedar
# indexadas compitiendo con el articulado.
SECCIONES_NO_NORMATIVAS = {
    "saludos_y_despedidas",
    "saludos",
    "despedidas",
    "agradecimientos",
    "respuestas_no_entendido",
}


class TipoDocumento(str, Enum):
    REGLAMENTO = "reglamento"
    CRONOGRAMA = "cronograma"
    MALLA = "malla"
    GLOSARIO = "glosario"
    FAQ = "faq"
    SERVICIO = "servicio"


class Procedencia(BaseModel):
    """De donde sale el documento. Sin esto una respuesta no es citable."""

    documento: str = Field(min_length=5)
    tipo: TipoDocumento
    universidad: str = "UNSAAC"
    # Deberia estar presente en todo reglamento, pero se admite nula porque los
    # archivos heredados no la declaran y no se inventan datos normativos. El
    # validador la exige en modo estricto: es un criterio de cierre de la Fase 2.
    resolucion: str | None = None
    anio: int | None = None
    url: str | None = None
    base_legal: list[str] = Field(default_factory=list)


class Fragmento(BaseModel):
    """Unidad de recuperacion. Un fragmento equivale a un chunk indexado."""

    id: str = Field(min_length=3)
    titulo: str = Field(min_length=3)
    texto: str = Field(min_length=1)
    # Ruta jerarquica dentro del documento, p. ej.
    # ["tutoria_universitaria", "numero_maximo_tutorados"].
    seccion: list[str] = Field(default_factory=list)
    # "Art. 15". Nulo mientras no se haya extraido del documento fuente; la Fase 2
    # consiste precisamente en llevar estos nulos a cero en los reglamentos.
    articulo: str | None = None
    palabras_clave: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def id_sin_espacios(cls, v: str) -> str:
        if " " in v:
            raise ValueError(f"El id de fragmento no puede contener espacios: {v!r}")
        return v

    @property
    def es_conversacional(self) -> bool:
        return any(s in SECCIONES_NO_NORMATIVAS for s in self.seccion)


class DocumentoCorpus(BaseModel):
    procedencia: Procedencia
    fragmentos: list[Fragmento]

    @model_validator(mode="after")
    def ids_unicos(self) -> "DocumentoCorpus":
        vistos = set()
        for f in self.fragmentos:
            if f.id in vistos:
                raise ValueError(f"Id de fragmento duplicado: {f.id}")
            vistos.add(f.id)
        return self

    @property
    def fragmentos_sin_articulo(self) -> list[Fragmento]:
        """Fragmentos normativos a los que todavia les falta numero de articulo."""
        if self.procedencia.tipo != TipoDocumento.REGLAMENTO:
            return []
        return [f for f in self.fragmentos if not f.articulo and not f.es_conversacional]
