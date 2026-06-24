from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    app_secret_key: str = "changeme"
    debug: bool = True

    # LLM
    groq_api_key: str

    # PostgreSQL
    database_url: str

    # Qdrant
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Rate limiting
    rate_limit_per_minute: int = 30
    
    #token validity duration in minutes
    jwt_expire_minutes: int = 30 

    # API auth
    api_key: str = "devmind-local-api-key"

  
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
