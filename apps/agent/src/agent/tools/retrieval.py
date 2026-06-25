"""Retrieval tools for the agent.

Uses hybrid search (BM25 + dense) with cross-encoder reranking
for production-quality retrieval.
"""

from typing import Optional, Any

from langchain_core.tools import tool
from langchain_core.documents import Document

from agent.config.settings import settings
from agent.memory.store import get_vector_store
from agent.memory.mem0_client import AgentMemory
from agent.retrieval.hybrid import hybrid_search
from agent.retrieval.reranker import rerank_documents
from agent.utils.observability import get_tracer

tracer = get_tracer(__name__)


@tool
async def search_knowledge(query: str, filter: Optional[dict[str, Any]] = None) -> str:
    """Search the knowledge base for relevant information.

    Args:
        query: The search query.
        filter: Optional metadata filter.

    Returns:
        Relevant information text.
    """
    with tracer.start_as_current_span("search_knowledge") as span:
        import structlog

        logger = structlog.get_logger(__name__)

        # Multilingual Search Strategy — hydraulic infrastructure domain
        search_terms = {
            "canal": ["канал", "арна"],
            "dam": ["плотина", "бөгет"],
            "pump": ["насос", "сорғы"],
            "inspection": ["осмотр", "тексеру"],
            "repair": ["ремонт", "жөндеу"],
            "condition": ["состояние", "жағдай"],
            "efficiency": ["КПД", "пайдалы әсер"],
            "risk": ["риск", "қауіп"],
            "coordinates": ["координаты", "координаталар"],
            "district": ["район", "аудан"],
            "water": ["вода", "су"],
            "sluice": ["шлюз", "шлюзы"],
            "reservoir": ["водохранилище", "су қоймасы"],
        }

        # Build an OR-based keyword query for BM25
        keywords = query.split()
        lower_query = query.lower()
        for eng, translations in search_terms.items():
            if eng in lower_query:
                keywords.extend(translations)

        # SQLite FTS5 OR logic
        keyword_query = " OR ".join(f'"{k}"' for k in keywords if len(k) > 2)

        logger.debug(
            "search_knowledge_expanded", original=query, keywords=keyword_query
        )
        span.set_attribute("query", query[:100])

        try:
            # Step 1: Hybrid retrieval
            if settings.use_hybrid_search:
                # We need to pass the keyword query specifically for BM25
                # I will use the 'query' as semantic and 'query' as sparse if I don't modify hybrid_search
                # But to be safe, I'll just use keyword_query which contains both.
                # Actually, I'll modify hybrid_search to handle this better in a moment.
                initial_docs = hybrid_search(
                    query=query,  # Semantic base
                    sparse_query=keyword_query,  # Keyword base
                    k=settings.retrieval_top_k_initial,
                    filter=filter,
                )
            else:
                # Fallback to simple dense search
                vector_store = get_vector_store()
                initial_docs = vector_store.similarity_search(
                    query, k=settings.retrieval_top_k_initial, filter=filter
                )

            span.set_attribute("initial_docs", len(initial_docs))
            logger.debug("search_knowledge_initial_results", count=len(initial_docs))

            if not initial_docs:
                logger.warning("search_knowledge_no_results", query=query)
                return "I couldn't find any relevant information in the knowledge base for your query."

            # Step 2: Optional cross-encoder reranking. Keep disabled by default for latency.
            if settings.use_reranker:
                with tracer.start_as_current_span("rerank_stage"):
                    docs = await rerank_documents(
                        query=query,
                        documents=initial_docs,
                        top_k=settings.retrieval_top_k_after_rerank,
                    )
            else:
                docs = initial_docs[: settings.retrieval_top_k_after_rerank]

            # Step 3: Format results for the LLM
            formatted_results = []
            for i, doc in enumerate(docs, 1):
                content = doc.page_content
                source = doc.metadata.get("source", "unknown")
                formatted_results.append(f"[{i}] Source: {source}\nContent: {content}")

            if not formatted_results:
                return "No matching information found in the documents."

            header = "--- SEARCH RESULTS ---\n\n"
            serialized = header + "\n\n".join(formatted_results)
            return serialized

        except Exception as e:
            span.set_attribute("error", str(e))
            return f"Encountered an error while searching: {str(e)}"


@tool
def search_user_memory(query: str, user_id: str = "default_user") -> str:
    """Search the user's personal long-term memory for life context, preferences, and past interactions.

    Args:
        query: What to look for in personal memory.
        user_id: The ID of the user. defaults to 'default_user'.

    Returns:
        Relevant personal context.
    """
    try:
        memory = AgentMemory()
        search_results = memory.search(query, user_id=user_id)

        results = (
            search_results.get("results", [])
            if isinstance(search_results, dict)
            else search_results
        )
        if not results:
            return "No relevant personal memories found."

        memories = [
            m.get("memory", m.get("text", "")) for m in results if isinstance(m, dict)
        ]
        memories = [m for m in memories if m]

        if not memories:
            return "No relevant personal memories found."

        return "Relevant personal memories:\n- " + "\n- ".join(memories)
    except Exception as e:
        return f"Error searching personal memory: {str(e)}"


@tool
def save_to_memory(content: str, metadata: str | None = None) -> str:
    """Save information to the knowledge base for future reference.

    Args:
        content: The content to save.
        metadata: Optional source metadata about the content.

    Returns:
        Confirmation message.
    """
    import uuid
    from agent.retrieval.hybrid import get_bm25_index

    try:
        vector_store = get_vector_store()
        bm25_index = get_bm25_index()
        memory = AgentMemory()

        doc_id = str(uuid.uuid4())
        source = metadata or "agent_memory"

        doc = Document(page_content=content, metadata={"source": source, "id": doc_id})

        # Add to knowledge indices
        vector_store.add_documents([doc], ids=[doc_id])
        bm25_index.add_documents([doc], ids=[doc_id])

        # Also add to Mem0 for long-term user context (associating with default user for now or metadata if available)
        user_id = "default_user"  # In production, this should come from context
        memory.add(
            content, user_id=user_id, metadata={"source": source, "type": "manual_save"}
        )

        return f"Successfully saved to knowledge base and long-term memory with ID: {doc_id}"
    except Exception as e:
        return f"Failed to save to memory: {str(e)}"
