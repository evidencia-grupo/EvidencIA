"""Checks for CBL methodology: Engage (ENG), ADR, EDA, and Reflect & Share (REF)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from audit.model import Check, CheckResult, Priority, Status
from audit.repo import RepoAccess

CHECKS: List[Check] = [
    Check(
        id="ENG-01",
        domain="CBL",
        priority=Priority.P0,
        expected="docs/visao/guiding-questions.md com exatamente GQ01–GQ12 e 8 seções obrigatórias",
        description="Verifica completude do artefato central de Engage",
        repo="docs",
        immediate_nogo=True,
    ),
    Check(
        id="ENG-02",
        domain="CBL",
        priority=Priority.P0,
        expected="essential-question-alignment.md existente citando a Essential Question",
        description="Verifica alinhamento explícito à Essential Question",
        repo="docs",
    ),
    Check(
        id="ENG-03",
        domain="CBL",
        priority=Priority.P1,
        expected="decision-log.md referencia ADR-001",
        description="Verifica rastreabilidade de decisões ao ADR-001",
        repo="docs",
    ),
    Check(
        id="ADR-01",
        domain="CBL",
        priority=Priority.P0,
        expected="ADR com Status Aceito/Accepted mencionando fim do score, HU11 no MVP, Evidence-Only e proibição de mock em produção",
        description="Verifica formalização da decisão arquitetural evidence-first",
        repo="docs",
    ),
    Check(
        id="EDA-01",
        domain="CBL",
        priority=Priority.P0,
        expected="notebooks/eda_datasets.ipynb existe, JSON válido e contém 17 seções (0–16)",
        description="Verifica estrutura e cobertura das 17 seções do notebook de EDA",
        repo="code",
        immediate_nogo=True,
    ),
    Check(
        id="EDA-02",
        domain="CBL",
        priority=Priority.P0,
        expected="notebook EXECUTADO: células de código com execution_count não nulo, sem erro e sem NotImplementedError",
        description="Verifica execução real completa e congelamento de saídas da EDA",
        repo="code",
    ),
    Check(
        id="EDA-03",
        domain="CBL",
        priority=Priority.P0,
        expected="docs/investigate/eda-results.md e eda-decisions.md (formato Achado→Evidência→Impacto→Decisão >= 1 linha); dataset-card.md",
        description="Verifica documentação e decisões derivadas da análise exploratória",
        repo="docs",
    ),
    Check(
        id="EDA-04",
        domain="CBL",
        priority=Priority.P0,
        expected="eda-results.md traz valores numéricos para Recall@1, Recall@3, Recall@5, MRR e nDCG@5",
        description="Verifica métricas objetivas de Information Retrieval da investigação",
        repo="docs",
    ),
    Check(
        id="REF-01",
        domain="CBL",
        priority=Priority.P0,
        expected="reflection.md, showcase-script.md, demo-script.md existentes; lessons-learned.md e research-portfolio.md (P1)",
        description="Verifica existência dos artefatos essenciais de Reflect & Share",
        repo="docs",
    ),
    Check(
        id="REF-02",
        domain="CBL",
        priority=Priority.P0,
        expected="showcase-script.md contém segmentos na ordem Challenge → EQ → GQs → EDA → ADR → Evidence UI → Act",
        description="Verifica ordem narrativa e cadeia pedagógica estrita do showcase",
        repo="docs",
    ),
    Check(
        id="REF-03",
        domain="CBL",
        priority=Priority.P0,
        expected="Anti-fabricação: todo parágrafo com número, %, Recall, MRR ou p90 tem marcador [EV: apontando caminho existente; sem PENDENTE em FINALIZE",
        description="Verifica integridade factual e ancoragem obrigatória de dados",
        repo="docs",
    ),
]


def check_eng_01(repo: RepoAccess) -> CheckResult:
    content = repo.read_docs("docs/visao/guiding-questions.md")
    if not content:
        return CheckResult("ENG-01", Status.FAIL, "Arquivo ausente", "docs/visao/guiding-questions.md não encontrado")

    # Check GQs (GQ01 to GQ12)
    found_gqs = set(re.findall(r"\bGQ(\d{2})\b", content))
    expected_gqs = {f"{i:02d}" for i in range(1, 13)}
    missing_gqs = expected_gqs - found_gqs
    if missing_gqs:
        return CheckResult(
            "ENG-01",
            Status.FAIL,
            f"Faltam GQs: {sorted(missing_gqs)}",
            f"Encontradas {len(found_gqs)} de 12 GQs",
        )

    # Check 8 required sections
    required_sections = [
        r"Essential\s+Question",
        r"Challenge",
        r"Guiding\s+Questions",
        r"Respostas\s+Sintetizadas",
        r"Evidências\s+Utilizadas",
        r"Decisões\s+Derivadas",
        r"Hipóteses\s+Ainda\s+Não\s+Validadas",
        r"Relação\s+Engage\s*→\s*Investigate|Relação\s+Engage\s*->\s*Investigate",
    ]
    missing_sections = []
    for pat in required_sections:
        if not re.search(pat, content, re.IGNORECASE):
            missing_sections.append(pat)

    if missing_sections:
        return CheckResult(
            "ENG-01",
            Status.FAIL,
            f"Faltam {len(missing_sections)} seções obrigatórias",
            f"Seções não encontradas: {missing_sections}",
        )

    return CheckResult("ENG-01", Status.PASS, "12 GQs e 8 seções presentes", "docs/visao/guiding-questions.md íntegro")


def check_eng_02(repo: RepoAccess) -> CheckResult:
    candidates = [
        "docs/visao/essential-question-alignment.md",
        "docs/visao/essential-question.md",
    ]
    found_path = None
    content = None
    for p in candidates:
        c = repo.read_docs(p)
        if c:
            found_path = p
            content = c
            break

    if not content or not found_path:
        return CheckResult("ENG-02", Status.FAIL, "Arquivo ausente", "essential-question-alignment.md não encontrado")

    # Check citation of Essential Question
    eq_keywords = ["pensamento crítico", "substituir seu pensamento", "avaliar a confiabilidade"]
    has_eq = any(kw.lower() in content.lower() for kw in eq_keywords)
    if not has_eq:
        return CheckResult(
            "ENG-02",
            Status.FAIL,
            "Essential Question não citada",
            f"{found_path} não contém os termos essenciais da EQ",
        )

    return CheckResult("ENG-02", Status.PASS, f"Encontrado em {found_path}", "Cita Essential Question explicitamente")


def check_eng_03(repo: RepoAccess) -> CheckResult:
    content = repo.read_docs("docs/visao/decision-log.md")
    if not content:
        return CheckResult("ENG-03", Status.FAIL, "Arquivo ausente", "docs/visao/decision-log.md não encontrado")

    if "ADR-001" in content:
        return CheckResult("ENG-03", Status.PASS, "Referência a ADR-001 presente", "decision-log.md referencia ADR-001")

    return CheckResult("ENG-03", Status.WARN, "Sem referência a ADR-001", "decision-log.md não cita ADR-001")


def check_adr_01(repo: RepoAccess) -> CheckResult:
    # Look for ADR files in docs/adr or docs/tecnico/decisoes
    candidate_paths = [
        "docs/adr/ADR-001-evidence-first.md",
        "docs/adr/ADR-001-evidence-first-architecture.md",
        "docs/adr/ADR-001-manifest-v3.md",
        "docs/tecnico/decisoes/ADR-006-evidence-first-architecture.md",
        "docs/tecnico/decisoes/ADR-001-manifest-v3.md",
    ]
    # Also discover any ADR in docs/adr or docs/tecnico/decisoes
    discovered: List[str] = []
    for base in ["docs/adr", "docs/tecnico/decisoes"]:
        dir_path = repo.docs_path / base
        if dir_path.is_dir():
            for f in dir_path.glob("ADR-*.md"):
                discovered.append(f"{base}/{f.name}".replace("\\", "/"))

    all_candidates = list(dict.fromkeys(candidate_paths + discovered))

    accepted_adrs = []
    for p in all_candidates:
        c = repo.read_docs(p)
        if not c:
            continue
        c_lower = c.lower()
        is_accepted = bool(re.search(r"status.*(aceito|accepted)", c_lower))
        has_score = "fim do score" in c_lower or "score" in c_lower and "remov" in c_lower
        has_hu11 = "hu11" in c_lower
        has_evidence_only = "evidence-only" in c_lower or "evidence_only" in c_lower
        has_mock_guard = "mock em produção" in c_lower or "mockinproductionerror" in c_lower or "proibição de mock" in c_lower or "anti-mock" in c_lower

        if is_accepted and has_score and has_hu11 and has_evidence_only and has_mock_guard:
            return CheckResult(
                "ADR-01",
                Status.PASS,
                f"Encontrado em {p}",
                "Status Aceito; cobre fim do score, HU11, Evidence-Only e proibição de mock",
            )
        elif is_accepted and (has_score or has_hu11 or has_evidence_only):
            accepted_adrs.append(p)

    if accepted_adrs:
        return CheckResult(
            "ADR-01",
            Status.FAIL,
            f"ADRs parciais: {accepted_adrs}",
            "ADR encontrado mas faltam requisitos (fim do score, HU11, Evidence-Only ou mock em produção)",
        )

    return CheckResult("ADR-01", Status.FAIL, "Nenhum ADR compatível encontrado", "Procurado em docs/adr/ e docs/tecnico/decisoes/")


def check_eda_01(repo: RepoAccess) -> CheckResult:
    rel_path = "notebooks/eda_datasets.ipynb"
    content = repo.read_code(rel_path)
    if not content:
        return CheckResult("EDA-01", Status.FAIL, "Arquivo ausente", f"{rel_path} não encontrado no código")

    try:
        nb = json.loads(content)
    except Exception as e:
        return CheckResult("EDA-01", Status.FAIL, "JSON inválido", f"Erro de parsing: {e}")

    cells = nb.get("cells", [])
    if not cells:
        return CheckResult("EDA-01", Status.FAIL, "Notebook vazio", "Nenhuma célula encontrada")

    # Check for 17 sections (0 to 16)
    found_sections = set()
    full_text = ""
    for c in cells:
        source = "".join(c.get("source", []))
        full_text += "\n" + source

    for i in range(17):
        # Look for section patterns like "Seção 0", "## 1.", "## 1 ", "1. Dataset Inventory", etc.
        patterns = [
            rf"(?:Seção|Secao|Section)\s+{i}\b",
            rf"##\s+{i}\b",
            rf"#\s+{i}\.",
        ]
        if any(re.search(pat, full_text, re.IGNORECASE) for pat in patterns):
            found_sections.add(i)

    missing = set(range(17)) - found_sections
    if missing:
        return CheckResult(
            "EDA-01",
            Status.FAIL,
            f"Faltam {len(missing)} seções: {sorted(missing)}",
            f"Encontradas seções {sorted(found_sections)} de 0 a 16",
        )

    return CheckResult("EDA-01", Status.PASS, "17 seções (0–16) encontradas", "Notebook estruturado com sucesso")


def check_eda_02(repo: RepoAccess) -> CheckResult:
    rel_path = "notebooks/eda_datasets.ipynb"
    content = repo.read_code(rel_path)
    if not content:
        return CheckResult("EDA-02", Status.FAIL, "Arquivo ausente", "notebooks/eda_datasets.ipynb não encontrado")

    try:
        nb = json.loads(content)
    except Exception:
        return CheckResult("EDA-02", Status.FAIL, "JSON inválido", "Falha ao abrir notebook")

    code_cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]
    if not code_cells:
        return CheckResult("EDA-02", Status.FAIL, "Sem células de código", "Nenhuma célula de código encontrada")

    unexecuted = 0
    errors = 0
    not_implemented = 0

    for c in code_cells:
        if c.get("execution_count") is None:
            unexecuted += 1

        outputs = c.get("outputs", [])
        for out in outputs:
            if out.get("output_type") == "error":
                errors += 1
                ename = out.get("ename", "")
                if "NotImplementedError" in ename:
                    not_implemented += 1
            # Check text outputs for NotImplementedError traceback
            for line in out.get("traceback", []):
                if "NotImplementedError" in line:
                    not_implemented += 1

    if unexecuted > 0:
        return CheckResult(
            "EDA-02",
            Status.FAIL,
            f"{unexecuted} células não executadas (execution_count: null)",
            f"Total de células de código: {len(code_cells)}",
        )
    if errors > 0:
        return CheckResult(
            "EDA-02",
            Status.FAIL,
            f"{errors} saídas com erro ({not_implemented} NotImplementedError)",
            "Notebook executado apresentou falhas de execução",
        )

    return CheckResult(
        "EDA-02",
        Status.PASS,
        f"Todas as {len(code_cells)} células executadas sem erros",
        "Notebook completamente executado",
    )


def check_eda_03(repo: RepoAccess) -> CheckResult:
    results_path = "docs/investigate/eda-results.md"
    decisions_path = "docs/investigate/eda-decisions.md"

    has_results = repo.docs_exists(results_path)
    has_decisions = repo.docs_exists(decisions_path)

    if not has_results or not has_decisions:
        missing = []
        if not has_results:
            missing.append(results_path)
        if not has_decisions:
            missing.append(decisions_path)
        return CheckResult("EDA-03", Status.FAIL, f"Arquivos ausentes: {missing}", "Relatórios de EDA não encontrados")

    decisions_content = repo.read_docs(decisions_path) or ""
    # Check decision format: Achado -> Evidência -> Impacto -> Decisão
    has_format = bool(
        re.search(r"Achado.*Evidência.*Impacto.*Decisão", decisions_content, re.IGNORECASE | re.DOTALL)
        or re.search(r"Achado.*->.*Evidência.*->.*Decisão", decisions_content, re.IGNORECASE)
    )

    if not has_format:
        return CheckResult(
            "EDA-03",
            Status.FAIL,
            "Formato de decisão ausente em eda-decisions.md",
            "Exigido formato: Achado → Evidência → Impacto → Decisão com >= 1 linha",
        )

    return CheckResult("EDA-03", Status.PASS, "eda-results.md e eda-decisions.md válidos", "Achados e decisões registrados")


def check_eda_04(repo: RepoAccess) -> CheckResult:
    content = repo.read_docs("docs/investigate/eda-results.md")
    if not content:
        return CheckResult("EDA-04", Status.FAIL, "docs/investigate/eda-results.md ausente", "Relatório de métricas IR não encontrado")

    required_metrics = ["Recall@1", "Recall@3", "Recall@5", "MRR", "nDCG@5"]
    missing_metrics = []

    for m in required_metrics:
        # Check metric followed by number (e.g., Recall@1: 0.82 or | Recall@1 | 0.82 |)
        escaped = re.escape(m)
        if not re.search(rf"{escaped}.*?[\:\s\|]+\s*(\d+(?:\.\d+)?)", content, re.IGNORECASE):
            missing_metrics.append(m)

    if missing_metrics:
        return CheckResult(
            "EDA-04",
            Status.FAIL,
            f"Faltam valores numéricos para: {missing_metrics}",
            "eda-results.md deve conter valores numéricos para todas as 5 métricas de IR",
        )

    return CheckResult("EDA-04", Status.PASS, "5 métricas numéricas de IR presentes", "Recall@1/3/5, MRR e nDCG@5 registrados")


def check_ref_01(repo: RepoAccess) -> CheckResult:
    required_p0 = [
        "docs/cbl/reflect-share/reflection.md",
        "docs/cbl/reflect-share/showcase-script.md",
        "docs/cbl/reflect-share/demo-script.md",
    ]
    p1_files = [
        "docs/cbl/reflect-share/lessons-learned.md",
        "docs/cbl/reflect-share/research-portfolio.md",
    ]

    missing_p0 = [p for p in required_p0 if not repo.docs_exists(p)]
    missing_p1 = [p for p in p1_files if not repo.docs_exists(p)]

    if missing_p0:
        return CheckResult("REF-01", Status.FAIL, f"Faltam artefatos P0: {missing_p0}", "Documentos obrigatórios ausentes")

    if missing_p1:
        return CheckResult("REF-01", Status.WARN, f"Faltam artefatos P1: {missing_p1}", "Artefatos complementares pendentes")

    return CheckResult("REF-01", Status.PASS, "Todos os 5 artefatos de Reflect & Share presentes", "reflection, showcase, demo, lessons, portfolio")


def check_ref_02(repo: RepoAccess) -> CheckResult:
    content = repo.read_docs("docs/cbl/reflect-share/showcase-script.md")
    if not content:
        return CheckResult("REF-02", Status.FAIL, "showcase-script.md ausente", "Roteiro de apresentação não encontrado")

    # Check order of segments
    segment_patterns = [
        r"Challenge",
        r"Essential\s+Question",
        r"Guiding\s+Questions",
        r"EDA",
        r"ADR",
        r"Evidence\s+UI|UI",
        r"Act|Validação\s+Act",
    ]

    last_pos = -1
    for seg in segment_patterns:
        match = re.search(seg, content, re.IGNORECASE)
        if not match:
            return CheckResult("REF-02", Status.FAIL, f"Segmento ausente: {seg}", "showcase-script.md não contém todos os 7 segmentos")
        if match.start() <= last_pos:
            return CheckResult(
                "REF-02",
                Status.FAIL,
                f"Ordem incorreta no segmento: {seg}",
                "Ordem esperada: Challenge → EQ → GQs → EDA → ADR → Evidence UI → Act",
            )
        last_pos = match.start()

    return CheckResult("REF-02", Status.PASS, "Ordem de segmentos validada", "Challenge → EQ → GQs → EDA → ADR → Evidence UI → Act")


def check_ref_03(repo: RepoAccess, fase: str = "SCAFFOLD") -> CheckResult:
    doc_paths = [
        "docs/cbl/reflect-share/reflection.md",
        "docs/cbl/reflect-share/showcase-script.md",
    ]

    violations = []
    for p in doc_paths:
        content = repo.read_docs(p)
        if not content:
            continue

        paragraphs = content.split("\n\n")
        for idx, para in enumerate(paragraphs, 1):
            para_clean = para.strip()
            if not para_clean or para_clean.startswith("#") or para_clean.startswith("|"):
                continue

            # Check if paragraph contains quantitative claim
            has_metric = bool(
                re.search(r"\b\d+%", para_clean)
                or re.search(r"\bRecall@\d\b", para_clean, re.IGNORECASE)
                or re.search(r"\bMRR\b", para_clean)
                or re.search(r"\bp90\b", para_clean, re.IGNORECASE)
                or re.search(r"\b\d+\s*(?:ms|segundos|s)\b", para_clean, re.IGNORECASE)
            )

            if has_metric:
                # Must contain [EV: <repo>:<path>#<anchor>@<sha>]
                ev_matches = re.findall(r"\[EV:\s*([^:]+):([^#@]+)(?:#([^@]+))?@([a-f0-9]+)\]", para_clean)
                if not ev_matches:
                    violations.append(f"{p} pág/parágrafo #{idx}: afirmação com métrica sem marcador [EV:]")
                else:
                    for repo_name, target_path, anchor, sha in ev_matches:
                        target_clean = target_path.strip()
                        # Check target file existence
                        exists = False
                        if "doc" in repo_name.lower():
                            exists = repo.docs_exists(target_clean)
                        else:
                            exists = repo.code_exists(target_clean)
                        if not exists:
                            violations.append(f"{p} #{idx}: marcador aponta para arquivo inexistente: {target_clean}")

        if fase.upper() == "FINALIZE":
            if "PENDENTE" in content:
                violations.append(f"{p}: bloco PENDENTE remanescente na fase FINALIZE")

    if violations:
        return CheckResult("REF-03", Status.FAIL, f"{len(violations)} violações de anti-fabricação", "; ".join(violations[:3]))

    return CheckResult("REF-03", Status.PASS, "Todas as métricas possuem marcador [EV:] válido", "Nenhuma fabricação detectada")


def run_checks(repo: RepoAccess, fase: str = "SCAFFOLD") -> List[CheckResult]:
    return [
        check_eng_01(repo),
        check_eng_02(repo),
        check_eng_03(repo),
        check_adr_01(repo),
        check_eda_01(repo),
        check_eda_02(repo),
        check_eda_03(repo),
        check_eda_04(repo),
        check_ref_01(repo),
        check_ref_02(repo),
        check_ref_03(repo, fase),
    ]
