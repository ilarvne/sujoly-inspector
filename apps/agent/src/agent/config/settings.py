from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Alem LLM models — all OpenAI-compatible via https://llm.alem.ai/v1
ALEM_MODELS = {
    "qwen3-6": {
        "context_window": 32768,
        "max_output": 8192,
        "capabilities": ["chat", "tool_calling"],
        "api_key_env": "CHAT_QWEN_API_KEY",
    },
    "gemma4": {
        "context_window": 32768,
        "max_output": 8192,
        "capabilities": ["chat", "tool_calling"],
        "api_key_env": "CHAT_GEMMA_API_KEY",
    },
    "alemllm": {
        "context_window": 32768,
        "max_output": 8192,
        "capabilities": ["chat", "tool_calling"],
        "api_key_env": "CHAT_ALEM_API_KEY",
    },
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    environment: str = "development"
    debug: bool = True
    request_timeout: int = 60
    max_history_messages: int = 15

    # Alem LLM (OpenAI-compatible)
    llm_base_url: str = "https://llm.alem.ai/v1"
    llm_model: str = "qwen3-6"
    llm_api_key: str = ""  # Filled from .env at runtime
    llm_temperature: float = 0.6
    llm_max_tokens: int = 2048

    # Embeddings (Alem, OpenAI-compatible)
    embedding_model: str = "text-1024"
    embedding_api_key: str = ""  # Filled from .env at runtime
    embedding_base_url: str = "https://llm.alem.ai/v1"
    embedding_dimensions: int = 1024

    # Reranker (Alem, custom POST endpoint)
    reranker_api_key: str = ""  # Filled from .env at runtime
    reranker_model: str = "reranker"
    reranker_url: str = "https://llm.alem.ai/v1/rerank"

    # Milvus vector store
    milvus_uri: str = "https://a1-milvus1.alem.ai:30130"
    milvus_host: str = "a1-milvus1.alem.ai"
    milvus_port: int = 30130
    milvus_user: str = "ilarvne"
    milvus_password: str = ""
    milvus_db: str = "alemplusvector"
    milvus_collection_name: str = "sujoly_knowledge"
    milvus_user_memory_collection: str = "sujoly_user_memory"

    # Retrieval
    retrieval_top_k_initial: int = 8
    retrieval_top_k_after_rerank: int = 2
    use_reranker: bool = True
    use_hybrid_search: bool = True
    hybrid_rrf_k: int = 60
    tool_max_concurrency: int = 4

    # Agent
    agent_name: str = "SuJoly Copilot"
    agent_max_iterations: int = 5
    max_tool_rounds: int = 3
    agent_api_keys: str = ""
    agent_api_key: str | None = None

    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:3001"

    # Rate limiting
    max_request_body_mb: int = 10
    rate_limit: str = "60/minute"
    rate_limit_per_user: str = "30/minute"

    # PostgreSQL (provided infra)
    database_url: str = "postgresql+asyncpg://ilarvne:yOv34H9W0E@a1-postgres1.alem.ai:30100/alemhackdb"
    postgres_url: str = "postgresql://ilarvne:yOv34H9W0E@a1-postgres1.alem.ai:30100/alemhackdb?sslmode=disable"

    # Redis (provided infra)
    redis_url: str = "redis://:NyH3Kl8Ankr2wJ22hpGE08jIQLCiwOhrkpAR3ZOu@149.137.233.13:31224/alemhackredis"

    # MinIO (provided infra)
    minio_endpoint: str = "a1-minio1.alem.ai"
    minio_access_key: str = "ilarvne"
    minio_secret_key: str = ""
    minio_bucket: str = "alemhackbucket"
    minio_use_ssl: bool = True

    # File storage
    upload_dir: str = "./data/uploads"

    # SuJoly API backend (FastAPI — to be built)
    sujoly_api_url: str = "http://localhost:8000"

    def get_llm_api_key(self) -> str:
        """Get the API key for the current chat model."""
        import os
        model_info = ALEM_MODELS.get(self.llm_model, {})
        key_env = model_info.get("api_key_env", "LLM_DEFAULT_API_KEY")
        return os.environ.get(key_env, self.llm_api_key)

    def get_embedding_api_key(self) -> str:
        import os
        return os.environ.get("EMBEDDINGS_API_KEY", self.embedding_api_key)

    def get_reranker_api_key(self) -> str:
        import os
        return os.environ.get("RERANKER_API_KEY", self.reranker_api_key)

    def get_available_models(self) -> list[str]:
        return list(ALEM_MODELS.keys())

    def get_agent_api_keys(self) -> list[str]:
        keys: list[str] = []
        if self.agent_api_key and self.agent_api_key.strip():
            keys.append(self.agent_api_key.strip())
        if self.agent_api_keys:
            keys.extend(
                key.strip() for key in self.agent_api_keys.split(",") if key.strip()
            )
        return list(dict.fromkeys(keys))

    def get_model_info(self, model: str | None = None) -> dict:
        model = model or self.llm_model
        if model not in ALEM_MODELS:
            return {}
        return {"model": model, **ALEM_MODELS[model]}


settings = Settings()
