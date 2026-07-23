import re
import unicodedata
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func


from app.application.ports.repository_ports import CorpusRepositoryPort
from app.application.dtos.rag_dtos import RetrievedChunkDTO
from app.infrastructure.database.models.corpus_chunk import CorpusChunk

STOP_WORDS = {
    "como", "para", "sobre", "entre", "hasta", "desde", "donde", "cuando",
    "quien", "cual", "cuales", "esta", "este", "estos", "estas", "tienen",
    "tiene", "hacer", "puedo", "puede", "pueden", "tengo", "unas", "unos",
    "cada", "todo", "todos", "toda", "todas", "otro", "otra", "que", "los",
    "las", "del", "con", "por", "una", "uno", "unos", "unas", "realizar",
    "dame", "informacion", "cuales", "son", "sobre", "mas", "hola", "gracias",
    "buenos", "dias", "tardes", "noches", "saludos", "favor", "ayuda", "necesito"
}


def _normalized_text(token: str) -> str:
    if not token:
        return ""
    nfkd = unicodedata.normalize("NFKD", token.casefold())
    cleaned = "".join(c for c in nfkd if not unicodedata.combining(c))
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


_normalized_stopword_key = _normalized_text


def _stem_plural(term: str) -> str:
    norm = _normalized_text(term)
    if len(norm) > 4:
        if norm.endswith("es"):
            return norm[:-2]
        if norm.endswith("s"):
            return norm[:-1]
    return norm


def _sql_accent_lower(col):
    return func.lower(func.translate(col, 'áéíóúÁÉÍÓÚñÑ', 'aeiouAEIOUnN'))


