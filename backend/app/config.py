from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"

    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = "mock_key"
    LLM_TIMEOUT_SECONDS: float = 8.0

    SEARCH_API_KEY: str = "mock_search_key"

    RATE_LIMIT_MAX_PER_MINUTE: int = 60
    CORS_ALLOWED_ORIGINS: str = "*"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
