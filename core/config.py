from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str
    database_url: str
    assistant_mode: str = "general"
    openai_model: str = "gpt-4.1-mini"
    default_language: str = "en"


settings = Settings()
