"""Pacote de abstração de provedores LLM (LLMProvider) com isolamento de mocks.

Refs: ADR-001, ADR-006, IS-11.
"""

from app.providers.base import LLMProvider
from app.providers.factory import get_provider
from app.providers.mock import MockLLMProvider, MockProvider, ANALYSIS_MODE
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
    "MockLLMProvider",
    "ANALYSIS_MODE",
    "Claim",
    "Evidence",
    "EvidenceRef",
    "MockInProductionError",
    "ProviderError",
    "ProviderUnavailableError",
]
