"""Esqueleto do provedor Remoto (APIs compatíveis OpenAI/vLLM) implementando LLMProvider.

Permite conexão com clusters próprios ou APIs externas autenticadas.
Chaves de API lidas exclusivamente via variáveis de ambiente; nunca hardcoded.

Refs: ADR-001, IS-11, S2-01.
"""

from __future__ import annotations

import os
from typing import List
from app.services.providers.types import Claim, Evidence


class RemoteLLMProvider:
    """Implementação do protocolo LLMProvider para servidores remotos compatíveis."""

    name: str = "remote"
    is_mock: bool = False

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("REMOTE_LLM_BASE_URL", "")).rstrip("/")
        # Chave obtida via variável de ambiente, nunca commitada
        self.api_key = api_key or os.getenv("REMOTE_LLM_API_KEY", "")
        self.model = model or os.getenv("REMOTE_LLM_MODEL", "qwen2.5:7b")

    async def extract_claims(self, transcript: str, video_title: str) -> List[Claim]:
        """Esqueleto: implementação remota agendada para a Sprint 2."""
        raise NotImplementedError(
            "TODO: migrar de ollama_service.py — ver issue 'Provider abstraction migration' (S2-01)"
        )

    async def generate_reflection(
        self,
        claims: List[Claim],
        evidence: List[Evidence],
    ) -> List[str]:
        """Esqueleto: implementação remota agendada para a Sprint 2."""
        raise NotImplementedError(
            "TODO: migrar de ollama_service.py — ver issue 'Provider abstraction migration' (S2-01)"
        )
