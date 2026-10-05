"""Adapter stub para ClaimReview (Google Fact Check Tools API).

Papel: ``external_complementary`` (ver sources.yaml).
Chave de API via env ``GOOGLE_FACT_CHECK_API_KEY`` — NUNCA commitada.

Esta implementação é um stub: lança ``NotImplementedError`` com instruções.
Refs: ADR-001, IS-04.
"""

from __future__ import annotations

import logging
from typing import Iterator

from ml.datasets.adapters.base import DatasetAdapter, register_adapter
from ml.schemas.evidence import EvidenceRecord

logger = logging.getLogger(__name__)


@register_adapter
class ClaimReviewAdapter(DatasetAdapter):
    """Adapter stub para Google Fact Check Tools API (ClaimReview).

    Requer chave de API via env GOOGLE_FACT_CHECK_API_KEY.
    Implementação completa: Sprint 2 (IS-06 / S2-01).
    """

    name = "claimreview"

    def parse(self, input_dir: str) -> Iterator[EvidenceRecord]:
        """Stub: levanta NotImplementedError com instruções.

        Args:
            input_dir: Não utilizado neste stub.

        Raises:
            NotImplementedError: Sempre. Implementar na Sprint 2.
        """
        raise NotImplementedError(
            "ClaimReviewAdapter não implementado. "
            "Para usar a Google Fact Check Tools API: "
            "(1) defina GOOGLE_FACT_CHECK_API_KEY no .env; "
            "(2) implemente o cliente HTTP neste módulo (Sprint 2). "
            "Ver issue: S2-01 'Provider abstraction migration'."
        )
