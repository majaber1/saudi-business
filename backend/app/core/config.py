"""
Application configuration, loaded from environment variables.
Copy .env.example to .env and adjust for your environment.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "FeasibilityOS AI"
    environment: str = "development"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/feasibilityos"
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"


settings = Settings()
