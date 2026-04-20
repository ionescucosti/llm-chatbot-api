from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str
    database_url: str
    assistant_mode: str = "general"
    openai_model: str = "gpt-4.1-mini"
    default_language: str = "en"

    # Redis & Celery
    redis_url: str = "redis://localhost:6379/0"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection_name: str = "documents"

    # Embeddings
    embedding_model: str = "text-embedding-3-small"

    # File upload
    max_file_size_mb: int = 10


settings = Settings()
