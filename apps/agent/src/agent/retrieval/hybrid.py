"""Hybrid search combining BM25 (sparse) and dense vector retrieval.

Implements Reciprocal Rank Fusion (RRF) to combine rankings from
multiple retrieval methods, which has been shown to improve NDCG@10
by ~18% over single-method retrieval.
"""

import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Dict, Any

from langchain_core.documents import Document

from agent.config.settings import settings
from agent.memory.store import get_vector_store
from agent.utils.observability import get_tracer

tracer = get_tracer(__name__)


class BM25Index:
    """SQLite-backed BM25 index for sparse retrieval."""
    
    def __init__(self, db_path: str | None = None):
        """Initialize the BM25 index.
        
        Args:
            db_path: Path to SQLite database. Defaults to settings path.
        """
        self.db_path = db_path or str(
            Path(settings.upload_dir).parent / "bm25_index.db"
        )
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure the FTS5 table exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts 
                USING fts5(
                    doc_id,
                    content,
                    source,
                    tokenize='porter unicode61'
                )
            """)
            conn.commit()
    
    def add_documents(self, documents: List[Document], ids: List[str] | None = None):
        """Add documents to the BM25 index.
        
        Args:
            documents: Documents to index.
            ids: Optional document IDs. Will generate UUIDs if not provided.
        """
        import uuid
        
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        with sqlite3.connect(self.db_path) as conn:
            for doc_id, doc in zip(ids, documents):
                source = doc.metadata.get("source", "unknown")
                conn.execute(
                    "INSERT INTO documents_fts (doc_id, content, source) VALUES (?, ?, ?)",
                    (doc_id, doc.page_content, source)
                )
            conn.commit()
    
    def search(
        self, 
        query: str, 
        k: int = 50,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple[str, float]]:
        """Search the BM25 index.
        
        Args:
            query: Search query.
            k: Number of results to return.
            filter: Optional metadata filter (currently supports 'source').
            
        Returns:
            List of (doc_id, bm25_score) tuples.
        """
        with sqlite3.connect(self.db_path) as conn:
            # Build query with optional source filter
            if filter and "source" in filter:
                results = conn.execute(
                    """
                    SELECT doc_id, bm25(documents_fts) as score, content, source
                    FROM documents_fts 
                    WHERE documents_fts MATCH ? AND source = ?
                    ORDER BY score
                    LIMIT ?
                    """,
                    (query, filter["source"], k)
                ).fetchall()
            else:
                results = conn.execute(
                    """
                    SELECT doc_id, bm25(documents_fts) as score, content, source
                    FROM documents_fts 
                    WHERE documents_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                    """,
                    (query, k)
                ).fetchall()
            
            return [(row[0], -row[1], row[2], row[3]) for row in results]  # (ID, score, raw_content, source)
    
    def get_documents_by_id(self, doc_ids: List[str]) -> List[Document]:
        """Retrieve documents by their IDs.
        
        Args:
            doc_ids: List of document IDs to fetch.
            
        Returns:
            List of Document objects.
        """
        if not doc_ids:
            return []
            
        placeholders = ",".join(["?"] * len(doc_ids))
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                f"SELECT doc_id, content, source FROM documents_fts WHERE doc_id IN ({placeholders})",
                doc_ids
            ).fetchall()
            
            return [
                Document(page_content=row[1], metadata={"id": row[0], "source": row[2]})
                for row in rows
            ]
    
    def delete_by_source(self, source: str):
        """Delete all documents from a source.
        
        Args:
            source: Source name to delete.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM documents_fts WHERE source = ?", (source,))
            conn.commit()


def reciprocal_rank_fusion(
    rankings: List[List[tuple[str, float]]],
    k: int = 60
) -> List[tuple[str, float]]:
    """Combine multiple rankings using Reciprocal Rank Fusion.
    
    RRF score = sum(1 / (k + rank_i)) for each ranking
    
    Args:
        rankings: List of ranked result lists, each containing (doc_id, score) tuples.
        k: Smoothing parameter (typically 50-100).
        
    Returns:
        Fused ranking as list of (doc_id, rrf_score) tuples.
    """
    rrf_scores: Dict[str, float] = {}
    
    for ranking in rankings:
        for rank, (doc_id, _) in enumerate(ranking, start=1):
            if doc_id not in rrf_scores:
                rrf_scores[doc_id] = 0.0
            rrf_scores[doc_id] += 1.0 / (k + rank)
    
    # Sort by RRF score descending
    fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return fused


