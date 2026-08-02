from pydantic import BaseModel, Field, model_validator
from typing import Literal


class RetrievedChunkDTO(BaseModel):
    text: str
    source: str | None = None
    cosine_distance: float | None = None
    retrieval_method: Literal["vector", "keyword", "texto", "hibrido"] = "vector"
    # Procedencia citable: permite que la respuesta referencie la norma exacta.
    documento: str | None = None
    articulo: str | None = None
    # Puntaje de la fusion reciproca; None cuando el recuperador no fusiona.
    rrf_score: float | None = None


class RAGRetrievalPolicy(BaseModel):
    limit: int = Field(default=6, gt=0)
    # Calibrado contra el golden set v2 con scripts.calibrar_umbral, no elegido a
    # ojo: en alcance las distancias van de 0.17 a 0.33 y fuera de alcance de
    # 0.29 a 0.44. Con 0.34 se conserva el 100% del recall en alcance y se
    # rechazan las consultas de otro dominio. El valor anterior, 0.45, dejaba
    # pasar las tres consultas fuera de alcance y rompia la abstencion.
    max_cosine_distance: float = Field(default=0.34, ge=0.0, le=2.0)
    keyword_fallback_limit: int = Field(default=2, ge=0)

    # --- Busqueda hibrida ---
    # Candidatos que aporta cada rama antes de fusionar. Mas candidatos mejoran el
    # recall de la fusion sin cambiar cuantos fragmentos se entregan al LLM.
    candidatos_por_rama: int = Field(default=20, gt=0)
    # Constante de Reciprocal Rank Fusion. 60 es el valor habitual: amortigua las
    # diferencias entre las primeras posiciones de cada ranking.
    rrf_k: int = Field(default=60, gt=0)
    # Piso de relevancia lexica. Sin el, una consulta fuera de alcance como
    # "derivada de una funcion" engancharia el curso "Calculo I" de la malla y
    # rompería la abstencion.
    min_ts_rank: float = Field(default=0.05, ge=0.0)

    @model_validator(mode="after")
    def validate_limits(self) -> "RAGRetrievalPolicy":
        if self.keyword_fallback_limit > self.limit:
            raise ValueError("keyword_fallback_limit must not exceed limit")
        if self.candidatos_por_rama < self.limit:
            raise ValueError("candidatos_por_rama must be at least limit")
        return self
