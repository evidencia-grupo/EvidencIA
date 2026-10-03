"""Tests for Security and Performance checks (SEC, PERF)."""

from audit import checks_security_perf
from audit.model import Status


def test_sec_01_no_env_and_secret_scanning(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_security_perf.check_sec_01(repo)
    assert res.status == Status.PASS

    # 1. Tracked .env violation
    env_file = code_dir / ".env"
    env_file.write_text("API_KEY=foo", encoding="utf-8")
    res = checks_security_perf.check_sec_01(repo)
    assert res.status == Status.FAIL
    assert ".env" in res.found
    env_file.unlink()

    # 2. Planted secret detection & anti-leak masking test
    planted_secret = "AIzaSy" + "A" * 33
    vuln_file = code_dir / "backend" / "app" / "config.py"
    vuln_file.write_text(f'GEMINI_KEY = "{planted_secret}"\n', encoding="utf-8")

    res = checks_security_perf.check_sec_01(repo)
    assert res.status == Status.FAIL
    assert "segredo(s) detectado(s)" in res.found
    assert "Google API Key detectada" in res.details
    # STRICT SAFETY INVARIANT: The planted secret string itself MUST NEVER appear in found or details!
    assert planted_secret not in res.found
    assert planted_secret not in res.details


def test_sec_02_gitignore_coverage(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_security_perf.check_sec_02(repo)
    assert res.status == Status.PASS

    # Incomplete .gitignore
    gitignore = code_dir / ".gitignore"
    gitignore.write_text("*.pyc\n__pycache__/\n", encoding="utf-8")
    res = checks_security_perf.check_sec_02(repo)
    assert res.status == Status.FAIL
    assert "Regras ausentes" in res.found


def test_sec_03_workflows_exist(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_security_perf.check_sec_03(repo)
    assert res.status == Status.PASS

    # Remove security.yml
    (code_dir / ".github" / "workflows" / "security.yml").unlink()
    res = checks_security_perf.check_sec_03(repo)
    assert res.status == Status.FAIL
    assert "security.yml" in res.found
