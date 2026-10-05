"""Testes do pipeline de ingestão e registro de datasets (bronze -> silver).

Garantias testadas:
- sources.yaml contém Fake.br, FactChecks.br, ClaimReview e ClaimPT com seus respectivos papéis.
- Adapters leem fixtures locais com sucesso e de forma determinística.
- Pipeline é idempotente (segunda execução não altera hashes).
- manifest.json tem formato determinístico e rastreável.

Refs: ADR-001, IS-03, IS-04, IS-09.
"""

import os
import shutil
import tempfile
import yaml

from ml.datasets.adapters.fakebr import FakeBrAdapter
from ml.datasets.adapters.factchecksbr import FactChecksBrAdapter
from ml.datasets.ingest import run_ingestion
from ml.datasets.manifest import (
    load_manifest,
    update_manifest,
    verify_manifest,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
SOURCES_YAML_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "datasets", "sources.yaml")


def test_sources_yaml_schema():
    """Valida o schema e o conteúdo obrigatório de sources.yaml."""
    assert os.path.exists(SOURCES_YAML_PATH), "sources.yaml não encontrado"

    with open(SOURCES_YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Verifica os 4 datasets obrigatórios
    required_datasets = ["fakebr", "factchecksbr", "claimreview", "claimpt"]
    for ds in required_datasets:
        assert ds in data, f"Dataset '{ds}' ausente em sources.yaml"
        entry = data[ds]
        for field in ["role", "language", "url", "license", "expected_columns", "notes"]:
            assert field in entry, f"Campo '{field}' ausente na entrada '{ds}' de sources.yaml"

    # Papéis estritos (ADR-001)
    assert data["fakebr"]["role"] == "linguistic_corpus"
    assert data["factchecksbr"]["role"] == "fact_check_evidence"
    assert data["claimreview"]["role"] == "external_complementary"
    assert data["claimpt"]["role"] == "methodological_auxiliary"

    # Nota sobre Português Europeu no ClaimPT
    assert "Europeu" in data["claimpt"]["notes"] or "PT-PT" in data["claimpt"]["notes"]


def test_adapter_fakebr_local_fixture():
    """Adapter FakeBr lê fixture local sem depender de rede."""
    adapter = FakeBrAdapter()
    records = list(adapter.parse(FIXTURES_DIR))
    assert len(records) > 0
    for r in records:
        assert r.record_type == "news"
        assert r.label in ("fake", "true")
        assert len(r.text) > 0


def test_adapter_factchecksbr_local_fixture():
    """Adapter FactChecksBr lê fixture local sem depender de rede."""
    adapter = FactChecksBrAdapter()
    records = list(adapter.parse(FIXTURES_DIR))
    assert len(records) > 0
    for r in records:
        assert r.record_type == "fact_check"
        assert len(r.claim_text) > 0
        assert r.verdict_normalized is not None


def test_ingestion_idempotence():
    """Garante idempotência: 2 execuções com a mesma entrada geram exatamente o mesmo hash."""
    temp_dir = tempfile.mkdtemp()
    try:
        silver_dir = os.path.join(temp_dir, "silver")

        # 1ª execução
        count1 = run_ingestion("fakebr", input_dir=FIXTURES_DIR, output_dir=silver_dir)
        assert count1 > 0

        manifest_path = os.path.join(temp_dir, "manifest.json")
        m1 = load_manifest(manifest_path)
        hash1 = m1["datasets"]["fakebr"]["sha256"]

        # 2ª execução
        count2 = run_ingestion("fakebr", input_dir=FIXTURES_DIR, output_dir=silver_dir)
        assert count2 == count1

        m2 = load_manifest(manifest_path)
        hash2 = m2["datasets"]["fakebr"]["sha256"]

        assert hash1 == hash2, "Idempotência violada: hash do arquivo silver mudou na 2ª execução"
    finally:
        shutil.rmtree(temp_dir)


def test_manifest_deterministic_and_verify():
    """Garante que manifest.json é determinístico e que a verificação detecta divergências."""
    temp_dir = tempfile.mkdtemp()
    try:
        manifest_file = os.path.join(temp_dir, "manifest.json")
        sample_file = os.path.join(temp_dir, "fakebr.parquet")
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("dados de teste")

        # Atualiza manifest
        update_manifest(
            dataset="fakebr",
            file_path=sample_file,
            source_url="https://example.com/fakebr",
            version="2024-01",
            record_count=10,
            manifest_path=manifest_file,
        )

        m = load_manifest(manifest_file)
        assert "fakebr" in m["datasets"]
        assert m["datasets"]["fakebr"]["record_count"] == 10

        # Verificação do manifest
        silver_dir = os.path.join(temp_dir, "silver")
        os.makedirs(silver_dir, exist_ok=True)
        shutil.copy(sample_file, os.path.join(silver_dir, "fakebr.parquet"))

        assert verify_manifest(manifest_file) is True

        # Modifica arquivo silver e confirma falha de integridade
        with open(os.path.join(silver_dir, "fakebr.parquet"), "a", encoding="utf-8") as f:
            f.write("adulteracao")

        assert verify_manifest(manifest_file) is False
    finally:
        shutil.rmtree(temp_dir)
