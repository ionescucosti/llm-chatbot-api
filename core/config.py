from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    sqlite_url: str
    assistant_mode: str = "general"
    openai_model: str = "pt-4.1-mini"
    default_language: str

    class Config:
        env_file = ".env"


settings = Settings()
