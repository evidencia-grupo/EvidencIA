"""Contrato Protocol para Provedores de Modelos de Linguagem (LLMProvider).

Estabelece a abstração padronizada para extração de alegações e geração de reflexão
sem acoplamento direto com Ollama, APIs externas ou mocks.

Refs: ADR-001, IS-11.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from app.providers.types import Claim, Evidence


@runtime_checkable
class LLMProvider(Protocol):
    """Protocolo oficial para provedores de LLM no EvidencIA.

    Qualquer provider deve implementar este protocolo para poder ser instanciado
    pelo `ProviderFactory`. A verificação em runtime é suportada via `@runtime_checkable`.
    """

    #: Identificador legível do provedor (ex.: 'ollama', 'remote', 'mock')
    name: str

    #: Flag booleana estrita indicando se a instância é mock
    is_mock: bool

    async def extract_claims(self, transcript: str, video_title: str) -> list[Claim]:
        """Extrai proposições atômicas checáveis a partir da transcrição de um vídeo.

        Args:
            transcript: Texto completo ou parcial higienizado da fala.
            video_title: Título original do vídeo para contexto.

        Returns:
            Lista de alegações estruturadas (Claim).
        """
        ...

    async def generate_reflection(
        self,
        claims: list[Claim],
        evidence: list[Evidence],
    ) -> list[str]:
        """Gera perguntas de reflexão não-dogmáticas orientadas por evidências (Sprint 2 / HU02).

        A LLM atua como formuladora de perguntas críticas, nunca como juíza da verdade.

        Args:
            claims: Alegações extraídas examinadas.
            evidence: Evidências reais recuperadas das bases curadas.

        Returns:
            Lista de 2 a 4 perguntas reflexivas orientadoras.
        """
        ...