@lru_cache(maxsize=1)
def get_bm25_index() -> BM25Index:
    """Get the BM25 index singleton."""
    return BM25Index()


@lru_cache(maxsize=8)
def get_hybrid_retriever(collection_name: str | None = None) -> "HybridRetriever":
    """Get a cached hybrid retriever for a collection."""
    return HybridRetriever(collection_name=collection_name)


class HybridRetriever:
    """Hybrid retriever combining dense and sparse search with RRF fusion."""
    
    def __init__(
        self,
        collection_name: str | None = None,
        rrf_k: int | None = None,
    ):
        """Initialize the hybrid retriever.
        
        Args:
            collection_name: ChromaDB collection name.
            rrf_k: RRF smoothing parameter.
        """
        self.collection_name = collection_name
        self.rrf_k = rrf_k or settings.hybrid_rrf_k
        self.vector_store = get_vector_store(collection_name)
        self.bm25_index = get_bm25_index()
    
    def search(
        self,
        query: str,
        k: int = 50,
        filter: Optional[Dict[str, Any]] = None,
        sparse_query: str | None = None,
    ) -> List[Document]:
        """Perform hybrid search with RRF fusion.
        
        Args:
            query: Semantic search query for vector store.
            k: Number of results to return after fusion.
            filter: Optional metadata filter.
            sparse_query: Optional keyword-based query for BM25. Defaults to 'query'.
            
        Returns:
            List of documents ranked by RRF score.
        """
        with tracer.start_as_current_span("hybrid_search") as span:
            sparse_query = sparse_query or query
            span.set_attribute("query", query[:100])
            span.set_attribute("sparse_query", sparse_query[:100])
            span.set_attribute("k", k)
            
            # 1. Dense search
            with tracer.start_as_current_span("dense_search"):
                dense_results = self.vector_store.similarity_search_with_score(
                    query, k=k, filter=filter
                )
                dense_ranking = []
                doc_map = {}
                
                for i, (doc, score) in enumerate(dense_results):
                    doc_id = doc.metadata.get("id", str(i))
                    dense_ranking.append((doc_id, score))
                    doc_map[doc_id] = doc
            
            # 2. Sparse (BM25) search
            with tracer.start_as_current_span("sparse_search"):
                try:
                    # BM25 returns (id, score, content, source)
                    sparse_results = self.bm25_index.search(sparse_query, k=k, filter=filter)
                    sparse_ranking = []
                    for doc_id, score, content, source in sparse_results:
                        sparse_ranking.append((doc_id, score))
                        # Only add to map if not already there from dense
                        if doc_id not in doc_map:
                            doc_map[doc_id] = Document(
                                page_content=content, 
                                metadata={"id": doc_id, "source": source}
                            )
                except Exception as e:
                    import structlog
                    logger = structlog.get_logger(__name__)
                    logger.warning("sparse_search_failed", error=str(e))
                    sparse_ranking = []
            
            span.set_attribute("dense_results", len(dense_ranking))
            span.set_attribute("sparse_results", len(sparse_ranking))
            
            # If no sparse results, just use dense
            if not sparse_ranking:
                return [doc for doc, _ in dense_results[:k]]
            
            # 3. RRF fusion
            with tracer.start_as_current_span("rrf_fusion"):
                fused = reciprocal_rank_fusion(
                    [dense_ranking, sparse_ranking],
                    k=self.rrf_k
                )
            
            # 4. Map back to documents
            results = []
            for doc_id, _ in fused[:k]:
                if doc_id in doc_map:
                    results.append(doc_map[doc_id])
                else:
                    # This shouldn't happen with the updated doc_map logic above,
                    # but good as a safety catch.
                    span.add_event(f"Missing doc in map: {doc_id}")
            
            span.set_attribute("final_results", len(results))
            return results


def hybrid_search(
    query: str,
    k: int = 50,
    filter: Optional[Dict[str, Any]] = None,
    collection_name: str | None = None,
    sparse_query: str | None = None,
) -> List[Document]:
    """Convenience function for hybrid search.
    
    Args:
        query: Semantic search query.
        k: Number of results to return.
        filter: Optional metadata filter.
        collection_name: Optional collection name.
        sparse_query: Optional keyword-based query for BM25.
        
    Returns:
        List of documents ranked by hybrid RRF score.
    """
    retriever = get_hybrid_retriever(collection_name=collection_name)
    return retriever.search(query, k=k, filter=filter, sparse_query=sparse_query)
