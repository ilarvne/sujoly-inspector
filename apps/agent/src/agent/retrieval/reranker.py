import httpx
from typing import List, Tuple
from functools import lru_cache

from langchain_core.documents import Document

from agent.config.settings import settings
from agent.utils.observability import get_tracer

tracer = get_tracer(__name__)


class Reranker:
    def __init__(self):
        self.url = settings.reranker_url
        self.model = settings.reranker_model
        self.api_key = settings.get_reranker_api_key()
        self.top_n = settings.retrieval_top_k_after_rerank

    async def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int | None = None,
    ) -> List[Tuple[Document, float]]:
        if not documents:
            return []

        with tracer.start_as_current_span("rerank") as span:
            span.set_attribute("num_documents", len(documents))
            span.set_attribute("query_length", len(query))

            passages = [doc.page_content for doc in documents]
            top_n = top_k or self.top_n

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "query": query,
                        "documents": passages,
                        "top_n": min(top_n, len(passages)),
                    },
                )
                response.raise_for_status()
                data = response.json()

            # Parse results - the API returns results with index and relevance_score
            results = data.get("results", [])
            doc_scores = []
            for result in results:
                idx = result.get("index", 0)
                score = result.get("relevance_score", 0.0)
                if idx < len(documents):
                    doc_scores.append((documents[idx], float(score)))

            doc_scores.sort(key=lambda x: x[1], reverse=True)

            if top_k is not None:
                doc_scores = doc_scores[:top_k]

            span.set_attribute("top_score", doc_scores[0][1] if doc_scores else 0.0)
            return doc_scores


@lru_cache(maxsize=1)
def get_reranker() -> Reranker:
    return Reranker()


async def rerank_documents(
    query: str,
    documents: List[Document],
    top_k: int | None = None,
) -> List[Document]:
    results = await get_reranker().rerank(query, documents, top_k)
    return [doc for doc, _ in results]
