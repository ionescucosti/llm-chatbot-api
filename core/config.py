from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    assistant_mode: str = "general"
    openai_model: str = "gpt-4.1-mini"

    class Config:
        env_file = ".env"


settings = Settings()
