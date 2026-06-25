from threading import Lock
from typing import Optional

from langchain_milvus import Milvus
from langchain_openai import OpenAIEmbeddings
from pymilvus import connections

from agent.config.settings import settings

_lock = Lock()
_embeddings_instance: Optional[OpenAIEmbeddings] = None
_milvus_connected: bool = False


def get_embeddings() -> OpenAIEmbeddings:
    global _embeddings_instance
    if _embeddings_instance is None:
        with _lock:
            if _embeddings_instance is None:
                _embeddings_instance = OpenAIEmbeddings(
                    model=settings.embedding_model,
                    openai_api_key=settings.get_embedding_api_key(),
                    openai_api_base=settings.embedding_base_url,
                    dimensions=settings.embedding_dimensions,
                )
    return _embeddings_instance


def _ensure_milvus_connection() -> None:
    """Establish the pymilvus connection once (thread-safe)."""
    global _milvus_connected
    if not _milvus_connected:
        with _lock:
            if not _milvus_connected:
                connections.connect(
                    alias="default",
                    uri=settings.milvus_uri,
                    user=settings.milvus_user,
                    password=settings.milvus_password,
                    db_name=settings.milvus_db,
                )
                _milvus_connected = True


def get_vector_store(collection_name: Optional[str] = None) -> Milvus:
    _ensure_milvus_connection()
    return Milvus(
        collection_name=collection_name or settings.milvus_collection_name,
        embedding_function=get_embeddings(),
        connection_args={
            "uri": settings.milvus_uri,
            "user": settings.milvus_user,
            "password": settings.milvus_password,
            "db_name": settings.milvus_db,
        },
    )


def get_retriever(
    collection_name: Optional[str] = None,
    k: int = 3,
    filter: Optional[dict] = None,
):
    vector_store = get_vector_store(collection_name)
    return vector_store.as_retriever(search_kwargs={"k": k, "filter": filter})


def list_sources(collection_name: Optional[str] = None) -> list[str]:
    vector_store = get_vector_store(collection_name)
    col = vector_store.col
    col.load()
    results = col.query(
        expr='source != ""',
        output_fields=["source"],
        limit=16384,
    )
    sources: set[str] = {
        r["source"] for r in results if r.get("source")
    }
    return sorted(list(sources))


def delete_source(source_name: str, collection_name: Optional[str] = None) -> None:
    vector_store = get_vector_store(collection_name)
    vector_store.col.delete(expr=f'source == "{source_name}"')
