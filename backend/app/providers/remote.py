"""Implementação do provedor Remoto (APIs compatíveis OpenAI/vLLM) sob LLMProvider.

Permite conexão com clusters próprios ou APIs externas autenticadas.
Chaves de API lidas exclusivamente via variáveis de ambiente; nunca hardcoded (RNF-04).
Refs: ADR-001, ADR-006, IS-11, Issue #32.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional
import httpx

from app.config import settings
from app.providers.prompts import extraction_messages, parse_extracted_claims, load_json_object, reflection_messages, parse_reflections
from app.providers.base import LLMProvider
from app.providers.types import Claim, Evidence, ProviderUnavailableError

logger = logging.getLogger(__name__)


class RemoteLLMProvider(LLMProvider):
    """Implementação do protocolo LLMProvider para servidores remotos compatíveis (OpenAI/vLLM)."""

    name: str = "remote"
    is_mock: bool = False

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("REMOTE_LLM_BASE_URL", settings.REMOTE_LLM_BASE_URL)).rstrip("/")
        self.api_key = api_key or os.getenv("REMOTE_LLM_API_KEY", settings.REMOTE_LLM_API_KEY)
        self.model = model or os.getenv("REMOTE_LLM_MODEL", settings.REMOTE_LLM_MODEL)
        self.timeout = float(os.getenv("REMOTE_LLM_TIMEOUT_SECONDS", str(min(timeout_seconds, settings.REMOTE_LLM_TIMEOUT_SECONDS))))

    async def extract_claims(self, transcript: str, video_title: str) -> List[Claim]:
        """Extrai proposições atômicas checáveis via API remota compatível com chat completions."""
        if not self.base_url:
            raise ProviderUnavailableError("REMOTE_LLM_BASE_URL não configurada para o provedor remoto.")

        payload = {
            "model": self.model,
            "messages": extraction_messages(transcript, video_title),
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        try:
            content = await self._chat(payload)
            parsed = load_json_object(content)
            return parse_extracted_claims(parsed)
        except Exception as exc:
            if isinstance(exc, ProviderUnavailableError):
                raise
            raise ProviderUnavailableError("Falha de comunicação com provedor remoto: resposta de extração inválida.") from exc

    async def generate_reflection(
        self,
        claims: List[Claim],
        evidence: List[Evidence],
    ) -> List[str]:
        """Formula perguntas reflexivas neutras estimulando o pensamento crítico."""
        if not claims:
            return []
        payload = {
            "model": self.model,
            "messages": reflection_messages(claims, evidence),
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        try:
            return parse_reflections(await self._chat(payload))
        except (ValueError, KeyError, TypeError) as exc:
            raise ProviderUnavailableError("Resposta de reflexão inválida do provedor.") from exc

    async def _chat(self, payload: dict) -> str:
        if not self.base_url:
            raise ProviderUnavailableError("REMOTE_LLM_BASE_URL não configurada para o provedor remoto.")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if "openrouter.ai" in self.base_url:
            headers["HTTP-Referer"] = "https://github.com/evidencia-grupo/EvidencIA"
            headers["X-Title"] = "EvidencIA - Fact-Checking"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            if response.status_code != 200:
                raise ProviderUnavailableError(f"Provedor remoto respondeu HTTP {response.status_code}")
            return response.json()["choices"][0]["message"]["content"]
        except ProviderUnavailableError:
            raise
        except Exception as exc:
            raise ProviderUnavailableError("Falha de comunicação com provedor remoto.") from exc
