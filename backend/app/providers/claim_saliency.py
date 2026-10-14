"""Heurísticas leves para remover ruído e priorizar alegações verificáveis."""

from __future__ import annotations

import re
import unicodedata


CONVERSATIONAL_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\b(?:ola|bom dia|boa tarde|boa noite|bem vindos|sejam bem vindos)\b",
        r"\bta comecando\b.*\bprograma\b",
        r"\bcomecando\s+(?:o|seu|o seu)?\s*programa\b",
        r"\bprograma de saude aqui\b",
        r"\bv[i]?em pra ca\b",
        r"\bolha so quem vem aqui\b",
        r"\bdoutor[, ]+tudo bem\b",
        r"\btudo bem[, ]+doutor\b",
        r"\bvamos chamar o\b",
        r"\b(?:inscreva-se|inscreva no canal|deixe seu like|curta o video|compartilhe o video)\b",
    )
)

FACTUAL_SIGNALS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\b(?:estudo|estudos|pesquisa|pesquisadores|ensaio clinico|dados|evidencia|relatorio)\b",
        r"\b(?:comprov|demonstr|indica|revel|caus|reduz|aument|previne|trata|cura|aprov)\w*\b",
        r"\b(?:eficacia|risco|mortalidade|incidencia|anticorpos|vacina|medicamento|tratamento)\b",
        r"\b(?:oms|anvisa|ministerio da saude|ipcc|fda)\b",
        r"\b(?:por cento|%|milhoes?|bilhoes?|\d+(?:[.,]\d+)?)\b",
    )
)


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.casefold())
    return " ".join("".join(char for char in normalized if not unicodedata.combining(char)).split())


def score_claim_saliency(text: str) -> float:
    """Dá prioridade a frases factuais e zera saudações, chamadas e conversa fiada."""
    normalized = _normalize(text)
    if any(pattern.search(normalized) for pattern in CONVERSATIONAL_PATTERNS):
        return 0.0

    return 1.0 + sum(bool(pattern.search(normalized)) for pattern in FACTUAL_SIGNALS)