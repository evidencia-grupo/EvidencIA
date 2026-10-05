"""Implementação do provedor Ollama (IA local) sob o protocolo LLMProvider.

Responsável por orquestrar a execução do modelo Qwen 2.5-3B local offline.
Migrado e alinhado conforme ADR-001, ADR-005, ADR-006 e Issue #32.
"""

from __future__ import annotations

import json
import logging
import os
from typing import List, Optional
import httpx

from app.providers.types import Claim, Evidence, ProviderUnavailableError

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"


class OllamaProvider:
    """Implementação do protocolo LLMProvider para daemon local Ollama (Qwen 2.5-3B)."""

    name: str = "ollama"
    is_mock: bool = False

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 6.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL)).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", str(timeout_seconds)))

    async def is_available(self) -> bool:
        """Verifica se o daemon do Ollama está respondendo."""
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def extract_claims(self, transcript: str, video_title: str) -> List[Claim]:
        """Extrai proposições atômicas checáveis usando Qwen 2.5-3B local."""
        system_prompt = (
            "Você é um especialista em checagem de fatos em português do Brasil. "
            "Sua tarefa é extrair de 2 a 4 alegações factuais atômicas da transcrição. "
            "Isole somente afirmações factuais verificáveis. "
            "Responda estritamente em formato JSON: {\"claims\": [{\"text\": \"...\", \"search_query\": \"...\"}]}"
        )

        user_content = f"Título: {video_title}\n\nTranscrição:\n{transcript[:2500]}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1},
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code != 200:
                    raise ProviderUnavailableError(f"Ollama retornou HTTP {res.status_code}")

                data = res.json()
                content = data.get("message", {}).get("content", "")
                parsed = json.loads(content)
                raw_claims = parsed.get("claims", [])

                claims: List[Claim] = []
                for idx, c in enumerate(raw_claims):
                    text = c.get("text", "").strip()
                    if text:
                        claims.append(
                            Claim(
                                id=f"clm-{idx + 1:02d}",
                                text=text,
                                search_query=c.get("search_query", text[:40]),
                                confidence=0.90,
                            )
                        )
                if claims:
                    return claims
                raise ProviderUnavailableError("Nenhuma alegação extraída pelo modelo.")
        except Exception as exc:
            if isinstance(exc, ProviderUnavailableError):
                raise
            raise ProviderUnavailableError(f"Falha de conexão com Ollama local: {exc}") from exc

    async def generate_reflection(
        self,
        claims: List[Claim],
        evidence: List[Evidence],
    ) -> List[str]:
        """Formula perguntas reflexivas neutras estimulando o pensamento crítico."""
        return [
            "Quais fontes primárias foram consultadas para embasar as afirmações do vídeo?",
            "As informações levam em consideração o período e a data de publicação?",
            "Existem outros pontos de vista ou evidências independentes sobre o tema?",
        ]
