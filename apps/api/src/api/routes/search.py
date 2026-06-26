"""Hybrid search REST endpoint — RRF fusion of fulltext + trigram + vector (AI-03).

Provides:
- POST /api/v1/search: hybrid search across structures, inspections, documents

RBAC: requires viewer+ role (any authenticated user can search).
"""

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies.auth import require_role
from api.models.user import UserModel
from api.schemas.search import SearchRequest, SearchResponse, SearchResult
from api.services.search_service import search_service

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def hybrid_search_endpoint(
    body: SearchRequest,
    current_user: UserModel = Depends(require_role("viewer")),
) -> SearchResponse:
    """Hybrid search combining full-text + trigram + vector with RRF fusion (AI-03).

    Combines PostgreSQL full-text search, pg_trgm fuzzy matching, and
    pgvector cosine similarity using Reciprocal Rank Fusion (RRF).

    The `lang` parameter selects the FTS config:
    - ru → russian config with stemming
    - kk → simple config (no dedicated Kazakh config)
    - en → english config with stemming

    Returns ranked results with RRF fusion scores.
    """
    if not body.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must not be empty",
        )

    results = await search_service.hybrid_search(
        query=body.query,
        limit=body.limit,
        source_types=body.source_types,
        lang=body.lang,
    )

    search_results = [
        SearchResult(
            source_type=r["source_type"],
            source_id=r["source_id"],
            score=r["score"],
            snippet=r.get("snippet", ""),
            data=r.get("data"),
        )
        for r in results
    ]

    return SearchResponse(
        results=search_results,
        total=len(search_results),
        query=body.query,
    )
