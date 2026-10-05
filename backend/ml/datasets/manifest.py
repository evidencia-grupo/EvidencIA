"""Módulo de manifest de dados para o pipeline EvidencIA.

Gera e verifica ``manifest.json`` com SHA-256, versão, data e contagem
por dataset. Deterministicamente ordenado (chaves alfabéticas).

CLI: ``python -m ml.datasets.manifest verify``

Refs: ADR-001, IS-09.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Caminho padrão do manifest (relativo ao backend/)
DEFAULT_MANIFEST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "manifest.json"
)


def compute_file_sha256(file_path: str) -> str:
    """Computa SHA-256 de um arquivo.

    Args:
        file_path: Caminho absoluto ou relativo ao arquivo.

    Returns:
        String no formato ``sha256:<hex64>``.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def load_manifest(manifest_path: str | None = None) -> dict:
    """Carrega o manifest.json existente.

    Args:
        manifest_path: Caminho para o manifest. Usa o padrão se None.

    Returns:
        Dicionário com o conteúdo do manifest ou ``{"datasets": {}}`` se não existir.
    """
    path = manifest_path or DEFAULT_MANIFEST_PATH
    if not os.path.exists(path):
        return {"datasets": {}}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_manifest(data: dict, manifest_path: str | None = None) -> None:
    """Persiste o manifest.json de forma determinística (chaves ordenadas).

    Args:
        data: Dicionário a serializar.
        manifest_path: Caminho de destino. Usa o padrão se None.
    """
    path = manifest_path or DEFAULT_MANIFEST_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


def update_manifest(
    dataset: str,
    file_path: str,
    source_url: str,
    version: str,
    record_count: int,
    manifest_path: str | None = None,
) -> dict:
    """Atualiza a entrada de um dataset no manifest.

    Idempotente: recalcula o SHA-256 e atualiza a entrada existente.

    Args:
        dataset: Nome do dataset (ex.: 'fakebr').
        file_path: Caminho para o arquivo silver.
        source_url: URL oficial do dataset.
        version: Versão do dataset (ex.: '2024-01').
        record_count: Número de registros no silver.
        manifest_path: Caminho do manifest. Usa o padrão se None.

    Returns:
        Dicionário atualizado do manifest.
    """
    manifest = load_manifest(manifest_path)
    sha256 = compute_file_sha256(file_path)
    manifest["datasets"][dataset] = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "record_count": record_count,
        "sha256": sha256,
        "source_url": source_url,
        "version": version,
    }
    save_manifest(manifest, manifest_path)
    logger.info("Manifest atualizado: %s | %s | %d registros", dataset, sha256, record_count)
    return manifest


def verify_manifest(manifest_path: str | None = None) -> bool:
    """Verifica a integridade dos arquivos silver via SHA-256 do manifest.

    Args:
        manifest_path: Caminho do manifest. Usa o padrão se None.

    Returns:
        ``True`` se todos os hashes conferem, ``False`` se algum diverge ou arquivo ausente.
    """
    manifest = load_manifest(manifest_path)
    datasets = manifest.get("datasets", {})
    if not datasets:
        logger.warning("Manifest vazio ou sem datasets registrados.")
        return True  # Sem dados = sem violação

    all_ok = True
    manifest_dir = os.path.dirname(os.path.abspath(manifest_path or DEFAULT_MANIFEST_PATH))
    silver_dir = os.path.join(manifest_dir, "silver")

    for name, meta in sorted(datasets.items()):
        expected_hash = meta.get("sha256", "")
        # Procura o arquivo silver correspondente
        silver_file = os.path.join(silver_dir, f"{name}.parquet")
        if not os.path.exists(silver_file):
            logger.error("Arquivo silver ausente: %s", silver_file)
            all_ok = False
            continue

        actual_hash = compute_file_sha256(silver_file)
        if actual_hash != expected_hash:
            logger.error(
                "Hash diverge para %s: esperado %s, encontrado %s",
                name,
                expected_hash,
                actual_hash,
            )
            all_ok = False
        else:
            logger.info("Hash OK: %s", name)

    return all_ok


def main() -> None:
    """CLI do módulo manifest.

    Usage: python -m ml.datasets.manifest [verify]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Gerenciador de manifest de dados EvidencIA")
    subparsers = parser.add_subparsers(dest="command")

    verify_parser = subparsers.add_parser("verify", help="Verifica integridade dos hashes no manifest")
    verify_parser.add_argument("--manifest", default=None, help="Caminho para o manifest.json")

    args = parser.parse_args()

    if args.command == "verify":
        ok = verify_manifest(args.manifest)
        if ok:
            print("[OK] Todos os hashes do manifest conferem.")
            sys.exit(0)
        else:
            print("[ERRO] Divergência de hash detectada. Verifique os logs.")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
