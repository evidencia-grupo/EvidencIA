from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"

    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = "mock_key"
    LLM_TIMEOUT_SECONDS: float = 8.0

    SEARCH_API_KEY: str = "mock_search_key"

    # Google Fact Check Tools API (ClaimReview RAG)
    GOOGLE_FACT_CHECK_API_KEY: Optional[str] = None
    FACT_CHECK_API_URL: str = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    # Ollama Local Engine (Qwen 2.5-3B)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_TIMEOUT_SECONDS: float = 6.0

    RATE_LIMIT_MAX_PER_MINUTE: int = 60
    CORS_ALLOWED_ORIGINS: str = "*"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
