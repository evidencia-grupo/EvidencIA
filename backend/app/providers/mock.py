"""Provedor Mock determinístico e sem dependência de rede para testes locais.

Garantias:
- 100% determinístico e offline.
- is_mock = True explicito.
- Expõe ANALYSIS_MODE = "mock" para marcar respostas geradas por mock.
- Bloqueado em produção pelo ProviderFactory (MockInProductionError).

Refs: ADR-001, IS-11.
"""

from __future__ import annotations

import re
from typing import List
from app.providers.base import LLMProvider
from app.providers.types import Claim, Evidence

ANALYSIS_MODE = "mock"


class MockLLMProvider(LLMProvider):
    """Implementação mock do protocolo LLMProvider para testes e CI."""

    name: str = "mock"
    is_mock: bool = True

    async def extract_claims(self, transcript: str, video_title: str) -> List[Claim]:
        """Retorna alegações sintéticas determinísticas baseadas no conteúdo da transcrição."""
        sentences = re.split(r"(?<=[.!?])\s+", transcript.strip())
        subjective = re.compile(r"^(eu\s+)?(acho|prefiro|adoro|gosto|detesto)|^na minha opinião", re.IGNORECASE)
        factual = [sentence for sentence in sentences if not subjective.search(sentence)]
        return [
            Claim(id=f"mock-clm-{index + 1:02d}", text=sentence, search_query=sentence[:40])
            for index, sentence in enumerate(factual[:4])
        ]

    async def generate_reflection(
        self,
        claims: List[Claim],
        evidence: List[Evidence],
    ) -> List[str]:
        """Retorna perguntas reflexivas padrão determinísticas sem inferência real."""
        if not claims:
            return []
        claim_text = claims[0].text
        return [
            f'Quais fontes primárias ajudam a investigar a afirmação "{claim_text}"?',
            "Que dados independentes permitem comparar as evidências desta alegação?",
            "Como a data e o contexto desta afirmação influenciam sua interpretação?",
        ]


# Compatibilidade com consumidores existentes.
MockProvider = MockLLMProvider
