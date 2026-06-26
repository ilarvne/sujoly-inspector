"""Pydantic schemas for hybrid search endpoint (AI-03).

Provides:
- SearchRequest: request body for POST /search
- SearchResult: single search result with source_type, source_id, score, snippet, data
- SearchResponse: response envelope with results, total, query
"""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request body for POST /search — hybrid search endpoint."""

    query: str = Field(..., description="Search query string", min_length=1)
    limit: int = Field(20, description="Max number of results", ge=1, le=100)
    source_types: list[str] | None = Field(
        None,
        description="Optional filter by source_type (structure, inspection, document, candidate)",
    )
    lang: str = Field(
        "ru",
        description="Language for full-text search config (ru, kk, en)",
    )


class SearchResult(BaseModel):
    """Single search result from hybrid search."""

    source_type: str = Field(..., description="Source entity type")
    source_id: str = Field(..., description="UUID of the source record")
    score: float = Field(..., description="RRF fusion score")
    snippet: str = Field("", description="Text snippet from the matching content")
    data: dict | None = Field(
        None, description="Optional additional data from the source record"
    )


class SearchResponse(BaseModel):
    """Response envelope for hybrid search results."""

    results: list[SearchResult] = Field(..., description="Ranked search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="The original search query")
