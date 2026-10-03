"""Provedor Mock determinístico e sem dependência de rede para testes locais.

Garantias:
- 100% determinístico e offline.
- is_mock = True explicito.
- Expõe ANALYSIS_MODE = "mock" para marcar respostas geradas por mock.
- Bloqueado em produção pelo ProviderFactory (MockInProductionError).

Refs: ADR-001, IS-11.
"""

from __future__ import annotations

from typing import List
from app.providers.types import Claim, Evidence

ANALYSIS_MODE = "mock"


class MockProvider:
    """Implementação mock do protocolo LLMProvider para testes e CI."""

    name: str = "mock"
    is_mock: bool = True

    async def extract_claims(self, transcript: str, video_title: str) -> List[Claim]:
        """Retorna alegações sintéticas determinísticas baseadas no conteúdo da transcrição."""
        # Extração determinística mínima para fixture de testes
        words = transcript.strip().split()
        sample_sentence = " ".join(words[:15]) if len(words) >= 15 else transcript.strip()

        return [
            Claim(
                id="mock-clm-01",
                text=f"Alegação extraída (mock): {sample_sentence}",
                search_query=sample_sentence[:40],
                status="inconclusiva",
                evidence_summary="Alegação sintetizada por MockProvider em ambiente de teste.",
                confidence=0.85,
            )
        ]

    async def generate_reflection(
        self,
        claims: List[Claim],
        evidence: List[Evidence],
    ) -> List[str]:
        """Retorna perguntas reflexivas padrão determinísticas sem inferência real."""
        return [
            "Quais fontes primárias foram consultadas para embasar os dados apresentados?",
            "As conclusões apresentadas levam em conta o contexto temporal da publicação?",
            "Existem evidências científicas revisadas por pares que sustentam a afirmação?",
        ]