class CorpusRepository(CorpusRepositoryPort):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_similar(
        self,
        query_embedding: List[float],
        *,
        limit: int,
        query_text: str | None,
        max_cosine_distance: float,
        keyword_fallback_limit: int,
    ) -> List[RetrievedChunkDTO]:
        candidate_limit = max(limit * 3, limit)
        distance_expr = CorpusChunk.embedding.cosine_distance(query_embedding).label("cosine_distance")

        result = await self.db.execute(
            select(CorpusChunk, distance_expr)
            .where(CorpusChunk.embedding.is_not(None))
            .order_by(distance_expr)
            .limit(candidate_limit)
        )

        rows = result.all()
        retrieved: List[RetrievedChunkDTO] = []
        seen_texts: set[str] = set()

        # max_cosine_distance = 0.45 corresponds to min_similarity >= 0.55
        for chunk, dist in rows:
            dist_val = float(dist) if dist is not None else None
            if dist_val is not None and dist_val <= max_cosine_distance:
                if chunk.text_content not in seen_texts:
                    seen_texts.add(chunk.text_content)
                    retrieved.append(
                        RetrievedChunkDTO(
                            text=chunk.text_content,
                            source=chunk.source,
                            cosine_distance=dist_val,
                            retrieval_method="vector"
                        )
                    )
                    if len(retrieved) >= limit:
                        break

        # Check if query is about malla / plan de estudios
        raw_norm = _normalized_text(query_text or "")
        is_malla_or_plan_query = "malla" in raw_norm or "plan" in raw_norm

        needed = limit - len(retrieved)

        # Force plan-aware retrieval if query is about malla/plan OR vector results are insufficient
        if (is_malla_or_plan_query or needed > 0) and keyword_fallback_limit > 0 and query_text:
            words = re.findall(r"\w+", query_text.casefold())

            clean_terms = []
            seen_terms = set()
            for w in words:
                norm_w = _normalized_text(w)
                if len(norm_w) >= 3 and norm_w not in STOP_WORDS and norm_w not in seen_terms:
                    seen_terms.add(norm_w)
                    clean_terms.append(w)

            if is_malla_or_plan_query and "malla" not in [t.lower() for t in clean_terms]:
                clean_terms.append("malla")

            if clean_terms:
                clean_stems = [_stem_plural(t) for t in clean_terms]
                or_conditions = []
                for st in clean_stems[:6]:
                    or_conditions.append(_sql_accent_lower(CorpusChunk.text_content).like(f"%{st}%"))
                    or_conditions.append(_sql_accent_lower(CorpusChunk.source).like(f"%{st}%"))

                if is_malla_or_plan_query:
                    kw_query = select(CorpusChunk).where(or_(*or_conditions)).order_by(CorpusChunk.source.desc(), CorpusChunk.id).limit(100)
                else:
                    kw_query = select(CorpusChunk).where(or_(*or_conditions)).limit(40)

                kw_result = await self.db.execute(kw_query)
                kw_candidates = kw_result.scalars().all()


                scored_candidates = []
                num_stems = len(clean_stems)

                for cand in kw_candidates:
                    c_text_norm = _normalized_text(cand.text_content or "")
                    c_source_norm = _normalized_text(cand.source or "")
                    c_text_stems = [_stem_plural(w) for w in c_text_norm.split()]
                    c_source_stems = [_stem_plural(w) for w in c_source_norm.split()]

                    matched_stems = set()
                    source_matched_stems = set()
                    for st in clean_stems:
                        if st in c_text_norm or any(st in s for s in c_text_stems):
                            matched_stems.add(st)
                        if st in c_source_norm or any(st in s for s in c_source_stems):
                            matched_stems.add(st)
                            source_matched_stems.add(st)

                    match_count = len(matched_stems)
                    if match_count == 0:
                        continue

                    # Minimum threshold check
                    if num_stems == 1:
                        if len(clean_stems[0]) < 5:
                            continue
                    else:
                        match_ratio = match_count / num_stems
                        if match_ratio < 0.2 and not is_malla_or_plan_query:
                            continue

                    match_ratio = match_count / num_stems if num_stems > 0 else 0.0

                    exact_phrase_bonus = 15.0 if raw_norm in c_text_norm or raw_norm in c_source_norm else 0.0
                    source_bonus = len(source_matched_stems) * 8.0

                    consecutive_bonus = 0.0
                    for i in range(len(clean_stems) - 1):
                        bigram = f"{clean_stems[i]} {clean_stems[i+1]}"
                        if bigram in c_text_norm or bigram in c_source_norm:
                            consecutive_bonus += 6.0

                    score = (match_count * 12.0) + (match_ratio * 20.0) + exact_phrase_bonus + source_bonus + consecutive_bonus

                    if score < 5.0 and not is_malla_or_plan_query:
                        continue

                    cand_id = getattr(cand, "id", 0) or 0
                    scored_candidates.append((score, cand_id, cand))

                # Deterministic sort by score descending, then cand_id ascending
                scored_candidates.sort(key=lambda x: (x[0], -x[1]), reverse=True)

                # Dynamic plan grouping
                plan_groups: dict[str, list] = {}
                for score, cid, c in scored_candidates:
                    if c.text_content in seen_texts:
                        continue
                    src = c.source or ""
                    txt = c.text_content or ""
                    years = re.findall(r"\b(19\d\d|20\d\d)\b", f"{src} {txt[:150]}")
                    if years:
                        p_year = years[0]
                    else:
                        p_year = src or "general"
                    plan_groups.setdefault(p_year, []).append(c)

                selected_kw_chunks = []
                selected_sources = set()

                if is_malla_or_plan_query and len(plan_groups) > 1:
                    for p_year in sorted(plan_groups.keys()):
                        group_chunks = plan_groups[p_year]
                        for c in group_chunks:
                            if c.text_content not in seen_texts:
                                seen_texts.add(c.text_content)
                                selected_sources.add(c.source or "desconocido")
                                selected_kw_chunks.append(c)
                                break

                for score, cid, c in scored_candidates:
                    if c.text_content in seen_texts:
                        continue
                    src = c.source or "desconocido"
                    if src not in selected_sources or len(selected_sources) == 1 or needed > 0:
                        selected_sources.add(src)
                        seen_texts.add(c.text_content)
                        selected_kw_chunks.append(c)
                        if is_malla_or_plan_query:
                            if len(retrieved) + len(selected_kw_chunks) >= limit:
                                break
                        elif len(selected_kw_chunks) >= min(needed, keyword_fallback_limit):
                            break

                if is_malla_or_plan_query and selected_kw_chunks:
                    all_chunks = retrieved + [
                        RetrievedChunkDTO(
                            text=c.text_content,
                            source=c.source,
                            cosine_distance=None,
                            retrieval_method="keyword"
                        )
                        for c in selected_kw_chunks
                    ]
                    final_chunks = []
                    seen_final_texts = set()

                    plan_seen_years = set()
                    for dto in all_chunks:
                        if dto.text in seen_final_texts:
                            continue
                        years = re.findall(r"\b(19\d\d|20\d\d)\b", f"{dto.source} {dto.text[:150]}")
                        y_key = years[0] if years else dto.source
                        if y_key not in plan_seen_years:
                            plan_seen_years.add(y_key)
                            seen_final_texts.add(dto.text)
                            final_chunks.append(dto)
                            if len(final_chunks) >= limit:
                                break

                    if len(final_chunks) < limit:
                        for dto in all_chunks:
                            if dto.text not in seen_final_texts:
                                seen_final_texts.add(dto.text)
                                final_chunks.append(dto)
                                if len(final_chunks) >= limit:
                                    break

                    return final_chunks[:limit]

                for c in selected_kw_chunks:
                    retrieved.append(
                        RetrievedChunkDTO(
                            text=c.text_content,
                            source=c.source,
                            cosine_distance=None,
                            retrieval_method="keyword"
                        )
                    )

        return retrieved[:limit]





    async def insert_chunk(self, text: str, embedding: List[float], source: str = None):
        chunk = CorpusChunk(
            source=source,
            text_content=text,
            embedding=embedding
        )
        self.db.add(chunk)
        await self.db.commit()
