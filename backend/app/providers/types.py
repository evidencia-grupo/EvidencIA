"""Tipos canônicos e exceções para a interface de provedores LLM.

Define os modelos de dados desacoplados de qualquer backend de inferência
específico, além das exceções padronizadas de governança e disponibilidade.

Refs: ADR-001, IS-11.
"""

from __future__ import annotations

from typing import Optional, Union
from pydantic import BaseModel, Field

from ml.schemas.evidence import EvidenceRecord


class ProviderError(Exception):
    """Exceção base para erros em provedores de LLM."""


class ProviderUnavailableError(ProviderError):
    """Lançada quando o provedor de LLM configurado está inacessível ou fora do ar."""


class MockInProductionError(ProviderError):
    """Lançada imediatamente (fail-fast) se o provider mock for acionado em ambiente de produção.

    Garantia central ADR-001: Mocks nunca podem aparecer silenciosamente em produção.
    """


class Claim(BaseModel):
    """Alegação atômica checável extraída pela LLM."""

    id: Optional[str] = Field(None, description="Identificador único da alegação")
    text: str = Field(..., min_length=1, description="Texto exato da alegação")
    search_query: Optional[str] = Field(None, description="Termo de busca otimizado para retrieval")
    status: Optional[str] = Field(None, description="Veredito preliminar sugerido pela LLM")
    evidence_summary: Optional[str] = Field(None, description="Resumo preliminar das evidências")
    confidence: float = Field(0.90, ge=0.0, le=1.0, description="Grau de confiança da extração")


class EvidenceRef(BaseModel):
    """Referência leve a uma evidência recuperada.

    Utilizada como DTO simplificado caso o registro completo EvidenceRecord
    não esteja carregado em memória.
    """

    evidence_id: str
    claim_text: str
    verdict: str = "unknown"
    summary: Optional[str] = None
    source_url: Optional[str] = None


# Escolha arquitetural documentada:
# O tipo Evidence aceito pela interface LLMProvider aceita tanto o schema canônico
# EvidenceRecord (ml.schemas.evidence) quanto a referência leve EvidenceRef.
Evidence = Union[EvidenceRecord, EvidenceRef]
