"""Recuperacion hibrida sobre el corpus: vectores + texto completo, fusionados por RRF.

Reemplaza el fallback por palabras clave anterior, que eran ~200 lineas de
heuristicas con constantes magicas (12.0, 20.0, 15.0, 8.0, 6.0, umbrales 5.0 y
0.2), casos especiales incrustados para "malla"/"plan" y busquedas
LIKE '%termino%' que no podian usar ningun indice.

Ahora hay dos ramas independientes:

- la vectorial, que captura similitud semantica aunque no compartan palabras;
- la lexica, sobre el indice GIN en espanol, que captura coincidencias exactas
  de codigos, numeros y nombres propios que el embedding diluye.

Se fusionan con Reciprocal Rank Fusion, que combina posiciones en vez de puntajes
y por lo tanto no necesita normalizar escalas incomparables entre si. Es el metodo
que la documentacion de pgvector recomienda para busqueda hibrida.
"""
from typing import List

from sqlalchemy import Float, func, literal, select
from sqlalchemy.dialects.postgresql import REGCONFIG
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.rag_dtos import RetrievedChunkDTO
from app.application.ports.repository_ports import CorpusRepositoryPort
from app.infrastructure.database.models.corpus_chunk import CorpusChunk

CONFIGURACION_FTS = "spanish"


def fusionar_rrf(
    rankings: list[list[int]],
    k: int = 60,
) -> dict[int, float]:
    """Reciprocal Rank Fusion sobre varias listas de ids ya ordenadas.

    Cada lista aporta 1 / (k + posicion). Al operar sobre posiciones y no sobre
    puntajes, evita tener que normalizar una distancia coseno contra un ts_rank,
    que viven en escalas distintas y sin techo comun.
    """
    puntajes: dict[int, float] = {}
    for ranking in rankings:
        for posicion, chunk_id in enumerate(ranking, start=1):
            puntajes[chunk_id] = puntajes.get(chunk_id, 0.0) + 1.0 / (k + posicion)
    return puntajes


class CorpusRepository(CorpusRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _rama_vectorial(
        self,
        query_embedding: List[float],
        limite: int,
        max_cosine_distance: float,
    ) -> list[tuple[CorpusChunk, float]]:
        distancia = CorpusChunk.embedding.cosine_distance(query_embedding).label("distancia")
        resultado = await self.db.execute(
            select(CorpusChunk, distancia)
            .where(CorpusChunk.embedding.is_not(None))
            .where(distancia <= max_cosine_distance)
            .order_by(distancia)
            .limit(limite)
        )
        return [(chunk, float(dist)) for chunk, dist in resultado.all()]

    async def _rama_lexica(
        self,
        query_text: str,
        limite: int,
        min_ts_rank: float,
    ) -> list[tuple[CorpusChunk, float]]:
        if not query_text or not query_text.strip():
            return []

        # El primer argumento debe ser regconfig. Con un VARCHAR, Postgres no
        # encuentra la funcion y la consulta falla en tiempo de ejecucion; el
        # test unitario no lo detecta porque compila el SQL sin ejecutarlo.
        consulta = func.plainto_tsquery(
            literal(CONFIGURACION_FTS, type_=REGCONFIG), query_text
        )
        rank = func.ts_rank_cd(CorpusChunk.busqueda_ts, consulta).cast(Float).label("rank")

        resultado = await self.db.execute(
            select(CorpusChunk, rank)
            .where(CorpusChunk.busqueda_ts.op("@@")(consulta))
            .where(rank >= min_ts_rank)
            .order_by(rank.desc())
            .limit(limite)
        )
        return [(chunk, float(r)) for chunk, r in resultado.all()]

    async def search_similar(
        self,
        query_embedding: List[float],
        *,
        limit: int,
        query_text: str | None,
        max_cosine_distance: float,
        keyword_fallback_limit: int,
        candidatos_por_rama: int = 20,
        rrf_k: int = 60,
        min_ts_rank: float = 0.05,
    ) -> List[RetrievedChunkDTO]:
        candidatos = max(candidatos_por_rama, limit)

        vectoriales = await self._rama_vectorial(query_embedding, candidatos, max_cosine_distance)
        lexicos = (
            await self._rama_lexica(query_text, candidatos, min_ts_rank)
            if keyword_fallback_limit > 0 and query_text
            else []
        )

        # Sin evidencia en ninguna rama no se devuelve nada: el caso de uso se
        # abstiene en lugar de dejar que el LLM responda desde su conocimiento.
        if not vectoriales and not lexicos:
            return []

        distancias = {chunk.id: dist for chunk, dist in vectoriales}
        por_id: dict[int, CorpusChunk] = {}
        for chunk, _ in vectoriales:
            por_id[chunk.id] = chunk
        for chunk, _ in lexicos:
            por_id.setdefault(chunk.id, chunk)

        ids_vector = [chunk.id for chunk, _ in vectoriales]
        ids_lexico = [chunk.id for chunk, _ in lexicos]
        puntajes = fusionar_rrf([ids_vector, ids_lexico], k=rrf_k)

        en_vector, en_lexico = set(ids_vector), set(ids_lexico)

        # A igualdad de puntaje se ordena por id para que el resultado sea
        # reproducible entre corridas, algo que la evaluacion necesita.
        ordenados = sorted(puntajes.items(), key=lambda kv: (-kv[1], kv[0]))

        recuperados: List[RetrievedChunkDTO] = []
        textos_vistos: set[str] = set()

        for chunk_id, puntaje in ordenados:
            chunk = por_id.get(chunk_id)
            if chunk is None or chunk.text_content in textos_vistos:
                continue
            textos_vistos.add(chunk.text_content)

            if chunk_id in en_vector and chunk_id in en_lexico:
                metodo = "hibrido"
            elif chunk_id in en_vector:
                metodo = "vector"
            else:
                metodo = "texto"

            recuperados.append(
                RetrievedChunkDTO(
                    text=chunk.text_content,
                    source=chunk.source,
                    cosine_distance=distancias.get(chunk_id),
                    retrieval_method=metodo,
                    documento=chunk.documento,
                    articulo=chunk.articulo,
                    rrf_score=round(puntaje, 6),
                )
            )
            if len(recuperados) >= limit:
                break

        return recuperados

    async def insert_chunk(self, text: str, embedding: List[float], source: str = None):
        chunk = CorpusChunk(
            source=source,
            text_content=text,
            embedding=embedding
        )
        self.db.add(chunk)
        await self.db.commit()
