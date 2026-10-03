"""Adapter para o dataset FactChecks.br (fake-news-UFG).

Produz ``EvidenceRecord`` com mapeamento de vereditos PT-BR → ``VerdictNormalized``.
Papel: ``fact_check_evidence`` (ver sources.yaml).

Refs: ADR-001, IS-04.
# TODO(verify-format): confirmar colunas reais no repositório oficial
# github.com/fake-news-UFG/FactChecks.br antes do primeiro uso com dados reais.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Iterator

from ml.datasets.adapters.base import DatasetAdapter, register_adapter
from ml.schemas.evidence import EvidenceRecord, VerdictNormalized, normalize_verdict

logger = logging.getLogger(__name__)

# Colunas esperadas conforme sources.yaml
# TODO(verify-format): validar contra o JSON/CSV real do repositório oficial
EXPECTED_COLUMNS = {"claim", "label", "explanation", "source", "url"}

# Mapeamento adicional específico do FactChecks.br (complementa VERDICT_MAP_PT_BR)
# Baseado nos vereditos observados nas agências brasileiras IFCN
# TODO(verify-format): confirmar lista completa de vereditos nos dados reais
FACTCHECKSBR_VERDICT_MAP: dict[str, VerdictNormalized] = {
    "falso": VerdictNormalized.contradicted,
    "falsa": VerdictNormalized.contradicted,
    "mentira": VerdictNormalized.contradicted,
    "incorreto": VerdictNormalized.contradicted,
    "verdadeiro": VerdictNormalized.supported,
    "verdadeira": VerdictNormalized.supported,
    "correto": VerdictNormalized.supported,
    "correta": VerdictNormalized.supported,
    "enganoso": VerdictNormalized.misleading,
    "enganosa": VerdictNormalized.misleading,
    "impreciso": VerdictNormalized.misleading,
    "imprecisa": VerdictNormalized.misleading,
    "exagerado": VerdictNormalized.misleading,
    "distorcido": VerdictNormalized.misleading,
    "parcialmente verdadeiro": VerdictNormalized.mixed,
    "parcialmente falso": VerdictNormalized.mixed,
    "misto": VerdictNormalized.mixed,
    "sem evidência": VerdictNormalized.unverifiable,
    "não verificado": VerdictNormalized.unverifiable,
    "indeterminado": VerdictNormalized.unverifiable,
    "inconclusivo": VerdictNormalized.unverifiable,
}


def _map_verdict(raw: str | None) -> VerdictNormalized:
    """Mapeia veredito bruto do FactChecks.br → ``VerdictNormalized``.

    Usa a tabela local antes de delegar para ``normalize_verdict`` global.
    Garantia: None ou valor desconhecido → ``unknown``, NUNCA ``contradicted``.

    Args:
        raw: Veredito bruto como string.

    Returns:
        ``VerdictNormalized`` correspondente.
    """
    if raw is None:
        return VerdictNormalized.unknown
    key = raw.strip().lower()
    if key in FACTCHECKSBR_VERDICT_MAP:
        return FACTCHECKSBR_VERDICT_MAP[key]
    # Delega para o mapeamento global como fallback
    return normalize_verdict(raw)


@register_adapter
class FactChecksBrAdapter(DatasetAdapter):
    """Adapter para o dataset FactChecks.br.

    Lê arquivos CSV ou JSON do diretório ``input_dir`` e produz ``EvidenceRecord``.
    Suporta ambos os formatos; tenta CSV primeiro, depois JSON.
    """

    name = "factchecksbr"

    def parse(self, input_dir: str) -> Iterator[EvidenceRecord]:
        """Lê arquivos do FactChecks.br e produz EvidenceRecords.

        Args:
            input_dir: Diretório com arquivos ``.csv`` ou ``.json`` do dataset.

        Yields:
            ``EvidenceRecord`` por registro válido.

        Raises:
            FileNotFoundError: Se o diretório não existir.
        """
        if not os.path.isdir(input_dir):
            raise FileNotFoundError(f"Diretório não encontrado: {input_dir!r}")

        # Tenta CSV primeiro, depois JSON
        csv_files = sorted(f for f in os.listdir(input_dir) if f.endswith(".csv"))
        json_files = sorted(f for f in os.listdir(input_dir) if f.endswith(".json"))

        if not csv_files and not json_files:
            logger.warning("Nenhum arquivo .csv ou .json encontrado em %s", input_dir)
            return

        idx = 0
        for csv_file in csv_files:
            file_path = os.path.join(input_dir, csv_file)
            logger.info("Processando CSV %s", file_path)
            yield from self._parse_csv(file_path, idx_start=idx)
            idx += 1  # simplificado; _parse_csv conta internamente

        for json_file in json_files:
            file_path = os.path.join(input_dir, json_file)
            logger.info("Processando JSON %s", file_path)
            yield from self._parse_json(file_path, idx_start=idx)
            idx += 1

    def _parse_csv(self, file_path: str, idx_start: int = 0) -> Iterator[EvidenceRecord]:
        """Parseia um arquivo CSV do FactChecks.br."""
        with open(file_path, encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            fieldnames = set(reader.fieldnames or [])
            missing = EXPECTED_COLUMNS - fieldnames
            if missing:
                logger.warning(
                    "Colunas ausentes em %s: %s — verifique sources.yaml",
                    file_path,
                    missing,
                )
            for i, row in enumerate(reader):
                record = self.to_canonical(row, idx=idx_start + i, source_file=os.path.basename(file_path))
                if record is not None:
                    yield record

    def _parse_json(self, file_path: str, idx_start: int = 0) -> Iterator[EvidenceRecord]:
        """Parseia um arquivo JSON do FactChecks.br (lista de objetos)."""
        with open(file_path, encoding="utf-8") as fh:
            try:
                data = json.load(fh)
            except json.JSONDecodeError as exc:
                logger.error("Erro ao parsear JSON %s: %s", file_path, exc)
                return

        if not isinstance(data, list):
            # Tenta extrair lista de campo 'data' ou 'claims'
            data = data.get("data") or data.get("claims") or []

        for i, row in enumerate(data):
            record = self.to_canonical(row, idx=idx_start + i, source_file=os.path.basename(file_path))
            if record is not None:
                yield record

    def to_canonical(  # type: ignore[override]
        self,
        raw: dict,
        idx: int = 0,
        source_file: str = "unknown",
    ) -> EvidenceRecord | None:
        """Converte linha bruta em ``EvidenceRecord``.

        Args:
            raw: Dicionário com os dados brutos de um registro.
            idx: Índice sequencial.
            source_file: Nome do arquivo de origem.

        Returns:
            ``EvidenceRecord`` válido ou ``None`` se o registro for inválido.
        """
        # Tenta diferentes nomes de campo (CSV vs JSON podem divergir)
        # TODO(verify-format): unificar após confirmar formato real
        claim_text = (
            (raw.get("claim") or raw.get("claimReviewed") or raw.get("title") or "")
            .strip()
        )
        if not claim_text:
            logger.debug("Registro %d ignorado: claim vazio", idx)
            return None

        verdict_raw = (
            (raw.get("label") or raw.get("rating") or raw.get("reviewRating") or "")
            .strip()
        )
        verdict_normalized = _map_verdict(verdict_raw)

        review_url = (raw.get("url") or raw.get("review_url") or "").strip() or None
        # Validação básica de URL
        if review_url and not review_url.startswith(("http://", "https://")):
            logger.debug("URL inválida no registro %d: %r — ignorando URL", idx, review_url)
            review_url = None

        # Tenta parsear data de publicação
        published_at: datetime | None = None
        raw_date = (raw.get("date") or raw.get("datePublished") or "").strip()
        if raw_date:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
                try:
                    dt = datetime.strptime(raw_date, fmt)
                    # Garante timezone-aware
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    published_at = dt
                    break
                except ValueError:
                    continue

        content_hash = "sha256:" + hashlib.sha256(claim_text.encode("utf-8")).hexdigest()

        return EvidenceRecord(
            evidence_id=f"factchecksbr:{source_file}:{idx:06d}",
            dataset="factchecksbr",
            dataset_version="2024-01",  # TODO(verify-format): extrair versão real
            claim_text=claim_text,
            normalized_claim=claim_text.lower().strip(),
            verdict_raw=verdict_raw or None,
            verdict_normalized=verdict_normalized,
            review_url=review_url,
            publisher=(raw.get("source") or raw.get("author") or "").strip() or None,
            published_at=published_at,
            evidence_summary=(raw.get("explanation") or raw.get("body") or "").strip() or None,
        )
