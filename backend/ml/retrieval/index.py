"""Indexação vetorial com Chroma para o pipeline EvidencIA.

Import tardio de chromadb e sentence_transformers — dentro das funções.
Executa: python -m ml.retrieval.index --collection evidencia --silver-dir backend/data/silver

Refs: ADR-001, IS-06.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Optional

logger = logging.getLogger(__name__)

# Diretório padrão de persistência do índice Chroma
DEFAULT_CHROMA_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "chroma"
)


def build_index(
    silver_dir: str,
    collection_name: str = "evidencia",
    chroma_dir: Optional[str] = None,
    model_name: Optional[str] = None,
    batch_size: int = 64,
) -> None:
    """Constrói o índice Chroma a partir dos arquivos silver.

    Args:
        silver_dir: Diretório com arquivos ``*.parquet`` ou ``*.jsonl`` do silver.
        collection_name: Nome da coleção Chroma.
        chroma_dir: Diretório de persistência do Chroma. Usa o padrão se None.
        model_name: Modelo de embedding. Usa ``DEFAULT_MODEL`` se None.
        batch_size: Tamanho do batch de indexação.

    Raises:
        ImportError: Se chromadb ou sentence_transformers não estiverem instalados.
        FileNotFoundError: Se silver_dir não existir.
    """
    # Import tardio — não falha se chromadb não estiver instalado
    try:
        import chromadb  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "chromadb não está instalado. Execute: pip install -r requirements-ml.txt"
        ) from exc

    from ml.embeddings.encoder import EmbeddingEncoder

    if not os.path.isdir(silver_dir):
        raise FileNotFoundError(f"Diretório silver não encontrado: {silver_dir!r}")

    persist_dir = chroma_dir or DEFAULT_CHROMA_DIR
    os.makedirs(persist_dir, exist_ok=True)

    encoder = EmbeddingEncoder(model_name)
    client = chromadb.PersistentClient(path=persist_dir)

    # Cria ou obtém coleção (idempotente)
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    # Processa arquivos silver
    silver_files = [
        f for f in os.listdir(silver_dir)
        if f.endswith(".parquet") or f.endswith(".jsonl")
    ]
    if not silver_files:
        logger.warning("Nenhum arquivo silver encontrado em %s", silver_dir)
        return

    total_indexed = 0
    for silver_file in sorted(silver_files):
        file_path = os.path.join(silver_dir, silver_file)
        logger.info("Indexando %s...", file_path)

        if silver_file.endswith(".parquet"):
            try:
                import pandas as pd  # type: ignore
            except ImportError as exc:
                raise ImportError("pandas não está instalado. Execute: pip install -r requirements-ml.txt") from exc
            df = pd.read_parquet(file_path)
            records = df.to_dict("records")
        else:
            import json as _json
            records = []
            with open(file_path, encoding="utf-8") as fh:
                for line in fh:
                    records.append(_json.loads(line))

        # Processa em batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            texts = []
            ids = []
            metadatas = []

            for rec in batch:
                # Usa claim_text para EvidenceRecord, text para NewsRecord
                text = rec.get("claim_text") or rec.get("text") or ""
                if not text:
                    continue
                rec_id = rec.get("evidence_id", f"unknown-{i}")
                texts.append(text)
                ids.append(rec_id)
                # Metadados filtráveis
                meta: dict = {
                    "dataset": rec.get("dataset", "unknown"),
                    "record_type": rec.get("record_type", "unknown"),
                    "record_json": json.dumps(rec, ensure_ascii=False, default=str),
                }
                if rec.get("published_at"):
                    meta["published_at"] = str(rec["published_at"])[:10]
                if rec.get("verdict_normalized"):
                    meta["verdict_normalized"] = rec["verdict_normalized"]
                metadatas.append(meta)

            if not texts:
                continue

            embeddings = encoder.encode(texts)
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )
            total_indexed += len(texts)

    logger.info("Indexação concluída: %d documentos em '%s'", total_indexed, collection_name)


def main() -> None:
    """CLI para construção do índice Chroma."""
    import argparse

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Constrói índice Chroma a partir do silver")
    parser.add_argument("--collection", default="evidencia", help="Nome da coleção Chroma")
    parser.add_argument("--silver-dir", required=True, dest="silver_dir", help="Diretório silver")
    parser.add_argument("--chroma-dir", dest="chroma_dir", default=None, help="Diretório Chroma")
    parser.add_argument("--model", default=None, help="Modelo de embedding")
    parser.add_argument("--batch-size", type=int, default=64, dest="batch_size")

    args = parser.parse_args()
    try:
        build_index(
            silver_dir=os.path.abspath(args.silver_dir),
            collection_name=args.collection,
            chroma_dir=args.chroma_dir,
            model_name=args.model,
            batch_size=args.batch_size,
        )
        print(f"[OK] Índice '{args.collection}' construído com sucesso.")
        sys.exit(0)
    except Exception as exc:
        logger.error("Erro ao construir índice: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
