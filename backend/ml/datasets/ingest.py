"""CLI de ingestão do pipeline de dados EvidencIA.

Executa o pipeline bronze → silver para um dataset específico.
Idempotente: 2ª execução gera os mesmos hashes se os dados de entrada não mudaram.

Usage:
    python -m ml.datasets.ingest --source fakebr --input-dir ./data/raw/fakebr
    python -m ml.datasets.ingest --source factchecksbr --input-dir ./data/raw/factchecksbr
    python -m ml.datasets.ingest --source fakebr --input-dir ./data/raw/fakebr --dry-run

Refs: ADR-001, IS-04.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

logger = logging.getLogger(__name__)


def _setup_logging(level: str = "INFO") -> None:
    """Configura logging básico para o CLI."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def _get_silver_path(output_dir: str, source_name: str) -> str:
    """Retorna o caminho do arquivo silver para um dataset."""
    return os.path.join(output_dir, f"{source_name}.parquet")


def _get_sources_config() -> dict:
    """Carrega o sources.yaml como dicionário."""
    try:
        import yaml  # type: ignore
    except ImportError:
        # Fallback mínimo se pyyaml não estiver instalado
        return {}

    sources_yaml = os.path.join(os.path.dirname(__file__), "sources.yaml")
    if not os.path.exists(sources_yaml):
        return {}
    with open(sources_yaml, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def run_ingestion(
    source: str,
    input_dir: str,
    output_dir: str,
    dry_run: bool = False,
) -> int:
    """Executa o pipeline de ingestão para um dataset.

    Etapas:
    1. Valida configuração em sources.yaml
    2. Carrega adapter correspondente
    3. Parseia registros do input_dir (bronze)
    4. Normaliza registros
    5. Valida registros (gera relatório)
    6. Serializa silver (salvo em output_dir/<source>.parquet)
    7. Atualiza manifest.json

    Args:
        source: Nome do dataset (ex.: 'fakebr', 'factchecksbr').
        input_dir: Diretório com dados brutos (bronze).
        output_dir: Diretório de destino para silver.
        dry_run: Se True, executa até validação sem gravar nada.

    Returns:
        Número de registros ingeridos com sucesso.
    """
    from ml.datasets.adapters.base import get_adapter
    from ml.datasets.normalize import normalize_evidence_record, normalize_news_record
    from ml.datasets.validate import validate_records
    from ml.schemas.evidence import EvidenceRecord, NewsRecord

    logger.info("=== Ingestão: %s | input=%s | dry_run=%s ===", source, input_dir, dry_run)

    # 1. Valida sources.yaml
    sources_config = _get_sources_config()
    if sources_config and source not in sources_config:
        logger.warning("Dataset '%s' não encontrado em sources.yaml. Continuando...", source)

    # 2. Carrega adapter
    adapter = get_adapter(source)
    logger.info("Adapter carregado: %s", adapter.__class__.__name__)

    # 3. Parseia registros
    logger.info("Parseando registros de %s...", input_dir)
    raw_records = list(adapter.parse(input_dir))
    logger.info("Registros parseados: %d", len(raw_records))

    # 4. Normaliza
    normalized = []
    for rec in raw_records:
        if isinstance(rec, EvidenceRecord):
            normalized.append(normalize_evidence_record(rec))
        elif isinstance(rec, NewsRecord):
            normalized.append(normalize_news_record(rec))
        else:
            normalized.append(rec)

    # 5. Valida
    valid_records, report = validate_records(normalized)
    logger.info(report.summary())
    if report.issues:
        logger.warning("Problemas encontrados: %d ocorrências", len(report.issues))

    if dry_run:
        logger.info("[DRY RUN] %d registros válidos — nada foi gravado.", len(valid_records))
        return len(valid_records)

    if not valid_records:
        logger.warning("Nenhum registro válido para gravar em %s", output_dir)
        return 0

    # 6. Serializa silver (JSON Lines como intermediário até ter pandas/pyarrow disponível)
    os.makedirs(output_dir, exist_ok=True)
    silver_path = _get_silver_path(output_dir, source)

    try:
        import pandas as pd  # type: ignore

        records_dicts = [r.model_dump(mode="json") for r in valid_records]
        df = pd.DataFrame(records_dicts)
        df.to_parquet(silver_path, index=False)
        logger.info("Silver gravado: %s (%d registros)", silver_path, len(df))
    except ImportError:
        # Fallback: JSON Lines (sem pandas/pyarrow)
        silver_path = silver_path.replace(".parquet", ".jsonl")
        with open(silver_path, "w", encoding="utf-8") as fh:
            for rec in valid_records:
                fh.write(rec.model_dump_json() + "\n")
        logger.info("Silver gravado (JSONL): %s (%d registros)", silver_path, len(valid_records))

    # 7. Atualiza manifest
    from ml.datasets.manifest import update_manifest

    sources_config_entry = _get_sources_config().get(source, {})
    source_url = sources_config_entry.get("url", "https://unknown")

    manifest_path = os.path.join(os.path.dirname(output_dir), "manifest.json")
    update_manifest(
        dataset=source,
        file_path=silver_path,
        source_url=source_url,
        version="2024-01",  # TODO(verify-format): extrair versão real
        record_count=len(valid_records),
        manifest_path=manifest_path,
    )

    return len(valid_records)


def main() -> None:
    """Entry point do CLI de ingestão."""
    _setup_logging()

    parser = argparse.ArgumentParser(
        description="Pipeline de ingestão de datasets EvidencIA (bronze → silver)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m ml.datasets.ingest --source fakebr --input-dir ./data/raw/fakebr
  python -m ml.datasets.ingest --source factchecksbr --input-dir ./data/raw/factchecksbr
  python -m ml.datasets.ingest --source fakebr --input-dir ./data/raw/fakebr --dry-run
""",
    )
    parser.add_argument(
        "--source",
        required=True,
        choices=["fakebr", "factchecksbr", "claimreview"],
        help="Dataset a ingerir",
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        dest="input_dir",
        help="Diretório com os dados brutos (bronze)",
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=None,
        help="Diretório de saída para o silver (padrão: backend/data/silver/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa sem gravar nada no disco",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nível de log",
    )

    args = parser.parse_args()
    _setup_logging(args.log_level)

    output_dir = args.output_dir or os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "silver"
    )
    output_dir = os.path.abspath(output_dir)

    try:
        count = run_ingestion(
            source=args.source,
            input_dir=os.path.abspath(args.input_dir),
            output_dir=output_dir,
            dry_run=args.dry_run,
        )
        print(f"✅ Ingestão concluída: {count} registros válidos" + (" [DRY RUN]" if args.dry_run else ""))
        sys.exit(0)
    except FileNotFoundError as exc:
        logger.error("Diretório não encontrado: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.error("Erro na ingestão: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
