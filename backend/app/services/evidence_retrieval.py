"""Recuperação auditável sem inferência LLM para o modo Evidence-Only."""

import logging

from app.schemas import Evidence, EvidenceProvenance
from ml.retrieval.search import search
from ml.schemas.evidence import EvidenceRecord

logger = logging.getLogger(__name__)


def retrieve_evidence(query: str) -> list[tuple[str, Evidence]]:
    try:
        hits = search(query, k=5)
    except Exception as exc:
        logger.warning("Busca vetorial indisponível (%s)", type(exc).__name__)
        return []
    result = []
    for hit in hits:
        record = hit.record
        if not isinstance(record, EvidenceRecord) or not record.review_url or not record.provenance:
            continue
        # Similaridade de busca não comprova uma relação factual com a fala do vídeo.
        result.append(
            (
                record.claim_text,
                Evidence(
                    sourceId=record.evidence_id,
                    relation="contextualizes",
                    title=record.review_title or record.claim_text,
                    url=record.review_url,
                    publishedAt=record.published_at.isoformat() if record.published_at else "",
                    publisher=record.publisher or "",
                    snippet=record.evidence_summary,
                    provenance=EvidenceProvenance(
                        dataset=record.dataset,
                        indexedAt=record.provenance.ingested_at.isoformat(),
                        contentHash=record.provenance.content_hash,
                    ),
                ),
            )
        )
    return result
