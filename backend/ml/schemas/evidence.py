"""Schema canônico de evidência para o pipeline EvidencIA.

Módulo central de tipos: define EvidenceRecord, NewsRecord e enumerações
de veredito para garantir que ausência de evidência NUNCA mapeie para
``contradicted``.

Refs: ADR-001, GQ05.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerações
# ---------------------------------------------------------------------------


class VerdictNormalized(str, Enum):
    """Veredito normalizado para todos os registros de evidência.

    Ausência de evidência/veredito NUNCA mapeia para ``contradicted``.
    O valor padrão (quando desconhecido ou ausente) é ``unknown``.

    Mapeamentos PT-BR → VerdictNormalized:
    - "falso", "false", "fake"              → contradicted
    - "verdadeiro", "correto", "true"       → supported
    - "enganoso", "misleading", "impreciso" → misleading
    - "parcialmente verdadeiro", "misto"    → mixed
    - "sem evidência", "não verificado"     → unverifiable
    - (qualquer desconhecido/None/vazio)    → unknown
    """

    supported = "supported"
    contradicted = "contradicted"
    misleading = "misleading"
    mixed = "mixed"
    unverifiable = "unverifiable"
    unknown = "unknown"


# Tabela configurável de mapeamento PT-BR → VerdictNormalized.
# Usada pelos adapters; pode ser sobrescrita via YAML externo.
VERDICT_MAP_PT_BR: dict[str, VerdictNormalized] = {
    # Falso / contraditado
    "falso": VerdictNormalized.contradicted,
    "falsa": VerdictNormalized.contradicted,
    "false": VerdictNormalized.contradicted,
    "fake": VerdictNormalized.contradicted,
    "incorreto": VerdictNormalized.contradicted,
    "incorreta": VerdictNormalized.contradicted,
    "mentira": VerdictNormalized.contradicted,
    # Verdadeiro / apoiado
    "verdadeiro": VerdictNormalized.supported,
    "verdadeira": VerdictNormalized.supported,
    "correto": VerdictNormalized.supported,
    "correta": VerdictNormalized.supported,
    "true": VerdictNormalized.supported,
    "real": VerdictNormalized.supported,
    "apoiada": VerdictNormalized.supported,
    # Enganoso / impreciso
    "enganoso": VerdictNormalized.misleading,
    "enganosa": VerdictNormalized.misleading,
    "impreciso": VerdictNormalized.misleading,
    "imprecisa": VerdictNormalized.misleading,
    "exagerado": VerdictNormalized.misleading,
    "exagerada": VerdictNormalized.misleading,
    "misleading": VerdictNormalized.misleading,
    "distorcido": VerdictNormalized.misleading,
    "distorcida": VerdictNormalized.misleading,
    # Misto / parcial
    "parcialmente verdadeiro": VerdictNormalized.mixed,
    "parcialmente verdadeiro/falso": VerdictNormalized.mixed,
    "parcialmente falso": VerdictNormalized.mixed,
    "misto": VerdictNormalized.mixed,
    "mixed": VerdictNormalized.mixed,
    # Sem evidência / não verificável
    "sem evidência": VerdictNormalized.unverifiable,
    "não verificado": VerdictNormalized.unverifiable,
    "unverifiable": VerdictNormalized.unverifiable,
    "inconclusivo": VerdictNormalized.unverifiable,
    "inconclusiva": VerdictNormalized.unverifiable,
    # Desconhecido (default)
    "": VerdictNormalized.unknown,
    "unknown": VerdictNormalized.unknown,
    "desconhecido": VerdictNormalized.unknown,
}


def normalize_verdict(raw: Optional[str]) -> VerdictNormalized:
    """Converte veredito bruto em ``VerdictNormalized``.

    Garantia central: ``None``, string vazia ou valor desconhecido
    resultam em ``VerdictNormalized.unknown`` — NUNCA em ``contradicted``.

    Args:
        raw: Veredito bruto (PT-BR, EN ou ``None``).

    Returns:
        ``VerdictNormalized`` correspondente.
    """
    if raw is None:
        return VerdictNormalized.unknown
    key = raw.strip().lower()
    return VERDICT_MAP_PT_BR.get(key, VerdictNormalized.unknown)


# ---------------------------------------------------------------------------
# Modelos de metadados
# ---------------------------------------------------------------------------


class Provenance(BaseModel):
    """Rastreabilidade de origem de um registro."""

    source_url: str = Field(..., description="URL da fonte original do dataset")
    content_hash: str = Field(
        ...,
        description="Hash SHA-256 do conteúdo do arquivo de origem (formato: sha256:<hex>)",
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    ingested_at: datetime = Field(..., description="Data/hora da ingestão (timezone-aware)")

    @field_validator("source_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Valida que source_url é uma URL bem-formada com esquema http/https."""
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"source_url deve usar http/https, recebido: {v!r}")
        if not parsed.netloc:
            raise ValueError(f"source_url deve ter domínio válido: {v!r}")
        return v

    @field_validator("ingested_at")
    @classmethod
    def validate_timezone_aware(cls, v: datetime) -> datetime:
        """Garante que ingested_at é timezone-aware."""
        if v.tzinfo is None:
            raise ValueError("ingested_at deve ser timezone-aware (use datetime com tzinfo)")
        return v


