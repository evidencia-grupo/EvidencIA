"""Factory e seletor de instâncias de LLMProvider com proteção anti-mock em produção.

Regras de governança (ADR-001 / IS-11):
1. `get_provider()` avalia `LLM_PROVIDER` e os aliases de ambiente.
2. Se `LLM_PROVIDER=mock` e qualquer alias for 'production' ou 'prod' (case-insensitive),
   lança `MockInProductionError` imediatamente (fail-fast).
3. Nunca realiza fallback silencioso para mock em caso de erro.
4. Valor desconhecido de `LLM_PROVIDER` levanta `ValueError` listando os valores válidos.

Refs: ADR-001, IS-11.
"""

from __future__ import annotations

import logging
import os

from typing import Optional

from app.config import settings

from app.providers.base import LLMProvider
from app.providers.mock import MockProvider
from app.providers.ollama import OllamaProvider
from app.providers.remote import RemoteLLMProvider
from app.providers.types import MockInProductionError, ProviderUnavailableError, ProviderError

audit_logger = logging.getLogger("app.audit")

VALID_PROVIDERS = ("ollama", "remote", "mock")

__all__ = [
    "get_provider",
    "VALID_PROVIDERS",
    "MockInProductionError",
    "ProviderUnavailableError",
    "ProviderError",
]


def get_provider(
    provider_name: Optional[str] = None,
    app_env: Optional[str] = None,
) -> LLMProvider:
    """Retorna uma instância configurada do provedor de LLM solicitado.

    Args:
        provider_name: Nome do provedor ('ollama', 'remote', 'mock').
                       Se omitido, lê da variável de ambiente `LLM_PROVIDER` (padrão: 'ollama').
        app_env: Ambiente de execução ('development', 'staging', 'production').
                 Se omitido, lê de `ENV`, `NODE_ENV`, `APP_ENV` ou `ENVIRONMENT`.

    Returns:
        Instância que satisfaz o protocolo LLMProvider.

    Raises:
        MockInProductionError: Se mock for requisitado em ambiente de produção.
        ValueError: Se o nome do provedor for desconhecido.
    """
    raw_provider = provider_name or os.getenv("LLM_PROVIDER", settings.LLM_PROVIDER)
    normalized_provider = raw_provider.strip().lower()

    raw_env = (
        app_env
        or os.getenv("ENV")
        or os.getenv("NODE_ENV")
        or os.getenv("APP_ENV")
        or os.getenv("ENVIRONMENT", settings.ENVIRONMENT)
    )

    # Guarda anti-mock estrita em produção (ADR-001 / ADR-006 / RF-15)
    # Um alias de desenvolvimento nunca pode esconder outro alias de produção.
    environments = [
        raw_env, settings.ENVIRONMENT, settings.ENV, settings.APP_ENV, settings.NODE_ENV,
        *(os.getenv(key, "") for key in ("ENV", "ENVIRONMENT", "APP_ENV", "NODE_ENV")),
    ]
    is_production = any((env or "").strip().lower() in ("production", "prod") for env in environments)

    if normalized_provider == "mock":
        if is_production:
            audit_logger.critical(
                "mock_in_production_blocked: LLM_PROVIDER=mock não é permitido em ambiente de produção",
                extra={"event": "mock_in_production_blocked", "provider": "mock", "environment": "production"},
            )
            raise MockInProductionError(
                "Violação de segurança ADR-001: LLM_PROVIDER=mock não é permitido em ambiente de "
                "produção. Configure um provedor real ('ollama' ou 'remote')."
            )
        return MockProvider()

    if normalized_provider == "ollama":
        return OllamaProvider()

    if normalized_provider == "remote":
        return RemoteLLMProvider()

    raise ValueError(
        f"Provedor LLM inválido: '{raw_provider}'. "
        f"Valores suportados: {list(VALID_PROVIDERS)}"
    )
