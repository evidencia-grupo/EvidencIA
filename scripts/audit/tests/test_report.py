"""Tests for deterministic markdown and JSON reporting."""

import json
from pathlib import Path
import pytest

from audit.model import AuditSummary, Check, CheckResult, Priority, Status, Verdict
from audit.report import (
    MAGIC_FIRST_LINE,
    render_markdown,
    write_json_report,
    write_report_file,
)


@pytest.fixture
def sample_audit_data():
    checks = {
        "ENG-01": Check("ENG-01", "CBL", Priority.P0, "12 GQs", "GQ check", "docs"),
        "TEL-01": Check("TEL-01", "TEL", Priority.P0, "local only", "No remote telemetria", "code"),
        "SCR-05": Check("SCR-05", "SCR", Priority.P2, "ceremonies.md", "Ritos Scrum", "docs"),
    }
    results = [
        CheckResult("ENG-01", Status.PASS, "12 GQs presentes", "Verificado em guiding-questions.md"),
        CheckResult("TEL-01", Status.PASS, "0 chamadas de rede", "Sanitize validado"),
        CheckResult("SCR-05", Status.FAIL, "ceremonies.md ausente", "Documentação incompleta"),
    ]
    summary = AuditSummary(
        verdict=Verdict.GO_WITH_DEBT,
        overall_counts={"PASS": 2, "FAIL": 1, "WARN": 0, "SKIP": 0},
        domain_counts={
            "CBL": {"PASS": 1, "FAIL": 0, "WARN": 0, "SKIP": 0},
            "TEL": {"PASS": 1, "FAIL": 0, "WARN": 0, "SKIP": 0},
            "SCR": {"PASS": 0, "FAIL": 1, "WARN": 0, "SKIP": 0},
        },
        blockers=[],
        debts=[results[2]],
        skips=[],
        exit_code=10,
        immediate_nogo_triggered=False,
        immediate_nogo_reasons=[],
    )
    return checks, results, summary


def test_render_markdown_determinism(sample_audit_data):
    checks, results, summary = sample_audit_data
    md1 = render_markdown(
        summary=summary,
        results=results,
        checks_by_id=checks,
        docs_sha="1234567",
        code_sha="abcdef0",
        date_str="2026-10-02",
        fase="SCAFFOLD",
    )
    md2 = render_markdown(
        summary=summary,
        results=results,
        checks_by_id=checks,
        docs_sha="1234567",
        code_sha="abcdef0",
        date_str="2026-10-02",
        fase="SCAFFOLD",
    )
    # Byte-for-byte exact equality
    assert md1 == md2
    assert md1.startswith(MAGIC_FIRST_LINE)
    assert "GO WITH DEBT" in md1
    assert "SCR-05" in md1


def test_write_report_file_rejects_git_path(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    target = git_dir / "report.md"

    with pytest.raises(PermissionError) as exc:
        write_report_file(target, f"{MAGIC_FIRST_LINE}\nContent")
    assert "Escrita proibida dentro de diretório .git" in str(exc.value)


def test_write_report_file_rejects_unmarked_file_overwrite(tmp_path: Path):
    target = tmp_path / "existing_doc.md"
    target.write_text("# Important existing doc\nDo not overwrite!", encoding="utf-8")

    with pytest.raises(PermissionError) as exc:
        write_report_file(target, f"{MAGIC_FIRST_LINE}\nNew report")
    assert "Recusa de sobrescrita segura" in str(exc.value)


def test_write_report_file_allows_marked_file_overwrite(tmp_path: Path):
    target = tmp_path / "CBL_COMPLETENESS_REPORT.md"
    target.write_text(f"{MAGIC_FIRST_LINE}\nOld report content", encoding="utf-8")

    new_content = f"{MAGIC_FIRST_LINE}\nUpdated report content"
    write_report_file(target, new_content)
    assert target.read_text(encoding="utf-8") == new_content


def test_write_json_report(tmp_path: Path, sample_audit_data):
    checks, results, summary = sample_audit_data
    target = tmp_path / "out.json"
    metadata = {"date": "2026-10-02", "fase": "SCAFFOLD"}

    write_json_report(target, summary, results, metadata)
    assert target.is_file()

    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["verdict"] == "GO WITH DEBT"
    assert data["exit_code"] == 10
    assert len(data["results"]) == 3
