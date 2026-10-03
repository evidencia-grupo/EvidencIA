"""Tests for Data Engineering and Architecture checks (DATA, ARC, UX)."""

import json
from audit import checks_data_arch
from audit.model import Status


def test_data_01_sources_yaml_roles_and_notes(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    # Check PASS initially
    res = checks_data_arch.check_data_01(repo)
    assert res.status == Status.PASS

    # Break ClaimPT role
    sources_file = code_dir / "backend" / "ml" / "datasets" / "sources.yaml"
    sources_file.write_text("fakebr:\n  role: linguistic_corpus\nfactchecksbr:\n  role: fact_check_evidence\nclaimpt:\n  role: invalid_role\n  notes: PT-EU", encoding="utf-8")
    res = checks_data_arch.check_data_01(repo)
    assert res.status == Status.FAIL
    assert "claimpt != methodological_auxiliary" in res.found

    # Break PT-EU note
    sources_file.write_text("fakebr:\n  role: linguistic_corpus\nfactchecksbr:\n  role: fact_check_evidence\nclaimpt:\n  role: methodological_auxiliary\n  notes: None", encoding="utf-8")
    res = checks_data_arch.check_data_01(repo)
    assert res.status == Status.FAIL
    assert "PT-EU" in res.found


def test_data_02_manifest_hashes(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_data_arch.check_data_02(repo)
    assert res.status == Status.PASS

    # Invalidate sha256 (not 64 hex)
    manifest_file = code_dir / "backend" / "data" / "manifest.json"
    manifest_file.write_text('{"datasets": {"factchecks": {"sha256": "invalid_short_hash"}}}', encoding="utf-8")
    res = checks_data_arch.check_data_02(repo)
    assert res.status == Status.FAIL
    assert "sem sha256 válido" in res.found


def test_data_03_backend_data_hygiene(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_data_arch.check_data_03(repo)
    assert res.status == Status.PASS

    # Add disallowed file
    bad_file = code_dir / "backend" / "data" / "raw_corpus.csv"
    bad_file.write_text("col1,col2\n1,2", encoding="utf-8")
    res = checks_data_arch.check_data_03(repo)
    assert res.status == Status.FAIL
    assert "Arquivos não permitidos" in res.found


def test_arc_01_llm_provider_ast(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_data_arch.check_arc_01(repo)
    assert res.status == Status.PASS

    # Remove generate_reflection method
    prov_file = code_dir / "backend" / "app" / "services" / "providers" / "base.py"
    prov_file.write_text("class LLMProvider:\n    async def extract_claims(self, transcript: str): pass\n", encoding="utf-8")
    res = checks_data_arch.check_arc_01(repo)
    assert res.status == Status.FAIL
    assert "generate_reflection" in res.found


def test_arc_03_silent_mock_fallback_xfail(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_data_arch.check_arc_03(repo)
    assert res.status == Status.PASS

    # Mark with xfail
    test_file = code_dir / "backend" / "tests" / "test_no_silent_mock_fallback.py"
    test_file.write_text("import pytest\n@pytest.mark.xfail(reason='debt')\ndef test_fallback(): pass", encoding="utf-8")
    res = checks_data_arch.check_arc_03(repo)
    assert res.status == Status.FAIL
    assert "ainda está marcado com @pytest.mark.xfail" in res.found


def test_arc_04_score_and_gauge_detection(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    # SearchHit.score is present in full_passing, and it should PASS
    res = checks_data_arch.check_arc_04(repo)
    assert res.status == Status.PASS

    # 1. Add reliabilityScore to api-schema.json
    schema_file = code_dir / "shared" / "schemas" / "api-schema.json"
    schema_file.write_text('{"properties": {"reliabilityScore": {"type": "number"}}}', encoding="utf-8")
    res = checks_data_arch.check_arc_04(repo)
    assert res.status == Status.FAIL
    assert "resíduos de score/gauge detectados" in res.found

    # Reset schema
    schema_file.write_text('{"properties": {"claims": {}}}', encoding="utf-8")

    # 2. Add residual gauge component in extension/src
    gauge_comp = code_dir / "extension" / "src" / "panel" / "components" / "Gauge.tsx"
    gauge_comp.write_text("export const Gauge = () => <div/>;", encoding="utf-8")
    res = checks_data_arch.check_arc_04(repo)
    assert res.status == Status.FAIL
    assert "gauge" in res.details.lower()
    gauge_comp.unlink()

    # 3. Add 'veracidade' in UI text
    card_file = code_dir / "extension" / "src" / "panel" / "components" / "EvidenceCard.tsx"
    card_file.write_text("export const EvidenceCard = () => <span>Nível de veracidade</span>;", encoding="utf-8")
    res = checks_data_arch.check_arc_04(repo)
    assert res.status == Status.FAIL
    assert "veracidade" in res.details.lower()


def test_ux_01_components(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_data_arch.check_ux_01(repo)
    assert res.status == Status.PASS

    # Remove EvidenceCard.tsx
    card_file = code_dir / "extension" / "src" / "panel" / "components" / "EvidenceCard.tsx"
    card_file.unlink()
    res = checks_data_arch.check_ux_01(repo)
    assert res.status == Status.FAIL
    assert "EvidenceCard.tsx" in res.found
