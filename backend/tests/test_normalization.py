"""Testes de normalização e validação do schema canônico de evidências.

Garantias testadas:
- Normalização determinística de texto (NFKC, espaços, minúsculas, sem remover acentos).
- Veredito ausente NUNCA mapeia para contradicted (sempre unknown).
- Mapeamento cobre vereditos típicos em PT-BR (falso, enganoso, verdadeiro, impreciso, sem evidência).
- Validação Pydantic rejeita claim_text vazio e URLs mal-formadas.
- published_at é timezone-aware ou None.

Refs: ADR-001, IS-05.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from ml.schemas.evidence import (
    EvidenceRecord,
    NewsRecord,
    VerdictNormalized,
    normalize_verdict,
)
from ml.datasets.normalize import normalize_text, normalize_news_record


def test_normalize_text_deterministic():
    """Garante que a normalização de texto é determinística e preserva acentuação PT-BR."""
    sample = "  Atenção:   Vacinas NÃO causam    Autismo!  \n"
    res1 = normalize_text(sample)
    res2 = normalize_text(sample)

    assert res1 == res2
    assert res1 == "atenção: vacinas não causam autismo!"
    assert "não" in res1
    assert "atenção" in res1


def test_verdict_absent_never_maps_to_contradicted():
    """Garantia central ADR-001: Ausência de veredito NUNCA mapeia para contradicted."""
    assert normalize_verdict(None) == VerdictNormalized.unknown
    assert normalize_verdict("") == VerdictNormalized.unknown
    assert normalize_verdict("   ") == VerdictNormalized.unknown
    assert normalize_verdict("não registrado") == VerdictNormalized.unknown
    assert normalize_verdict("qualquer_coisa_estranha") == VerdictNormalized.unknown

    # Instanciando EvidenceRecord sem veredito
    record = EvidenceRecord(
        evidence_id="factchecksbr:sample:001",
        dataset="factchecksbr",
        dataset_version="2024-01",
        claim_text="Alegação sem veredito informado.",
        verdict_raw=None,
    )
    assert record.verdict_normalized == VerdictNormalized.unknown
    assert record.verdict_normalized != VerdictNormalized.contradicted


def test_verdict_mapping_covers_ptbr_typical_terms():
    """Testa cobertura das categorias de veredito frequentes em agências brasileiras."""
    # Falsos / contraditados
    assert normalize_verdict("Falso") == VerdictNormalized.contradicted
    assert normalize_verdict("falsa") == VerdictNormalized.contradicted
    assert normalize_verdict("fake") == VerdictNormalized.contradicted

    # Verdadeiros / apoiados
    assert normalize_verdict("Verdadeiro") == VerdictNormalized.supported
    assert normalize_verdict("correto") == VerdictNormalized.supported
    assert normalize_verdict("apoiada") == VerdictNormalized.supported

    # Enganosos / imprecisos
    assert normalize_verdict("Enganoso") == VerdictNormalized.misleading
    assert normalize_verdict("impreciso") == VerdictNormalized.misleading

    # Sem evidência / inconclusivos
    assert normalize_verdict("sem evidência") == VerdictNormalized.unverifiable
    assert normalize_verdict("não verificado") == VerdictNormalized.unverifiable
    assert normalize_verdict("inconclusivo") == VerdictNormalized.unverifiable

    # Misto / parcialmente verdadeiro
    assert normalize_verdict("parcialmente verdadeiro") == VerdictNormalized.mixed
    assert normalize_verdict("misto") == VerdictNormalized.mixed


def test_pydantic_validation_empty_claim():
    """Rejeita claim_text vazio."""
    with pytest.raises(ValidationError):
        EvidenceRecord(
            evidence_id="factchecksbr:sample:002",
            dataset="factchecksbr",
            dataset_version="2024-01",
            claim_text="",
        )


def test_pydantic_validation_invalid_url():
    """Rejeita URLs mal-formadas."""
    with pytest.raises(ValidationError):
        EvidenceRecord(
            evidence_id="factchecksbr:sample:003",
            dataset="factchecksbr",
            dataset_version="2024-01",
            claim_text="Texto válido",
            review_url="ftp://invalido.com/teste",
        )


def test_published_at_timezone_aware():
    """published_at deve ser timezone-aware ou None; nunca naive datetime."""
    # Válido: timezone-aware
    rec_tz = EvidenceRecord(
        evidence_id="factchecksbr:sample:004",
        dataset="factchecksbr",
        dataset_version="2024-01",
        claim_text="Texto válido",
        published_at=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc),
    )
    assert rec_tz.published_at is not None
    assert rec_tz.published_at.tzinfo is not None

    # Válido: None
    rec_none = EvidenceRecord(
        evidence_id="factchecksbr:sample:005",
        dataset="factchecksbr",
        dataset_version="2024-01",
        claim_text="Texto válido",
        published_at=None,
    )
    assert rec_none.published_at is None

    # Inválido: naive datetime
    with pytest.raises(ValidationError):
        EvidenceRecord(
            evidence_id="factchecksbr:sample:006",
            dataset="factchecksbr",
            dataset_version="2024-01",
            claim_text="Texto válido",
            published_at=datetime(2026, 1, 15, 12, 0),
        )


def test_news_record_normalization():
    """Testa normalização e metadados lexicais do NewsRecord (Fake.br)."""
    news = NewsRecord(
        evidence_id="fakebr:sample:001",
        dataset_version="2024-01",
        text="URGENTE! O governo aprovou o novo benefício?",
        label="fake",
    )
    norm = normalize_news_record(news)

    assert norm.lexical_metadata["exclamation_count"] == 1
    assert norm.lexical_metadata["question_count"] == 1
    assert norm.lexical_metadata["caps_word_count"] == 1
    assert "urgente! o governo aprovou o novo benefício?" in norm.lexical_metadata["normalized_text"]
