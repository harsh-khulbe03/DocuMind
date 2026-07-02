from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    llm_provider: Literal["ollama", "bedrock", "groq"] = "ollama"

    # Embeddings ("local" runs sentence-transformers in-process — free, no service)
    embedding_provider: Literal["ollama", "bedrock", "local"] = "ollama"
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Ollama
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "llama3.2"
    ollama_embedding_model: str = "nomic-embed-text"

    # Groq (free hosted LLM, OpenAI-compatible API)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # CORS: comma-separated origins, or "*" for any
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Bedrock
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_embedding_model_id: str = "amazon.titan-embed-text-v2:0"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""  # required for Qdrant Cloud
    qdrant_collection: str = "documind"

    # Retrieval
    vector_top_k: int = 20
    lexical_top_k: int = 20
    rerank_top_n: int = 5
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    confidence_threshold: float = 0.1

    # Ingestion
    chunk_max_tokens: int = 512
    upload_dir: Path = Path("uploads")
    sqlite_path: Path = Path("data/documind.db")

    def ensure_dirs(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s