class EmbeddingMeta(BaseModel):
    """Metadados do embedding gerado para o registro."""

    model: str = Field(..., description="Nome do modelo de embedding (ex.: 'neuralmind/bert-base-portuguese-cased')")
    dimension: int = Field(..., gt=0, description="Dimensão do vetor de embedding")


# ---------------------------------------------------------------------------
# Modelo canônico: EvidenceRecord (fact-checks)
# ---------------------------------------------------------------------------


class EvidenceRecord(BaseModel):
    """Registro canônico de evidência de fact-checking.

    Produzido pelos adapters de FactChecks.br e ClaimReview.
    O campo ``verdict_normalized`` NUNCA é ``contradicted`` por ausência de evidência.
    """

    # Identificação
    evidence_id: str = Field(
        ...,
        description="ID único no formato '<dataset>:<fonte>:<id_original>'",
        pattern=r"^[a-zA-Z0-9_.-]+:[a-zA-Z0-9_.-]+:.+$",
    )
    record_type: str = Field(default="fact_check", description="Tipo do registro")

    # Origem
    dataset: str = Field(..., description="Nome do dataset de origem (ex.: 'factchecksbr')")
    dataset_version: str = Field(..., description="Versão do dataset (ex.: '2024-01')")
    language: str = Field(default="pt-BR", description="Código BCP-47 do idioma")

    # Conteúdo da alegação
    claim_text: str = Field(..., min_length=1, description="Texto original da alegação")
    normalized_claim: str = Field(default="", description="Alegação normalizada (unicode NFKC, minúsculas)")

    # Veredito
    verdict_raw: Optional[str] = Field(None, description="Veredito bruto conforme dataset de origem")
    verdict_normalized: VerdictNormalized = Field(
        default=VerdictNormalized.unknown,
        description="Veredito normalizado. Ausência → unknown, NUNCA → contradicted",
    )

    # Metadados da checagem
    review_title: Optional[str] = Field(None, description="Título da matéria de checagem")
    review_url: Optional[str] = Field(None, description="URL da matéria de checagem (https)")
    publisher: Optional[str] = Field(None, description="Agência de checagem (ex.: 'Aos Fatos')")
    published_at: Optional[datetime] = Field(None, description="Data de publicação (timezone-aware ou None)")

    # Resumo e fontes de evidência
    evidence_summary: Optional[str] = Field(None, description="Resumo da evidência em texto livre")
    source_urls: list[str] = Field(default_factory=list, description="URLs das fontes usadas na checagem")

    # Classificação temática
    topic: Optional[str] = Field(None, description="Tópico/tema da alegação")
    category: Optional[str] = Field(None, description="Categoria (saúde, política, economia, ...)")

    # Rastreabilidade
    provenance: Optional[Provenance] = Field(None, description="Metadados de proveniência do registro")

    # Embedding (preenchido pelo pipeline de indexação)
    embedding: Optional[list[float]] = Field(None, description="Vetor de embedding (preenchido por index.py)")
    embedding_meta: Optional[EmbeddingMeta] = Field(None, description="Metadados do modelo de embedding")

    @field_validator("review_url")
    @classmethod
    def validate_review_url(cls, v: Optional[str]) -> Optional[str]:
        """Valida que review_url usa http/https quando presente."""
        if v is None:
            return v
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"review_url deve usar http/https: {v!r}")
        if not parsed.netloc:
            raise ValueError(f"review_url deve ter domínio válido: {v!r}")
        return v

    @field_validator("published_at")
    @classmethod
    def validate_published_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Garante que published_at é timezone-aware quando presente."""
        if v is not None and v.tzinfo is None:
            raise ValueError("published_at deve ser timezone-aware ou None")
        return v

    @model_validator(mode="before")
    @classmethod
    def coerce_verdict_normalized(cls, data: Any) -> Any:
        """Garante que verdict_normalized é derivado de verdict_raw quando não fornecido.

        Invariante: ausência de veredito → unknown, NUNCA contradicted.
        """
        if isinstance(data, dict):
            if "verdict_normalized" not in data or data.get("verdict_normalized") is None:
                raw = data.get("verdict_raw")
                data["verdict_normalized"] = normalize_verdict(raw)
        return data

    def compute_content_hash(self) -> str:
        """Computa SHA-256 do claim_text para uso em Provenance.content_hash."""
        digest = hashlib.sha256(self.claim_text.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"


# ---------------------------------------------------------------------------
# Modelo canônico: NewsRecord (Fake.br — corpus linguístico)
# ---------------------------------------------------------------------------


class NewsRecord(BaseModel):
    """Registro de notícia do corpus Fake.br.

    **ATENÇÃO**: Fake.br é um corpus linguístico de classificação de texto,
    NÃO uma base de verdades factuais. O campo ``label`` indica classificação
    do corpus, não evidência de fact-checking.
    Papel no pipeline: ``linguistic_corpus`` (ver sources.yaml).
    """

    # Identificação
    evidence_id: str = Field(
        ...,
        description="ID único no formato 'fakebr:<subset>:<id>'",
    )
    record_type: str = Field(default="news", description="Tipo do registro")

    # Origem
    dataset: str = Field(default="fakebr", description="Dataset de origem")
    dataset_version: str = Field(..., description="Versão do dataset")
    language: str = Field(default="pt-BR", description="Código BCP-47 do idioma")

    # Conteúdo
    text: str = Field(..., min_length=1, description="Texto completo ou trecho da notícia")
    label: str = Field(..., description="Rótulo do corpus: 'fake' ou 'true'")

    # Metadados opcionais
    author: Optional[str] = Field(None, description="Autor da notícia (quando disponível)")
    category: Optional[str] = Field(None, description="Categoria editorial")
    published_at: Optional[datetime] = Field(None, description="Data de publicação (timezone-aware ou None)")

    # Metadados lexicais (preenchidos por normalize.py)
    lexical_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadados lexicais: token_count, char_count, has_caps_words, etc.",
    )

    # Rastreabilidade
    provenance: Optional[Provenance] = Field(None, description="Metadados de proveniência")

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        """Valida que label é 'fake' ou 'true'."""
        normalized = v.strip().lower()
        if normalized not in ("fake", "true"):
            raise ValueError(f"label deve ser 'fake' ou 'true', recebido: {v!r}")
        return normalized

    @field_validator("published_at")
    @classmethod
    def validate_published_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Garante que published_at é timezone-aware quando presente."""
        if v is not None and v.tzinfo is None:
            raise ValueError("published_at deve ser timezone-aware ou None")
        return v
