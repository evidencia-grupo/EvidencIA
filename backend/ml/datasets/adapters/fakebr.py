"""Adapter para o corpus Fake.br (NILC / USP São Carlos).

Produz ``NewsRecord`` — corpus linguístico, NÃO base de verdades factuais.
Papel: ``linguistic_corpus`` (ver sources.yaml).

Refs: ADR-001, IS-04.
# TODO(verify-format): confirmar colunas reais do CSV no repositório oficial
# github.com/roneysco/Fake.br-Corpus antes do primeiro uso com dados reais.
"""

from __future__ import annotations

import csv
import hashlib
import logging
import os
from datetime import timezone
from typing import Iterator

from ml.datasets.adapters.base import DatasetAdapter, register_adapter
from ml.schemas.evidence import NewsRecord

logger = logging.getLogger(__name__)

# Colunas esperadas conforme sources.yaml
# TODO(verify-format): validar contra o CSV real do repositório oficial
EXPECTED_COLUMNS = {"text", "label"}
OPTIONAL_COLUMNS = {"category", "author"}

# Mapeamento de labels do Fake.br → label canônico
LABEL_MAP = {
    "fake": "fake",
    "1": "fake",
    "true": "true",
    "real": "true",
    "0": "true",
}


@register_adapter
class FakeBrAdapter(DatasetAdapter):
    """Adapter para o corpus Fake.br.

    Lê arquivos CSV do diretório ``input_dir`` e produz ``NewsRecord``.

    AVISO: Fake.br é um corpus linguístico de classificação.
    NÃO use os registros como evidências factuais de fact-checking.
    """

    name = "fakebr"

    def parse(self, input_dir: str) -> Iterator[NewsRecord]:
        """Lê CSV(s) do Fake.br e produz NewsRecords.

        Args:
            input_dir: Diretório com arquivos ``.csv`` do corpus Fake.br.

        Yields:
            ``NewsRecord`` por linha válida encontrada.

        Raises:
            FileNotFoundError: Se o diretório não existir.
        """
        if not os.path.isdir(input_dir):
            raise FileNotFoundError(f"Diretório não encontrado: {input_dir!r}")

        csv_files = sorted(f for f in os.listdir(input_dir) if f.endswith(".csv"))
        if not csv_files:
            logger.warning("Nenhum arquivo .csv encontrado em %s", input_dir)
            return

        idx = 0
        for csv_file in csv_files:
            file_path = os.path.join(input_dir, csv_file)
            logger.info("Processando %s", file_path)

            with open(file_path, encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                fieldnames = set(reader.fieldnames or [])

                # Verifica colunas obrigatórias
                missing = EXPECTED_COLUMNS - fieldnames
                if missing:
                    # TODO(verify-format): adaptar se o formato real divergir
                    logger.warning(
                        "Colunas ausentes em %s: %s — verifique sources.yaml",
                        csv_file,
                        missing,
                    )

                for row in reader:
                    record = self.to_canonical(row, idx=idx, source_file=csv_file)
                    if record is not None:
                        yield record
                        idx += 1

    def to_canonical(  # type: ignore[override]
        self,
        raw: dict,
        idx: int = 0,
        source_file: str = "unknown",
    ) -> NewsRecord | None:
        """Converte linha do CSV em ``NewsRecord``.

        Args:
            raw: Dicionário de uma linha do CSV.
            idx: Índice sequencial (para gerar evidence_id único).
            source_file: Nome do arquivo CSV de origem.

        Returns:
            ``NewsRecord`` válido ou ``None`` se a linha for inválida.
        """
        text = (raw.get("text") or "").strip()
        if not text:
            logger.debug("Linha %d ignorada: texto vazio", idx)
            return None

        raw_label = (raw.get("label") or "").strip().lower()
        label = LABEL_MAP.get(raw_label)
        if label is None:
            logger.warning("Label desconhecido %r na linha %d — ignorando", raw_label, idx)
            return None

        # Gera content_hash a partir do texto
        content_hash = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

        return NewsRecord(
            evidence_id=f"fakebr:{source_file}:{idx:06d}",
            dataset="fakebr",
            dataset_version="2024-01",  # TODO(verify-format): extrair versão real do manifest
            text=text,
            label=label,
            author=(raw.get("author") or "").strip() or None,
            category=(raw.get("category") or "").strip() or None,
            published_at=None,  # TODO(verify-format): Fake.br nem sempre fornece data
            lexical_metadata={
                "char_count": len(text),
                "word_count": len(text.split()),
                "source_file": source_file,
                "row_index": idx,
            },
        )
