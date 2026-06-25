from typing import Any
from pathlib import Path

import structlog
from mem0 import Memory

from agent.config.settings import settings
from agent.memory.store import get_embeddings

logger = structlog.get_logger(__name__)


class AgentMemory:
    _instance: "AgentMemory | None" = None
    _memory: Memory | None = None

    def __new__(cls) -> "AgentMemory":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if AgentMemory._memory is not None:
            return

        history_db_path = Path(settings.upload_dir).parent / "mem0_history.db"
        history_db_path.parent.mkdir(parents=True, exist_ok=True)

        config = {
            "vector_store": {
                "provider": "milvus",
                "config": {
                    "collection_name": settings.milvus_user_memory_collection,
                    "uri": settings.milvus_uri,
                    "user": settings.milvus_user,
                    "password": settings.milvus_password,
                    "db_name": settings.milvus_db,
                },
            },
            "llm": {
                "provider": "litellm",
                "config": {
                    "model": f"openai/{settings.llm_model}",
                    "api_key": settings.get_llm_api_key(),
                    "api_base": settings.llm_base_url,
                    "temperature": settings.llm_temperature,
                    "max_tokens": 1000,
                },
            },
            "embedder": {
                "provider": "langchain",
                "config": {
                    "model": get_embeddings(),
                },
            },
            "history_db_path": str(history_db_path),
            "version": "v1.1",
        }

        logger.info(
            "initializing_mem0",
            milvus_uri=settings.milvus_uri,
            milvus_db=settings.milvus_db,
            milvus_collection=settings.milvus_user_memory_collection,
            llm_model=config["llm"]["config"]["model"],
            embedder_model=settings.embedding_model,
            history_db=str(history_db_path),
        )

        try:
            AgentMemory._memory = Memory.from_config(config)
        except Exception as e:
            logger.error("mem0_initialization_failed", error=str(e), exc_info=True)
            raise

    @property
    def memory(self) -> Memory:
        if AgentMemory._memory is None:
            raise RuntimeError("Memory not initialized")
        return AgentMemory._memory

    def add(
        self, content: str, user_id: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            return self.memory.add(content, user_id=user_id, metadata=metadata)
        except Exception as e:
            logger.error("mem0_add_failed", user_id=user_id, error=str(e))
            raise

    def search(self, query: str, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        try:
            results = self.memory.search(query, user_id=user_id, limit=limit)
            logger.debug(
                "mem0_search", user_id=user_id, query=query[:50], results=len(results)
            )
            return results
        except Exception as e:
            logger.error("mem0_search_failed", user_id=user_id, error=str(e))
            return []

    def get_all(self, user_id: str) -> list[dict[str, Any]]:
        try:
            return self.memory.get_all(user_id=user_id)
        except Exception as e:
            logger.error("mem0_get_all_failed", user_id=user_id, error=str(e))
            return []

    def delete(self, memory_id: str) -> bool:
        try:
            self.memory.delete(memory_id)
            return True
        except Exception as e:
            logger.error("mem0_delete_failed", memory_id=memory_id, error=str(e))
            return False

    def delete_all(self, user_id: str) -> bool:
        try:
            self.memory.delete_all(user_id=user_id)
            return True
        except Exception as e:
            logger.error("mem0_delete_all_failed", user_id=user_id, error=str(e))
            return False
