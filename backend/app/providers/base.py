"""Contrato abstrato para Provedores de Modelos de Linguagem (LLMProvider).

Estabelece a abstração padronizada para extração de alegações e geração de reflexão
sem acoplamento direto com Ollama, APIs externas ou mocks.

Refs: ADR-001, IS-11.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.providers.types import Claim, Evidence


class LLMProvider(ABC):
    """Classe abstrata oficial para provedores de LLM no EvidencIA.

    Todo provedor deve implementar os dois métodos assíncronos antes de ser instanciado.
    """

    #: Identificador legível do provedor (ex.: 'ollama', 'remote', 'mock')
    name: str

    #: Flag booleana estrita indicando se a instância é mock
    is_mock: bool

    @abstractmethod
    async def extract_claims(self, transcript: str, video_title: str) -> list[Claim]:
        """Extrai proposições atômicas checáveis a partir da transcrição de um vídeo.

        Args:
            transcript: Texto completo ou parcial higienizado da fala.
            video_title: Título original do vídeo para contexto.

        Returns:
            Lista de alegações estruturadas (Claim).
        """
        ...

    @abstractmethod
    async def generate_reflection(
        self,
        claims: list[Claim],
        evidence: list[Evidence],
    ) -> list[str]:
        """Gera perguntas de reflexão não-dogmáticas orientadas por evidências.

        A LLM atua como formuladora de perguntas críticas, nunca como juíza da verdade.

        Args:
            claims: Alegações extraídas examinadas.
            evidence: Evidências reais recuperadas das bases curadas.

        Returns:
            Lista de 2 a 4 perguntas reflexivas orientadoras.
        """
        ...
