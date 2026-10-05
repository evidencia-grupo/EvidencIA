"""Módulo de validação de registros do pipeline EvidencIA.

Valida nulos, duplicatas, textos vazios e URLs inválidas.
Retorna um ``ValidationReport`` sem levantar exceção por registro.

Refs: ADR-001, IS-04.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Union
from urllib.parse import urlparse

from ml.schemas.evidence import EvidenceRecord, NewsRecord

logger = logging.getLogger(__name__)

CanonicalRecord = Union[EvidenceRecord, NewsRecord]


@dataclass
class ValidationIssue:
    """Descreve um problema encontrado em um registro."""

    record_id: str
    field: str
    issue: str


@dataclass
class ValidationReport:
    """Relatório de validação de um batch de registros."""

    total: int = 0
    valid: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def invalid(self) -> int:
        """Número de registros com ao menos um problema."""
        return self.total - self.valid

    def add_issue(self, record_id: str, field_name: str, issue: str) -> None:
        """Registra um problema de validação."""
        self.issues.append(ValidationIssue(record_id=record_id, field=field_name, issue=issue))

    def summary(self) -> str:
        """Retorna string de resumo do relatório."""
        return (
            f"Validação: {self.total} registros | "
            f"{self.valid} válidos | "
            f"{self.invalid} com problemas | "
            f"{len(self.issues)} ocorrências"
        )


def _is_valid_url(url: str) -> bool:
    """Verifica se uma URL é válida (http/https com domínio)."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def validate_records(records: list[CanonicalRecord]) -> tuple[list[CanonicalRecord], ValidationReport]:
    """Valida uma lista de registros canônicos.

    Não levanta exceção por registro — registra no ``ValidationReport``.
    Registros com ``claim_text`` vazio são excluídos da saída válida.

    Args:
        records: Lista de ``EvidenceRecord`` ou ``NewsRecord``.

    Returns:
        Tupla ``(registros_válidos, relatório)``.
    """
    report = ValidationReport(total=len(records))
    valid_records: list[CanonicalRecord] = []
    seen_ids: set[str] = set()

    for record in records:
        rid = record.evidence_id
        is_valid = True

        # Duplicata exata por evidence_id
        if rid in seen_ids:
            report.add_issue(rid, "evidence_id", "Duplicata de evidence_id")
            is_valid = False
        else:
            seen_ids.add(rid)

        # Texto vazio
        if isinstance(record, EvidenceRecord):
            if not record.claim_text.strip():
                report.add_issue(rid, "claim_text", "claim_text vazio")
                is_valid = False
            # URL inválida (quando presente)
            if record.review_url and not _is_valid_url(record.review_url):
                report.add_issue(rid, "review_url", f"URL inválida: {record.review_url!r}")
                # Não invalida o registro por URL — apenas registra
        elif isinstance(record, NewsRecord):
            if not record.text.strip():
                report.add_issue(rid, "text", "text vazio")
                is_valid = False

        if is_valid:
            valid_records.append(record)
            report.valid += 1
        else:
            logger.debug("Registro inválido: %s", rid)

    return valid_records, report
