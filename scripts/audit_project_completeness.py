#!/usr/bin/env python3
"""CLI entrypoint for Project Completeness Audit (EvidencIA & Documentation).

Usage:
  python scripts/audit_project_completeness.py \\
    --docs-repo ../documentation --code-repo . \\
    --output ../documentation/docs/cbl/reflect-share/CBL_COMPLETENESS_REPORT.md \\
    [--json out.json] [--run-tests] [--check-github] [--min-participants 10] [--date YYYY-MM-DD] [--fase SCAFFOLD|FINALIZE]
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import Dict, List

# Ensure scripts directory is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from audit import checks_act_telemetry, checks_cbl, checks_data_arch, checks_scrum_trace, checks_security_perf
    from audit.model import Check, CheckResult, calculate_verdict
    from audit.report import render_markdown, write_json_report, write_report_file
    from audit.repo import RepoAccess
except ImportError as e:
    sys.stderr.write(f"Erro ao importar módulos de auditoria: {e}\n")
    sys.exit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auditoria automatizada fail-closed de completude do projeto EvidencIA e documentação CBL.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--docs-repo",
        type=str,
        required=True,
        help="Caminho para o repositório de documentação.",
    )
    parser.add_argument(
        "--code-repo",
        type=str,
        default=".",
        help="Caminho para o repositório de código EvidencIA.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Caminho do arquivo markdown de saída para o relatório de auditoria.",
    )
    parser.add_argument(
        "--json",
        type=str,
        default=None,
        help="Caminho opcional para exportar o relatório consolidado em JSON.",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        default=False,
        help="Executa suites de testes automatizados nos checks dependentes de execução.",
    )
    parser.add_argument(
        "--check-github",
        action="store_true",
        default=False,
        help="Consulta histórico de PRs e issues via API/CLI do GitHub (requer conectividade).",
    )
    parser.add_argument(
        "--min-participants",
        type=int,
        default=10,
        help="Número mínimo de participantes por condição exigido no Act.",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Data fixa da auditoria no formato YYYY-MM-DD para saídas determinísticas.",
    )
    parser.add_argument(
        "--fase",
        type=str,
        choices=["SCAFFOLD", "FINALIZE"],
        default="SCAFFOLD",
        help="Fase da execução: SCAFFOLD (esperado NO-GO baseline) ou FINALIZE (exige evidências reais).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # 1. Initialize Read-Only Repo Access
    try:
        repo = RepoAccess(docs_repo=args.docs_repo, code_repo=args.code_repo)
    except Exception as e:
        sys.stderr.write(f"Erro de acesso aos repositórios: {e}\n")
        return 2

    # 2. Collect Checks Definition
    all_checks: List[Check] = (
        checks_cbl.CHECKS
        + checks_data_arch.CHECKS
        + checks_act_telemetry.CHECKS
        + checks_scrum_trace.CHECKS
        + checks_security_perf.CHECKS
    )
    checks_by_id: Dict[str, Check] = {c.id: c for c in all_checks}

    # 3. Execute Checks
    results: List[CheckResult] = []
    try:
        results.extend(checks_cbl.run_checks(repo, fase=args.fase))
        results.extend(checks_data_arch.run_checks(repo, run_tests=args.run_tests))
        results.extend(checks_act_telemetry.run_checks(repo, min_participants=args.min_participants))
        results.extend(checks_scrum_trace.run_checks(repo, check_github=args.check_github))
        results.extend(checks_security_perf.run_checks(repo))
    except Exception as e:
        sys.stderr.write(f"Falha inesperada durante a execução dos checks: {e}\n")
        return 2

    # 4. Calculate Fail-Closed Verdict
    summary = calculate_verdict(results, checks_by_id)

    # 5. Metadata and Date
    date_str = args.date or datetime.date.today().isoformat()
    docs_sha = repo.get_commit_sha("docs")
    code_sha = repo.get_commit_sha("code")

    metadata = {
        "date": date_str,
        "fase": args.fase,
        "docs_repo": str(repo.docs_path),
        "code_repo": str(repo.code_path),
        "docs_sha": docs_sha,
        "code_sha": code_sha,
        "run_tests": args.run_tests,
        "check_github": args.check_github,
        "min_participants": args.min_participants,
    }

    # 6. Render and Write Markdown Report
    try:
        md_content = render_markdown(
            summary=summary,
            results=results,
            checks_by_id=checks_by_id,
            docs_sha=docs_sha,
            code_sha=code_sha,
            date_str=date_str,
            fase=args.fase,
        )
        write_report_file(args.output, md_content)
    except PermissionError as pe:
        sys.stderr.write(f"Violação de segurança na gravação do relatório: {pe}\n")
        return 2
    except Exception as e:
        sys.stderr.write(f"Erro ao gravar relatório de saída: {e}\n")
        return 2

    # 7. Write Optional JSON
    if args.json:
        try:
            write_json_report(args.json, summary, results, metadata)
        except Exception as e:
            sys.stderr.write(f"Erro ao gravar relatório JSON: {e}\n")
            return 2

    # 8. Print Console Summary
    sys.stdout.write(f"==========================================================\n")
    sys.stdout.write(f"AUDITORIA DE COMPLETUDE DO PROJETO EVIDENCIA\n")
    sys.stdout.write(f"Data: {date_str} | Fase: {args.fase} | Veredito: {summary.verdict.value}\n")
    sys.stdout.write(f"Total: {sum(summary.overall_counts.values())} checks | ")
    sys.stdout.write(f"PASS: {summary.overall_counts['PASS']} | FAIL: {summary.overall_counts['FAIL']} | ")
    sys.stdout.write(f"WARN: {summary.overall_counts['WARN']} | SKIP: {summary.overall_counts['SKIP']}\n")
    if summary.immediate_nogo_triggered:
        sys.stdout.write(f"[ATENCAO] Bloqueio Imediato ativado: {summary.immediate_nogo_reasons}\n")
    sys.stdout.write(f"Relatório gerado em: {args.output}\n")
    sys.stdout.write(f"==========================================================\n")

    return summary.exit_code


if __name__ == "__main__":
    sys.exit(main())
