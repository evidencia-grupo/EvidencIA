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
            "Extraia de 0 a 4 alegações factuais atômicas da transcrição. "
            "Responda estritamente em JSON: {\"claims\": [{\"text\": \"...\", \"search_query\": \"...\"}]}"
        )
        system_prompt += (
            " Cada alegação deve conter uma única proposição verificável, preservando sujeitos, datas e qualificadores. "
            "Não invente fatos nem use o título como alegação. Ignore preferências, opiniões e saudações. "
            'Se não houver fatos verificáveis, retorne {"claims": []}. Não atribua notas ou vereditos ao vídeo.'
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
                raw_claims = parsed["claims"]
                if not isinstance(raw_claims, list):
                    raise ValueError("Lista de alegações inválida")
                if not raw_claims:
                    return []
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
        if not claims:
            return []
        claim_text = claims[0].text
        return [
            f'Quais fontes primárias ajudam a investigar a afirmação "{claim_text}"?',
            "Que dados independentes permitem comparar as evidências desta alegação?",
            "Como a data e o contexto desta afirmação influenciam sua interpretação?",
        ]
