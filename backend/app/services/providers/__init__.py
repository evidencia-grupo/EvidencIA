"""Módulo de compatibilidade para app.services.providers -> app.providers.

Mantém interoperabilidade com ferramentas de auditoria e referências legadas
enquanto centraliza a implementação em app.providers (ADR-004 / Arquitetura oficial).
"""

from app.providers.base import LLMProvider
from app.providers.factory import get_provider
from app.providers.mock import MockProvider, ANALYSIS_MODE
from app.providers.ollama import OllamaProvider
from app.providers.remote import RemoteLLMProvider
from app.providers.types import (
    Claim,
    Evidence,
    EvidenceRef,
    MockInProductionError,
    ProviderError,
    ProviderUnavailableError,
)

__all__ = [
    "LLMProvider",
    "get_provider",
    "MockProvider",
    "ANALYSIS_MODE",
    "OllamaProvider",
    "RemoteLLMProvider",
    "Claim",
    "Evidence",
    "EvidenceRef",
    "MockInProductionError",
    "ProviderError",
    "ProviderUnavailableError",
]
