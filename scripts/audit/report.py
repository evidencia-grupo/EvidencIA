"""Deterministic markdown and JSON report generation for the Completeness Audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from audit.model import AuditSummary, Check, CheckResult, Priority, Status, Verdict

MAGIC_FIRST_LINE = "<!-- CBL_COMPLETENESS_REPORT -->"


def render_markdown(
    summary: AuditSummary,
    results: List[CheckResult],
    checks_by_id: Dict[str, Check],
    docs_sha: str,
    code_sha: str,
    date_str: str,
    fase: str = "SCAFFOLD",
) -> str:
    """Renders the full deterministic markdown report."""
    lines: List[str] = [MAGIC_FIRST_LINE]

    lines.append(f"# Relatório de Auditoria de Completude do Projeto — EvidencIA")
    lines.append("")
    lines.append(f"> **Data da Auditoria:** {date_str}  ")
    lines.append(f"> **Fase Auditada:** `{fase.upper()}`  ")
    lines.append(f"> **Versão Documentação:** `@`{docs_sha}  ")
    lines.append(f"> **Versão Código:** `@`{code_sha}  ")
    lines.append(f"> **Veredito Geral:** **`{summary.verdict.value}`**  ")
    if summary.immediate_nogo_triggered:
        lines.append(f"> **Flag de Bloqueio Imediato:** `ATIVADA` (condição fatal de integridade violada)  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. Resumo por Domínio
    lines.append("## 1. Resumo Quantitativo por Domínio")
    lines.append("")
    lines.append("| Domínio | PASS | FAIL | WARN | SKIP | Total |")
    lines.append("|:---|:---:|:---:|:---:|:---:|:---:|")

    sorted_domains = sorted(summary.domain_counts.keys())
    for d in sorted_domains:
        counts = summary.domain_counts[d]
        total = sum(counts.values())
        lines.append(
            f"| **{d}** | {counts['PASS']} | {counts['FAIL']} | {counts['WARN']} | {counts['SKIP']} | {total} |"
        )

    # Total row
    tot = summary.overall_counts
    total_checks = sum(tot.values())
    lines.append(
        f"| **TOTAL GERAL** | **{tot['PASS']}** | **{tot['FAIL']}** | **{tot['WARN']}** | **{tot['SKIP']}** | **{total_checks}** |"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # 2. Tabela Completa de Checks
    lines.append("## 2. Tabela Detalhada de Checks")
    lines.append("")
    lines.append("| Domínio | ID | Evidência Esperada | Encontrada | Status | Classe | Detalhe |")
    lines.append("|:---|:---|:---|:---|:---:|:---:|:---|")

    # Deterministic sort by check ID
    sorted_results = sorted(results, key=lambda r: r.check_id)
    for r in sorted_results:
        chk = checks_by_id.get(r.check_id)
        domain = chk.domain if chk else "OTHER"
        priority = chk.priority.value if chk else "P1"
        expected = chk.expected if chk else ""

        # Escape pipes
        clean_exp = expected.replace("|", "/")
        clean_found = r.found.replace("|", "/")
        clean_det = r.details.replace("|", "/")

        status_badge = f"**{r.status.value}**" if r.status in (Status.FAIL, Status.WARN) else r.status.value

        lines.append(
            f"| {domain} | **{r.check_id}** | {clean_exp} | {clean_found} | {status_badge} | {priority} | {clean_det} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # 3. Lista de Bloqueadores (P0)
    lines.append("## 3. Bloqueadores (P0 não-PASS)")
    lines.append("")
    if summary.blockers:
        lines.append(f"Foram identificados **{len(summary.blockers)}** bloqueadores críticos P0:")
        lines.append("")
        for b in sorted(summary.blockers, key=lambda x: x.check_id):
            chk = checks_by_id.get(b.check_id)
            desc = chk.description if chk else ""
            lines.append(f"- **[{b.check_id}]** (`{b.status.value}`): {b.found}")
            lines.append(f"  - *Critério:* {desc}")
            if b.details:
                lines.append(f"  - *Detalhe:* {b.details}")
    else:
        lines.append("Nenhum bloqueador P0 pendente. Todos os critérios bloqueadores foram atendidos com sucesso.")

    lines.append("")
    lines.append("---")
    lines.append("")

    # 4. Lista de Dívidas Técnicas (P1/P2)
    lines.append("## 4. Dívidas Técnicas e Alertas (P1/P2)")
    lines.append("")
    if summary.debts:
        lines.append(f"Foram registradas **{len(summary.debts)}** dívidas técnicas/alertas:")
        lines.append("")
        for d in sorted(summary.debts, key=lambda x: x.check_id):
            chk = checks_by_id.get(d.check_id)
            prio = chk.priority.value if chk else "P1"
            lines.append(f"- **[{d.check_id}]** ({prio} - `{d.status.value}`): {d.found}")
            if d.details:
                lines.append(f"  - *Detalhe:* {d.details}")
    else:
        lines.append("Nenhuma dívida técnica registrada nos critérios P1 e P2.")

    lines.append("")
    lines.append("---")
    lines.append("")

    # 5. Checks Não Executados (SKIP)
    lines.append("## 5. Verificações Não Executadas (SKIP)")
    lines.append("")
    if summary.skips:
        lines.append(f"Foram pulados **{len(summary.skips)}** checks condicionais:")
        lines.append("")
        for s in sorted(summary.skips, key=lambda x: x.check_id):
            lines.append(f"- **[{s.check_id}]**: {s.found} (Como destravar: {s.details})")
    else:
        lines.append("Todos os checks do catálogo foram executados.")

    lines.append("")
    lines.append("---")
    lines.append("")

    # 6. Regra de Veredito
    lines.append("## 6. Regra de Veredito Aplicada")
    lines.append("")
    lines.append("```text")
    lines.append("NO-GO          se qualquer critério P0 falhar ou for pulado (fail-closed)")
    lines.append("GO WITH DEBT   se todos os critérios P0 passarem, restando apenas P1/P2 com dívida registrada")
    lines.append("GO             se todos os critérios tiverem evidência verificável")
    lines.append("NO-GO IMEDIATO se: GQs ausentes · EDA ausente · Act sem usuários · hash divergente · dado pessoal")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def write_report_file(output_path: Path | str, content: str) -> None:
    """Safely writes the report to output_path adhering to non-destruction rules."""
    out_file = Path(output_path).resolve()

    # Security check: never write inside a .git directory
    if ".git" in out_file.parts:
        raise PermissionError(f"Escrita proibida dentro de diretório .git: {out_file}")

    # Security check: if file exists, it must start with the magic header line
    if out_file.exists():
        try:
            first_line = out_file.read_text(encoding="utf-8").splitlines()[0].strip()
        except Exception:
            first_line = ""
        if first_line != MAGIC_FIRST_LINE:
            raise PermissionError(
                f"Recusa de sobrescrita segura: {out_file} já existe e sua primeira linha não é '{MAGIC_FIRST_LINE}'."
            )

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(content, encoding="utf-8")


def write_json_report(json_path: Path | str, summary: AuditSummary, results: List[CheckResult], metadata: Dict[str, Any]) -> None:
    """Safely writes a machine-readable JSON summary of the audit."""
    target = Path(json_path).resolve()
    if ".git" in target.parts:
        raise PermissionError(f"Escrita proibida dentro de diretório .git: {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": metadata,
        "verdict": summary.verdict.value,
        "exit_code": summary.exit_code,
        "immediate_nogo_triggered": summary.immediate_nogo_triggered,
        "immediate_nogo_reasons": summary.immediate_nogo_reasons,
        "overall_counts": summary.overall_counts,
        "domain_counts": summary.domain_counts,
        "blockers": [b.to_dict() for b in summary.blockers],
        "debts": [d.to_dict() for d in summary.debts],
        "skips": [s.to_dict() for s in summary.skips],
        "results": [r.to_dict() for r in sorted(results, key=lambda x: x.check_id)],
    }
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
