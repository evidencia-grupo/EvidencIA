"""Esqueleto do provedor Ollama (IA local) implementando o protocolo LLMProvider.

Responsável por orquestrar a execução do modelo Qwen 2.5-3B local offline.
A migração de ollama_service.py para este módulo ocorre na Sprint 2 (S2-01).

Refs: ADR-001, IS-11, S2-01.
"""

from __future__ import annotations

import os
from typing import List
from app.services.providers.types import Claim, Evidence

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"


class OllamaProvider:
    """Implementação do protocolo LLMProvider para daemon local Ollama."""

    name: str = "ollama"
    is_mock: bool = False

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 6.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL)).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", str(timeout_seconds)))

    async def extract_claims(self, transcript: str, video_title: str) -> List[Claim]:
        """Esqueleto: migração de ollama_service.py agendada para a Sprint 2."""
        raise NotImplementedError(
            "TODO: migrar de ollama_service.py — ver issue 'Provider abstraction migration' (S2-01)"
        )

    async def generate_reflection(
        self,
        claims: List[Claim],
        evidence: List[Evidence],
    ) -> List[str]:
        """Esqueleto: migração de síntese agendada para a Sprint 2."""
        raise NotImplementedError(
            "TODO: migrar de ollama_service.py — ver issue 'Provider abstraction migration' (S2-01)"
        )
