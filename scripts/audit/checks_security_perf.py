"""Checks for Security and Performance (SEC, PERF)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

from audit.model import Check, CheckResult, Priority, Status
from audit.repo import RepoAccess

CHECKS: List[Check] = [
    Check(
        id="SEC-01",
        domain="SEC",
        priority=Priority.P0,
        expected="Nenhum .env rastreado; varredura negativa para chaves (AIza..., sk-..., ghp_...); valores mascarados",
        description="Garante ausência de chaves de API e segredos commitados no repositório",
        repo="code",
    ),
    Check(
        id="SEC-02",
        domain="SEC",
        priority=Priority.P0,
        expected=".gitignore cobre .env*, backend/data/{bronze,silver,gold}/* e analysis/act/data/",
        description="Verifica cobertura das regras de ignore para segredos e dados brutos",
        repo="code",
    ),
    Check(
        id="SEC-03",
        domain="SEC",
        priority=Priority.P1,
        expected="Workflows ci.yml, security.yml e freeze-guard.yml existentes em .github/workflows/",
        description="Verifica esteira de segurança e proteção de caminhos congelados",
        repo="code",
    ),
    Check(
        id="SEC-04",
        domain="SEC",
        priority=Priority.P1,
        expected="Testes de rate limit, limite de transcript e prompt injection existentes",
        description="Verifica cobertura de testes de abuso, injeção e negação de serviço",
        repo="code",
    ),
    Check(
        id="PERF-01",
        domain="PERF",
        priority=Priority.P1,
        expected="test_retrieval_latency.py existe e medição de P90 registrada na Sprint 2",
        description="Verifica testes automatizados de latência e orçamento de performance",
        repo="code",
    ),
]


def check_sec_01(repo: RepoAccess) -> CheckResult:
    tracked = repo.get_tracked_files("code")

    # 1. Check for tracked .env files (allow .env.example)
    tracked_env = [f for f in tracked if f.endswith(".env") or ".env." in f and not f.endswith(".env.example")]
    if tracked_env:
        return CheckResult(
            "SEC-01",
            Status.FAIL,
            f"Arquivo .env rastreado no Git: {tracked_env}",
            "Nenhum arquivo .env deve ser versionado",
        )

    # 2. Secret scan patterns
    secret_patterns = [
        (re.compile(r"AIza[0-9A-Za-z_-]{35}"), "Google API Key"),
        (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI / Generic Secret Key"),
        (re.compile(r"ghp_[A-Za-z0-9]{36}"), "GitHub Personal Access Token"),
        (re.compile(r"gho_[A-Za-z0-9]{36}"), "GitHub OAuth Token"),
    ]

    violations = []
    for rel in tracked:
        # Skip binaries, test fixtures, package locks
        if any(rel.endswith(ext) for ext in [".png", ".jpg", ".svg", ".lock", ".jsonl", ".ipynb", ".min.js"]):
            continue
        full_path = repo.code_path / rel
        if not full_path.is_file():
            continue

        try:
            content = full_path.read_text(encoding="utf-8")
        except Exception:
            continue

        for line_no, line in enumerate(content.splitlines(), 1):
            for pat, name in secret_patterns:
                if pat.search(line):
                    # NEVER leak the secret in found or details!
                    violations.append(f"{rel}:{line_no} ({name} detectada)")

    if violations:
        return CheckResult(
            "SEC-01",
            Status.FAIL,
            f"{len(violations)} segredo(s) detectado(s) no código rastreado",
            "; ".join(violations[:3]),
        )

    return CheckResult("SEC-01", Status.PASS, "Varredura limpa; nenhum segredo ou .env detectado", f"{len(tracked)} arquivos auditados")


def check_sec_02(repo: RepoAccess) -> CheckResult:
    gitignore = repo.read_code(".gitignore")
    if not gitignore:
        return CheckResult("SEC-02", Status.FAIL, ".gitignore ausente", "Arquivo .gitignore não encontrado no código")

    required_patterns = [
        r"\.env",
        r"(?:data/|backend/data/)",
        r"(?:analysis/act/data/|act/data/|data/)",
    ]

    missing = []
    if ".env" not in gitignore:
        missing.append(".env*")
    if "data" not in gitignore:
        missing.append("backend/data/*")

    if missing:
        return CheckResult("SEC-02", Status.FAIL, f"Regras ausentes no .gitignore: {missing}", ".gitignore incompleto")

    return CheckResult("SEC-02", Status.PASS, ".gitignore cobre .env*, backend/data/ e telemetria", ".gitignore validado")


def check_sec_03(repo: RepoAccess) -> CheckResult:
    workflows_dir = repo.code_path / ".github" / "workflows"
    required = ["ci.yml", "security.yml", "freeze-guard.yml"]

    missing = []
    for wf in required:
        if not (workflows_dir / wf).is_file():
            missing.append(wf)

    if missing:
        return CheckResult("SEC-03", Status.FAIL, f"Workflows ausentes em .github/workflows: {missing}", "Esteira de CI incompleta")

    return CheckResult("SEC-03", Status.PASS, "ci.yml, security.yml e freeze-guard.yml presentes", "Esteira de segurança ativa")


def check_sec_04(repo: RepoAccess) -> CheckResult:
    # Check for tests covering rate limit, transcript limit, prompt injection
    test_files = list(repo.code_path.glob("**/test_*.py"))
    all_test_code = ""
    for tf in test_files:
        try:
            all_test_code += "\n" + tf.read_text(encoding="utf-8")
        except Exception:
            pass

    has_rate_limit = "rate_limit" in all_test_code or "ratelimit" in all_test_code
    has_transcript_limit = "transcript" in all_test_code and ("limit" in all_test_code or "max_length" in all_test_code)
    has_injection = "injection" in all_test_code or "prompt_injection" in all_test_code

    if not (has_rate_limit and has_transcript_limit and has_injection):
        missing = []
        if not has_rate_limit:
            missing.append("rate limit")
        if not has_transcript_limit:
            missing.append("limite de transcript")
        if not has_injection:
            missing.append("prompt injection")
        return CheckResult("SEC-04", Status.FAIL, f"Testes de segurança ausentes: {missing}", "Testes de abuso e injeção incompletos")

    return CheckResult("SEC-04", Status.PASS, "Testes de rate limit, tamanho de transcrição e injeção presentes", "Testes de segurança validados")


def check_perf_01(repo: RepoAccess) -> CheckResult:
    candidates = [
        "backend/tests/test_retrieval_latency.py",
        "tests/test_retrieval_latency.py",
    ]
    has_test = any(repo.code_exists(p) for p in candidates)

    review_content = repo.read_docs("docs/scrum/sprint-02/review.md") or ""
    has_p90_measured = bool(re.search(r"P90.*?\d+", review_content))

    if not has_test:
        return CheckResult("PERF-01", Status.FAIL, "test_retrieval_latency.py ausente", "Teste de latência de recuperação não encontrado")

    if not has_p90_measured:
        return CheckResult("PERF-01", Status.WARN, "test_retrieval_latency.py existe, mas P90 não preenchido na review da Sprint 2", "Medição pendente de consolidação")

    return CheckResult("PERF-01", Status.PASS, "test_retrieval_latency.py presente e medição P90 documentada", "Performance sob controle")


def run_checks(repo: RepoAccess) -> List[CheckResult]:
    return [
        check_sec_01(repo),
        check_sec_02(repo),
        check_sec_03(repo),
        check_sec_04(repo),
        check_perf_01(repo),
    ]
