"""Módulo de normalização de texto para o pipeline EvidencIA.

Aplica normalização determinística: unicode NFKC, espaços, minúsculas.
NÃO remove acentos (preserva características do PT-BR).

Refs: ADR-001, IS-05.
"""

from __future__ import annotations

import re
import unicodedata

from ml.schemas.evidence import EvidenceRecord, NewsRecord


def normalize_text(text: str) -> str:
    """Normaliza texto para comparação e indexação.

    Passos (em ordem):
    1. Unicode NFKC (normaliza formas de caracteres equivalentes)
    2. Colapso de espaços múltiplos para espaço simples
    3. Strip de espaços no início/fim
    4. Minúsculas

    NÃO remove acentos — essencial para PT-BR correto.

    Args:
        text: Texto bruto de entrada.

    Returns:
        Texto normalizado, determinístico.
    """
    # Unicode NFKC
    normalized = unicodedata.normalize("NFKC", text)
    # Colapso de espaços (incluindo tab, newline)
    normalized = re.sub(r"\s+", " ", normalized)
    # Strip + minúsculas
    return normalized.strip().lower()


def normalize_evidence_record(record: EvidenceRecord) -> EvidenceRecord:
    """Preenche ``normalized_claim`` no ``EvidenceRecord`` com texto normalizado.

    Args:
        record: Registro de evidência a normalizar.

    Returns:
        Novo ``EvidenceRecord`` com ``normalized_claim`` preenchido.
        (Pydantic v2: cria cópia com model_copy)
    """
    normalized_claim = normalize_text(record.claim_text)
    return record.model_copy(update={"normalized_claim": normalized_claim})


def normalize_news_record(record: NewsRecord) -> NewsRecord:
    """Adiciona metadados lexicais ao ``NewsRecord``.

    Preenche ``lexical_metadata`` com contagens básicas.

    Args:
        record: Registro de notícia a normalizar.

    Returns:
        Novo ``NewsRecord`` com ``lexical_metadata`` atualizado.
    """
    text = record.text
    words = text.split()
    caps_words = sum(1 for w in words if w.isupper() and len(w) > 1)
    exclamations = text.count("!")
    questions = text.count("?")

    updated_meta = {
        **record.lexical_metadata,
        "char_count": len(text),
        "word_count": len(words),
        "caps_word_count": caps_words,
        "exclamation_count": exclamations,
        "question_count": questions,
        "normalized_text": normalize_text(text),
    }
    return record.model_copy(update={"lexical_metadata": updated_meta})
