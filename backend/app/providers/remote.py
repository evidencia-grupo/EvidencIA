"""Implementação do provedor Remoto (APIs compatíveis OpenAI/vLLM) sob LLMProvider.

Permite conexão com clusters próprios ou APIs externas autenticadas.
Chaves de API lidas exclusivamente via variáveis de ambiente; nunca hardcoded (RNF-04).
Refs: ADR-001, ADR-006, IS-11, Issue #32.
"""

from __future__ import annotations

import json
import logging
import os
from typing import List, Optional
import httpx

from app.providers.types import Claim, Evidence, ProviderUnavailableError

logger = logging.getLogger(__name__)


class RemoteLLMProvider:
    """Implementação do protocolo LLMProvider para servidores remotos compatíveis (OpenAI/vLLM)."""

    name: str = "remote"
    is_mock: bool = False

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 8.0,
    ) -> None:
        self.base_url = (base_url or os.getenv("REMOTE_LLM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("REMOTE_LLM_API_KEY", "")
        self.model = model or os.getenv("REMOTE_LLM_MODEL", "qwen2.5:7b")
        self.timeout = float(os.getenv("REMOTE_LLM_TIMEOUT_SECONDS", str(timeout_seconds)))

    async def extract_claims(self, transcript: str, video_title: str) -> List[Claim]:
        """Extrai proposições atômicas checáveis via API remota compatível com chat completions."""
        if not self.base_url:
            raise ProviderUnavailableError("REMOTE_LLM_BASE_URL não configurada para o provedor remoto.")

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        system_prompt = (
            "Você é um especialista em fact-checking. "
            "Extraia de 2 a 4 alegações factuais atômicas da transcrição. "
            "Responda estritamente em JSON: {\"claims\": [{\"text\": \"...\", \"search_query\": \"...\"}]}"
        )
        user_content = f"Título: {video_title}\n\nTranscrição:\n{transcript[:2500]}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                if res.status_code != 200:
                    raise ProviderUnavailableError(f"Provedor remoto respondeu HTTP {res.status_code}")

                data = res.json()
                content = data["choices"][0]["message"]["content"]
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
                raise ProviderUnavailableError("Nenhuma alegação válida retornada pelo provedor remoto.")
        except Exception as exc:
            if isinstance(exc, ProviderUnavailableError):
                raise
            raise ProviderUnavailableError(f"Falha de comunicação com provedor remoto: {exc}") from exc

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
