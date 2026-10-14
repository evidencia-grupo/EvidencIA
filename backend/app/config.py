import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

# Fonte única: ambientes que exigem auth, Redis, CORS estrito e bloqueiam o provedor mock.
PRODUCTION_ENVIRONMENTS = ("production", "prod", "staging")


class Settings(BaseSettings):
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    ENV: Optional[str] = None
    APP_ENV: Optional[str] = None
    NODE_ENV: Optional[str] = None
    LOG_LEVEL: str = "info"

    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = "mock_key"
    LLM_TIMEOUT_SECONDS: float = Field(15.0, gt=0, le=15, allow_inf_nan=False)

    REMOTE_LLM_BASE_URL: str = ""
    REMOTE_LLM_API_KEY: str = ""
    REMOTE_LLM_MODEL: str = "qwen2.5:7b"
    REMOTE_LLM_TIMEOUT_SECONDS: float = Field(15.0, gt=0, le=15, allow_inf_nan=False)

    SEARCH_API_KEY: str = "mock_search_key"

    # Google Fact Check Tools API (ClaimReview RAG)
    GOOGLE_FACT_CHECK_API_KEY: Optional[str] = None
    FACT_CHECK_API_URL: str = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    # Ollama Local Engine (Qwen 2.5-3B)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_TIMEOUT_SECONDS: float = Field(15.0, gt=0, le=15, allow_inf_nan=False)

    RATE_LIMIT_MAX_PER_MINUTE: int = Field(60, ge=1)
    RATE_LIMIT_STORAGE_URI: str = "memory://"
    # Proxies reversos confiáveis à frente da API (Render: 1). 0 = X-Forwarded-For ignorado.
    TRUSTED_PROXY_HOPS: int = Field(0, ge=0, le=5)
    MAX_REQUEST_BODY_BYTES: int = Field(524288, ge=1024, le=10485760)
    CORS_ALLOWED_ORIGINS: str = "https://www.youtube.com,chrome-extension://*"

    AUTH_SECRET: str = "dev_evidencia_secret_key_change_in_production"
    REQUIRE_AUTH: bool = False

    def is_production(self) -> bool:
        return any((value or "").strip().lower() in PRODUCTION_ENVIRONMENTS
                   for value in (self.ENV, self.ENVIRONMENT, self.APP_ENV, self.NODE_ENV))

    model_config = {
        "env_file": (
            os.path.join(os.path.dirname(__file__), "..", ".env"),
            ".env",
        ),
        "extra": "ignore",
    }


settings = Settings()
