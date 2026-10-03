"""Tests for CLI entrypoint and exit codes."""

import json
from pathlib import Path
import subprocess
import sys

import pytest


def test_cli_missing_required_args():
    cmd = [sys.executable, "scripts/audit_project_completeness.py"]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).resolve().parent.parent.parent.parent))
    assert res.returncode == 2
    assert "the following arguments are required" in res.stderr.lower()


def test_cli_nonexistent_repo():
    cmd = [
        sys.executable,
        "scripts/audit_project_completeness.py",
        "--docs-repo", "nonexistent_docs_path_xyz",
        "--code-repo", ".",
        "--output", "test_report.md",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path(__file__).resolve().parent.parent.parent.parent))
    assert res.returncode == 2
    assert "Erro de acesso aos repositórios" in res.stderr


def test_cli_executes_on_mock_repos(make_repos, tmp_path: Path):
    docs_dir, code_dir, _ = make_repos(full_passing=True)
    report_out = tmp_path / "report_out.md"
    json_out = tmp_path / "report_out.json"

    cmd = [
        sys.executable,
        "scripts/audit_project_completeness.py",
        "--docs-repo", str(docs_dir),
        "--code-repo", str(code_dir),
        "--output", str(report_out),
        "--json", str(json_out),
        "--date", "2026-10-02",
        "--fase", "SCAFFOLD",
    ]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent.parent.parent),
    )

    # In mock repo without git tags initialized, ACT-02 (P0) fails, so exit code must be 20 (NO-GO)
    assert res.returncode == 20
    assert "AUDITORIA DE COMPLETUDE DO PROJETO EVIDENCIA" in res.stdout
    assert "Veredito: NO-GO" in res.stdout

    # Verify report was generated
    assert report_out.is_file()
    first_line = report_out.read_text(encoding="utf-8").splitlines()[0]
    assert first_line == "<!-- CBL_COMPLETENESS_REPORT -->"

    # Verify json was generated
    assert json_out.is_file()
    data = json.loads(json_out.read_text(encoding="utf-8"))
    assert data["verdict"] == "NO-GO"
    assert data["exit_code"] == 20
