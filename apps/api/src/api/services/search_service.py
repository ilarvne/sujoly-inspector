"""Hybrid search service combining full-text + pg_trgm + pgvector with RRF fusion.

Provides:
- hybrid_search: RRF-fused results from three search methods (AI-03)
- _fulltext_search: PostgreSQL full-text search on tsvector columns
- _trigram_search: pg_trgm similarity on name columns
- _vector_search: pgvector cosine distance on embeddings (placeholder for MVP)

RRF fusion: score = sum(1 / (k + rank_i)) for each method, k=60

All user input is parameterized via SQLAlchemy constructs (T-02-01 mitigation).
"""

import uuid

import structlog
from sqlalchemy import and_, desc, func, literal_column, or_, select

from api.infrastructure.database import async_session
from api.models.embedding import EmbeddingModel
from api.models.structure import StructureModel

logger = structlog.get_logger(__name__)

# Language → PostgreSQL FTS config mapping (D-10)
_TS_CONFIGS = {"ru": "russian", "kk": "simple", "en": "english"}

# Language → generated tsvector column name (D-10)
_TS_COLUMNS = {"ru": "search_ts_ru", "kk": "search_ts_kk", "en": "search_ts_en"}

# RRF constant (standard value from original paper)
_RRF_K = 60


class SearchService:
    """Hybrid search combining full-text + trigram + vector with RRF fusion (AI-03)."""

    async def hybrid_search(
        self,
        query: str,
        limit: int = 20,
        source_types: list[str] | None = None,
        lang: str = "ru",
    ) -> list[dict]:
        """Hybrid search combining three methods with RRF fusion (AI-03).

        1. Full-text search: tsvector @@ tsquery on search_ts_ru/kk/en
        2. Trigram similarity: pg_trgm similarity() on name_ru/kk/en
        3. Vector similarity: pgvector cosine distance on embeddings

        RRF fusion: score = sum(1 / (k + rank_i)) for each method
        k = 60 (standard RRF constant)

        Args:
            query: search query string
            limit: max number of results
            source_types: optional filter by source_type
            lang: language for FTS config selection

        Returns:
            Ranked list of dicts with source_type, source_id, score, snippet.
        """
        # Run all three search methods in parallel conceptually
        fulltext_results = await self._fulltext_search(query, limit * 2, lang)
        trigram_results = await self._trigram_search(query, limit * 2)
        vector_results = await self._vector_search(query, limit * 2)

        # RRF fusion: combine ranks from each method
        scores: dict[str, float] = {}  # key = "source_type:source_id"

        for rank, result in enumerate(fulltext_results, start=1):
            key = f"{result['source_type']}:{result['source_id']}"
            scores[key] = scores.get(key, 0.0) + 1.0 / (_RRF_K + rank)
            if key not in scores or result.get("snippet"):
                # Store metadata from first occurrence
                pass

        for rank, result in enumerate(trigram_results, start=1):
            key = f"{result['source_type']}:{result['source_id']}"
            scores[key] = scores.get(key, 0.0) + 1.0 / (_RRF_K + rank)

        for rank, result in enumerate(vector_results, start=1):
            key = f"{result['source_type']}:{result['source_id']}"
            scores[key] = scores.get(key, 0.0) + 1.0 / (_RRF_K + rank)

        # Build result metadata map
        all_results: dict[str, dict] = {}
        for result in fulltext_results + trigram_results + vector_results:
            key = f"{result['source_type']}:{result['source_id']}"
            if key not in all_results:
                all_results[key] = result

        # Filter by source_types if specified
        if source_types:
            scores = {
                k: v for k, v in scores.items()
                if k.split(":")[0] in source_types
            }

        # Sort by RRF score descending
        ranked_keys = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

        # Build final results
        results = []
        for key in ranked_keys[:limit]:
            result = all_results.get(key, {
                "source_type": key.split(":")[0],
                "source_id": key.split(":")[1],
                "snippet": "",
            })
            result["score"] = scores[key]
            results.append(result)

        return results

    async def _fulltext_search(
        self, query: str, limit: int, lang: str = "ru"
    ) -> list[dict]:
        """PostgreSQL full-text search using tsvector columns.

        Uses plainto_tsquery for safe query parsing (T-02-01).
        Ranks with ts_rank_cd.

        Args:
            query: search query string
            limit: max number of results
            lang: language for FTS config selection

        Returns:
            List of dicts with source_type, source_id, score, snippet.
        """
        ts_config = _TS_CONFIGS.get(lang, "simple")
        ts_col_name = _TS_COLUMNS.get(lang, "search_ts_ru")

        ts_col = literal_column(ts_col_name)
        tsquery = func.plainto_tsquery(ts_config, query)
        fts_rank = func.ts_rank_cd(ts_col, tsquery)
        fts_match = ts_col.op("@@")(tsquery)

        async with async_session() as session:
            stmt = (
                select(
                    StructureModel.id,
                    fts_rank.label("rank"),
                )
                .where(
                    and_(
                        StructureModel.status != "deleted",
                        fts_match,
                    )
                )
                .order_by(desc(fts_rank))
                .limit(limit)
            )

            result = await session.execute(stmt)
            rows = result.all()

            return [
                {
                    "source_type": "structure",
                    "source_id": str(row[0]),
                    "score": float(row[1]),
                    "snippet": "",
                }
                for row in rows
            ]

    async def _trigram_search(
        self, query: str, limit: int
    ) -> list[dict]:
        """pg_trgm similarity search on name columns.

        similarity(name_ru/kk/en, query) > 0.1 threshold.
        Uses the greatest() of all three name similarities.

        Args:
            query: search query string
            limit: max number of results

        Returns:
            List of dicts with source_type, source_id, score, snippet.
        """
        trigram_best = func.greatest(
            func.similarity(StructureModel.name_ru, query),
            func.similarity(StructureModel.name_kk, query),
            func.similarity(StructureModel.name_en, query),
        )

        # 0.1 threshold to filter low-quality matches
        trigram_match = trigram_best > 0.1

        async with async_session() as session:
            stmt = (
                select(
                    StructureModel.id,
                    StructureModel.name_ru,
                    trigram_best.label("similarity"),
                )
                .where(
                    and_(
                        StructureModel.status != "deleted",
                        or_(
                            StructureModel.name_ru.isnot(None),
                            StructureModel.name_kk.isnot(None),
                            StructureModel.name_en.isnot(None),
                        ),
                        trigram_match,
                    )
                )
                .order_by(desc(trigram_best))
                .limit(limit)
            )

            result = await session.execute(stmt)
            rows = result.all()

            return [
                {
                    "source_type": "structure",
                    "source_id": str(row[0]),
                    "score": float(row[2]),
                    "snippet": row[1] or "",
                }
                for row in rows
            ]

    async def _vector_search(
        self, query: str, limit: int
    ) -> list[dict]:
        """pgvector cosine similarity search on embeddings.

        For MVP/hackathon: returns empty list since we don't have
        an embedding generation pipeline yet. In production, this
        would generate an embedding via OpenAI API and query pgvector.

        Args:
            query: search query string (unused in MVP placeholder)
            limit: max number of results

        Returns:
            Empty list for MVP — no query embedding available.
        """
        # MVP: no embedding generation pipeline — skip vector search
        # In production: generate embedding, then:
        #   stmt = select(
        #       EmbeddingModel.source_type,
        #       EmbeddingModel.source_id,
        #       EmbeddingModel.content_text,
        #       EmbeddingModel.embedding.cosine_distance(query_embedding).label("distance"),
        #   ).order_by(EmbeddingModel.embedding.cosine_distance(query_embedding)).limit(limit)
        logger.debug("vector_search_skipped", reason="no_embedding_pipeline")
        return []


# Module-level singleton for route handlers
search_service = SearchService()
