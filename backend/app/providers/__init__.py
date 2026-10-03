"""Pacote de abstração de provedores LLM (LLMProvider) com isolamento de mocks.

Refs: ADR-001, IS-11.
"""

from app.services.providers.base import LLMProvider
from app.services.providers.factory import get_provider
from app.services.providers.mock import MockProvider, ANALYSIS_MODE
from app.services.providers.types import (
    Claim,
    Evidence,
    EvidenceRef,
    MockInProductionError,
    ProviderUnavailableError,
)

__all__ = [
    "LLMProvider",
    "get_provider",
    "MockProvider",
    "ANALYSIS_MODE",
    "Claim",
    "Evidence",
    "EvidenceRef",
    "MockInProductionError",
    "ProviderUnavailableError",
]
