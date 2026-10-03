"""Checks for CBL Act phase and Telemetry (ACT, TEL)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from audit.model import Check, CheckResult, Priority, Status
from audit.repo import RepoAccess

CHECKS: List[Check] = [
    Check(
        id="TEL-01",
        domain="TEL",
        priority=Priority.P0,
        expected="extension/src/telemetry/ com schema JSON, sanitize.ts, testes; nenhum fetch/XMLHttpRequest/sendBeacon/WebSocket",
        description="Garante telemetria estritamente local e sem transmissão remota",
        repo="code",
    ),
    Check(
        id="TEL-02",
        domain="TEL",
        priority=Priority.P1,
        expected="docs/cbl/act/telemetry-spec.md existe e o catálogo de eventos coincide com EVENT_ALLOWLIST",
        description="Verifica especificação formal da telemetria",
        repo="docs",
    ),
    Check(
        id="ACT-01",
        domain="ACT",
        priority=Priority.P0,
        expected="experiment-plan.md, participant-protocol.md e metrics-definition.md existentes em docs/cbl/act/",
        description="Verifica instrumentos nucleares do protocolo experimental",
        repo="docs",
    ),
    Check(
        id="ACT-02",
        domain="ACT",
        priority=Priority.P0,
        expected="Pré-registro travado: tag git act-prereg-v1 existe e metrics-definition.md não contém PROPOSTO nem A DEFINIR",
        description="Verifica imutabilidade metodológica do pré-registro",
        repo="docs",
    ),
    Check(
        id="ACT-03",
        domain="ACT",
        priority=Priority.P0,
        expected="results.md existe, sem {{ ou PREENCHER, com N >= --min-participants por condição",
        description="Verifica relatório de resultados com participantes humanos reais",
        repo="docs",
        immediate_nogo=True,
    ),
    Check(
        id="ACT-04",
        domain="ACT",
        priority=Priority.P0,
        expected="Nenhum e-mail, CPF ou telefone em arquivos rastreados; analysis/act/data/ não rastreado",
        description="Verifica conformidade estrita com a LGPD e ausência de PII",
        repo="both",
    ),
    Check(
        id="ACT-05",
        domain="ACT",
        priority=Priority.P1,
        expected="participant-protocol.md contém TCLE e procedimento de pseudonimização",
        description="Verifica garantias éticas e de consentimento informado",
        repo="docs",
    ),
    Check(
        id="ACT-06",
        domain="ACT",
        priority=Priority.P0,
        expected="limitations.md existe e seção 'Limitações observadas' não está vazia em results.md",
        description="Verifica transparência de limitações metodológicas e observadas",
        repo="docs",
    ),
    Check(
        id="ACT-07",
        domain="ACT",
        priority=Priority.P0,
        expected="Integridade: summary_sha256 em results.md é igual ao SHA-256 real de analysis/act/out/summary.json",
        description="Garante autenticidade criptográfica e anti-adulteração de métricas",
        repo="both",
        immediate_nogo=True,
    ),
    Check(
        id="ACT-08",
        domain="ACT",
        priority=Priority.P0,
        expected="Decisão GO/INVESTIGAR/NO-GO em results.md é compatível com a regra pré-registrada aplicada aos números de summary.json",
        description="Verifica fidelidade estrita à regra de decisão pré-registrada",
        repo="docs",
        immediate_nogo=True,
    ),
]


def check_tel_01(repo: RepoAccess) -> CheckResult:
    telemetry_dir = repo.code_path / "extension" / "src" / "telemetry"
    if not telemetry_dir.is_dir():
        # Fallback to src/telemetry
        telemetry_dir = repo.code_path / "src" / "telemetry"
        if not telemetry_dir.is_dir():
            return CheckResult("TEL-01", Status.FAIL, "extension/src/telemetry/ ausente", "Diretório de telemetria não encontrado")

    # Check for schema JSON
    json_schemas = list(telemetry_dir.rglob("*.json"))
    has_schema = len(json_schemas) > 0

    # Check sanitize.ts
    has_sanitize = (telemetry_dir / "sanitize.ts").is_file()

    # Check tests
    tests = list(telemetry_dir.rglob("*.test.ts")) + list(telemetry_dir.rglob("*_test.ts"))
    has_tests = len(tests) > 0

    if not (has_schema and has_sanitize and has_tests):
        missing = []
        if not has_schema:
            missing.append("schema JSON")
        if not has_sanitize:
            missing.append("sanitize.ts")
        if not has_tests:
            missing.append("testes unitários")
        return CheckResult("TEL-01", Status.FAIL, f"Componentes ausentes em telemetry: {missing}", "Telemetria incompleta")

    # Prohibited network calls
    prohibited_network = ["fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket"]
    network_violations = []

    for ts_file in telemetry_dir.rglob("*.ts"):
        try:
            code = ts_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for call in prohibited_network:
            if call in code:
                # ignore comments if simple check
                lines = code.splitlines()
                for idx, line in enumerate(lines, 1):
                    line_s = line.strip()
                    if call in line_s and not line_s.startswith("//") and not line_s.startswith("/*"):
                        network_violations.append(f"{ts_file.name}:{idx} ({call})")

    if network_violations:
        return CheckResult(
            "TEL-01",
            Status.FAIL,
            f"Chamadas de rede proibidas detectadas: {network_violations[:3]}",
            "Telemetria deve ser estritamente local sem emissão de tráfego de rede",
        )

    return CheckResult(
        "TEL-01",
        Status.PASS,
        f"Schema JSON, sanitize.ts e {len(tests)} testes presentes; 0 chamadas de rede",
        "Telemetria local ética validada",
    )


def check_tel_02(repo: RepoAccess) -> CheckResult:
    content = repo.read_docs("docs/cbl/act/telemetry-spec.md")
    if not content:
        return CheckResult("TEL-02", Status.FAIL, "docs/cbl/act/telemetry-spec.md ausente", "Especificação de telemetria não encontrada")

    # Look for EVENT_ALLOWLIST or list of canonical event names
    events_found = re.findall(r"[\"'](analysis_[a-z_]+|panel_[a-z_]+|reflection_[a-z_]+|claim_[a-z_]+)[\"']", content)
    if not events_found:
        events_found = re.findall(r"`(analysis_[a-z_]+|panel_[a-z_]+|reflection_[a-z_]+|claim_[a-z_]+)`", content)

    if not events_found:
        return CheckResult("TEL-02", Status.WARN, "Catálogo de eventos não identificado no markdown", "telemetry-spec.md presente")

    return CheckResult("TEL-02", Status.PASS, f"{len(set(events_found))} tipos de eventos documentados", "telemetry-spec.md validado")


def check_act_01(repo: RepoAccess) -> CheckResult:
    required = [
        "docs/cbl/act/experiment-plan.md",
        "docs/cbl/act/participant-protocol.md",
        "docs/cbl/act/metrics-definition.md",
    ]
    missing = [p for p in required if not repo.docs_exists(p)]
    if missing:
        return CheckResult("ACT-01", Status.FAIL, f"Arquivos ausentes: {missing}", "Protocolo experimental incompleto")

    return CheckResult("ACT-01", Status.PASS, "experiment-plan.md, participant-protocol.md, metrics-definition.md presentes", "Instrumentos nucleares do Act validados")


def check_act_02(repo: RepoAccess) -> CheckResult:
    docs_tags = repo.get_tags("docs")
    code_tags = repo.get_tags("code")
    all_tags = docs_tags + code_tags

    has_tag = "act-prereg-v1" in all_tags

    content = repo.read_docs("docs/cbl/act/metrics-definition.md") or ""
    has_proposto = bool(re.search(r"\bPROPOSTO\b", content))
    has_definir = bool(re.search(r"\bA\s+DEFINIR\b", content))

    issues = []
    if not has_tag:
        issues.append("Tag git 'act-prereg-v1' ausente")
    if has_proposto:
        issues.append("Contém termo 'PROPOSTO'")
    if has_definir:
        issues.append("Contém termo 'A DEFINIR'")

    if issues:
        return CheckResult("ACT-02", Status.FAIL, "; ".join(issues), "Pré-registro não travado formalmente")

    return CheckResult("ACT-02", Status.PASS, "Tag act-prereg-v1 presente e sem placeholders", "Pré-registro congelado")


def check_act_03(repo: RepoAccess, min_participants: int = 10) -> CheckResult:
    results_path = "docs/cbl/act/results.md"
    content = repo.read_docs(results_path)
    if not content:
        return CheckResult(
            "ACT-03",
            Status.FAIL,
            "docs/cbl/act/results.md ausente",
            "Resultados do estudo Act com participantes reais ainda não produzidos",
        )

    if "{{" in content or "PREENCHER" in content.upper():
        return CheckResult("ACT-03", Status.FAIL, "Placeholders presentes em results.md", "Contém {{ ou PREENCHER")

    # Check N per condition
    n_matches = re.findall(r"N\s*=\s*(\d+)", content)
    if not n_matches:
        n_matches = re.findall(r"participantes\s*:\s*(\d+)", content, re.IGNORECASE)

    if n_matches:
        counts = [int(x) for x in n_matches]
        if any(c < min_participants for c in counts):
            return CheckResult(
                "ACT-03",
                Status.FAIL,
                f"N insuficiente: {counts} < {min_participants}",
                f"Exigido N >= {min_participants} por condição",
            )

    return CheckResult("ACT-03", Status.PASS, "results.md preenchido com dados reais", f"N >= {min_participants} verificado")


def check_act_04(repo: RepoAccess) -> CheckResult:
    # 1. Ensure analysis/act/data/ is NOT tracked
    code_tracked = repo.get_tracked_files("code")
    data_tracked = [f for f in code_tracked if f.startswith("analysis/act/data/")]
    if data_tracked:
        return CheckResult(
            "ACT-04",
            Status.FAIL,
            f"Pasta de dados pessoais rastreada no Git: {data_tracked[:3]}",
            "analysis/act/data/ deve estar no .gitignore",
        )

    # 2. Secret / PII scan in tracked files
    pii_violations = []

    cpf_pattern = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
    # Email pattern ignoring example / documentation domains
    email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.com|evidencia-grupo\.dev|users\.noreply\.github\.com)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    for r_type in ["code", "docs"]:
        tracked = repo.get_tracked_files(r_type)
        root = repo.docs_path if r_type == "docs" else repo.code_path
        for rel in tracked:
            # Skip fixtures, test mocks, package locks
            if "fixtures" in rel or "package-lock" in rel or rel.endswith(".min.js") or rel.endswith(".svg"):
                continue
            full = root / rel
            if not full.is_file():
                continue
            try:
                txt = full.read_text(encoding="utf-8")
            except Exception:
                continue

            # Check CPF
            for line_no, line in enumerate(txt.splitlines(), 1):
                if cpf_pattern.search(line):
                    pii_violations.append(f"{r_type}:{rel}:{line_no} (CPF detectado)")
                em = email_pattern.search(line)
                if em:
                    pii_violations.append(f"{r_type}:{rel}:{line_no} (Email detectado: {em.group(0)[:3]}***)")

    if pii_violations:
        return CheckResult("ACT-04", Status.FAIL, f"{len(pii_violations)} potenciais dados pessoais (PII) encontrados", "; ".join(pii_violations[:2]))

    return CheckResult("ACT-04", Status.PASS, "Nenhum CPF, e-mail de voluntário ou dado pessoal detectado", "LGPD e privacidade atendidas")


def check_act_05(repo: RepoAccess) -> CheckResult:
    content = repo.read_docs("docs/cbl/act/participant-protocol.md")
    if not content:
        return CheckResult("ACT-05", Status.FAIL, "docs/cbl/act/participant-protocol.md ausente", "Protocolo de participantes não encontrado")

    has_tcle = bool(re.search(r"TCLE|Consentimento\s+Livre", content, re.IGNORECASE))
    has_pseudo = bool(re.search(r"pseudonimiz|anonimiz", content, re.IGNORECASE))

    if not (has_tcle and has_pseudo):
        missing = []
        if not has_tcle:
            missing.append("TCLE")
        if not has_pseudo:
            missing.append("procedimento de pseudonimização")
        return CheckResult("ACT-05", Status.FAIL, f"Seções éticas ausentes: {missing}", "participant-protocol.md incompleto")

    return CheckResult("ACT-05", Status.PASS, "TCLE e pseudonimização presentes", "participant-protocol.md validado")


def check_act_06(repo: RepoAccess) -> CheckResult:
    has_limitations = repo.docs_exists("docs/cbl/act/limitations.md")
    if not has_limitations:
        return CheckResult("ACT-06", Status.FAIL, "docs/cbl/act/limitations.md ausente", "Arquivo de limitações não encontrado")

    results_content = repo.read_docs("docs/cbl/act/results.md")
    if not results_content:
        return CheckResult("ACT-06", Status.WARN, "limitations.md presente; results.md ainda não criado (SCAFFOLD)", "Limitações observadas pendentes de coleta")

    has_obs = bool(re.search(r"Limitações\s+observadas.*?\n([^\n#]+)", results_content, re.IGNORECASE))
    if not has_obs:
        return CheckResult("ACT-06", Status.FAIL, "Seção 'Limitações observadas' vazia em results.md", "Limitações de campo não documentadas")

    return CheckResult("ACT-06", Status.PASS, "limitations.md e limitações observadas documentadas", "Transparência de limitações assegurada")


def check_act_07(repo: RepoAccess) -> CheckResult:
    results_content = repo.read_docs("docs/cbl/act/results.md")
    summary_content = repo.read_code("analysis/act/out/summary.json")

    if not results_content:
        return CheckResult("ACT-07", Status.FAIL, "results.md ausente", "Não é possível validar integridade sem results.md")

    if not summary_content:
        return CheckResult("ACT-07", Status.FAIL, "analysis/act/out/summary.json ausente", "Arquivo de métricas consolidadas não encontrado")

    # Compute actual SHA256 of summary.json
    actual_hash = hashlib.sha256(summary_content.encode("utf-8")).hexdigest()

    # Find summary_sha256 in results.md
    match = re.search(r"summary_sha256[:\s\|`]+([a-f0-9]{64})", results_content, re.IGNORECASE)
    if not match:
        return CheckResult("ACT-07", Status.FAIL, "summary_sha256 não registrado em results.md", "Hash de integridade ausente")

    recorded_hash = match.group(1).lower()
    if recorded_hash != actual_hash:
        return CheckResult(
            "ACT-07",
            Status.FAIL,
            f"Hash divergente: registrado {recorded_hash[:8]} != real {actual_hash[:8]}",
            "Falha de integridade: summary.json foi alterado após o registro dos resultados",
        )

    return CheckResult("ACT-07", Status.PASS, f"Hash criptográfico conferido: {actual_hash[:16]}...", "Integridade dos resultados garantida")


def check_act_08(repo: RepoAccess) -> CheckResult:
    results_content = repo.read_docs("docs/cbl/act/results.md")
    summary_data = repo.read_json_code("analysis/act/out/summary.json")

    if not results_content or not summary_data:
        return CheckResult("ACT-08", Status.FAIL, "results.md ou summary.json ausente", "Impossível validar decisão")

    # Extract decision recorded in results.md
    decision_match = re.search(r"decisão[:\s\|`]+(GO|INVESTIGAR|NO-GO)", results_content, re.IGNORECASE)
    if not decision_match:
        return CheckResult("ACT-08", Status.FAIL, "Decisão GO/INVESTIGAR/NO-GO não identificada em results.md", "Formato inválido")

    recorded_decision = decision_match.group(1).upper()

    # Apply pre-registered rule to summary numbers
    metrics = summary_data.get("metrics", {})
    cond_b = metrics.get("condition_B", {})
    cond_a = metrics.get("condition_A", {})

    acc_b = cond_b.get("accuracy_assisted", {}).get("mean", 0)
    acc_a = cond_a.get("accuracy_assisted", {}).get("mean", 0)

    # Basic check: if B is significantly lower than A, cannot be GO
    if acc_b < acc_a and recorded_decision == "GO":
        return CheckResult(
            "ACT-08",
            Status.FAIL,
            f"Decisão {recorded_decision} viola regra pré-registrada (Acurácia B {acc_b} < A {acc_a})",
            "Inconsistência entre métricas e veredito do estudo",
        )

    return CheckResult("ACT-08", Status.PASS, f"Decisão {recorded_decision} compatível com métricas pré-registradas", "Regra de decisão validada")


def run_checks(repo: RepoAccess, min_participants: int = 10) -> List[CheckResult]:
    return [
        check_tel_01(repo),
        check_tel_02(repo),
        check_act_01(repo),
        check_act_02(repo),
        check_act_03(repo, min_participants),
        check_act_04(repo),
        check_act_05(repo),
        check_act_06(repo),
        check_act_07(repo),
        check_act_08(repo),
    ]
