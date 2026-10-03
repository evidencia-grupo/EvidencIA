"""Test fixtures and fake repository generator for audit tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Tuple

import pytest
import sys
from pathlib import Path

# Add scripts directory to sys.path so 'audit' package is importable
_scripts_dir = Path(__file__).resolve().parent.parent.parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from audit.repo import RepoAccess


@pytest.fixture
def make_repos(tmp_path: Path) -> Callable[..., Tuple[Path, Path, RepoAccess]]:
    """Factory fixture to create fake docs and code repositories in tmp_path."""

    def _factory(full_passing: bool = True) -> Tuple[Path, Path, RepoAccess]:
        docs_dir = tmp_path / "fake_docs"
        code_dir = tmp_path / "fake_code"
        docs_dir.mkdir(parents=True, exist_ok=True)
        code_dir.mkdir(parents=True, exist_ok=True)

        if full_passing:
            # 1. Docs - Engage
            gq_file = docs_dir / "docs" / "visao" / "guiding-questions.md"
            gq_file.parent.mkdir(parents=True, exist_ok=True)
            gq_text = "# Guiding Questions\n## Essential Question\nComo sistemas de IA podem ajudar as pessoas a avaliar a confiabilidade de informações sem substituir seu pensamento crítico?\n## Challenge\nDesafio CBL\n## Guiding Questions\n"
            for i in range(1, 13):
                gq_text += f"- GQ{i:02d}: Pergunta orientadora {i}\n"
            gq_text += "## Respostas Sintetizadas\nResumo\n## Evidências Utilizadas\nEvidencias\n## Decisões Derivadas\nDecisoes\n## Hipóteses Ainda Não Validadas\nHipoteses\n## Relação Engage → Investigate\nTransicao\n"
            gq_file.write_text(gq_text, encoding="utf-8")

            eq_file = docs_dir / "docs" / "visao" / "essential-question-alignment.md"
            eq_file.write_text("# Alinhamento\nAvaliando como a IA pode apoiar sem substituir seu pensamento crítico.", encoding="utf-8")

            dec_file = docs_dir / "docs" / "visao" / "decision-log.md"
            dec_file.write_text("# Decision Log\n| D-001 | 2026-10-02 | ADR-001 adotado |", encoding="utf-8")

            # 2. Docs - ADR
            adr_file = docs_dir / "docs" / "adr" / "ADR-001-evidence-first.md"
            adr_file.parent.mkdir(parents=True, exist_ok=True)
            adr_file.write_text(
                "# ADR-001\nStatus: Aceito\nDecisão: Fim do score global, inclusão de HU11 no MVP, suporte a Evidence-Only e proibição de mock em produção.",
                encoding="utf-8",
            )

            # 3. Docs - Investigate & EDA
            eda_res = docs_dir / "docs" / "investigate" / "eda-results.md"
            eda_res.parent.mkdir(parents=True, exist_ok=True)
            eda_res.write_text(
                "# EDA Results\n| Recall@1 | 0.65 |\n| Recall@3 | 0.81 |\n| Recall@5 | 0.89 |\n| MRR | 0.72 |\n| nDCG@5 | 0.76 |",
                encoding="utf-8",
            )

            eda_dec = docs_dir / "docs" / "investigate" / "eda-decisions.md"
            eda_dec.write_text("# Decisões\nAchado 1: Fake.br é léxico -> Evidência: EDA -> Impacto: RAG -> Decisão: Usar FactChecks", encoding="utf-8")

            # 4. Docs - Act
            act_dir = docs_dir / "docs" / "cbl" / "act"
            act_dir.mkdir(parents=True, exist_ok=True)
            (act_dir / "experiment-plan.md").write_text("# Plano Experimental", encoding="utf-8")
            (act_dir / "participant-protocol.md").write_text("# Protocolo\nTCLE e consentimento livre com pseudonimização", encoding="utf-8")
            (act_dir / "metrics-definition.md").write_text("# Métricas Definidas\nRegras sem pendências", encoding="utf-8")
            (act_dir / "telemetry-spec.md").write_text('# Telemetria\nEventos permitidos: "analysis_requested", "panel_opened"', encoding="utf-8")
            (act_dir / "limitations.md").write_text("# Limitações", encoding="utf-8")

            # Act results
            summary_content = '{"metrics": {"condition_A": {"accuracy_assisted": {"mean": 0.75}}, "condition_B": {"accuracy_assisted": {"mean": 0.85}}}}'
            import hashlib
            sha = hashlib.sha256(summary_content.encode("utf-8")).hexdigest()
            (act_dir / "results.md").write_text(
                f"# Resultados\nN = 12 participantes por condição.\nsummary_sha256: `{sha}`\nDecisão: GO\n## Limitações observadas\nEfeito novidade observado.",
                encoding="utf-8",
            )

            # 5. Docs - Reflect & Share
            ref_dir = docs_dir / "docs" / "cbl" / "reflect-share"
            ref_dir.mkdir(parents=True, exist_ok=True)
            (ref_dir / "reflection.md").write_text(
                f"# Reflexão\nObservamos acurácia de 85% [EV: docs:docs/cbl/act/results.md#res@1234567] na intervenção.",
                encoding="utf-8",
            )
            (ref_dir / "showcase-script.md").write_text(
                "# Showcase\n## Challenge\nDesafio\n## Essential Question\nPergunta\n## Guiding Questions\nGQs\n## EDA\nDados\n## ADR\nDecisao\n## Evidence UI\nInterface\n## Act\nValidacao com 85% [EV: docs:docs/cbl/act/results.md#act@1234567]",
                encoding="utf-8",
            )
            (ref_dir / "demo-script.md").write_text("# Demo Script", encoding="utf-8")
            (ref_dir / "lessons-learned.md").write_text("# Lições", encoding="utf-8")
            (ref_dir / "research-portfolio.md").write_text("# Portfólio", encoding="utf-8")

            # 6. Docs - Scrum & Traceability
            scrum_dir = docs_dir / "docs" / "scrum"
            scrum_dir.mkdir(parents=True, exist_ok=True)
            (scrum_dir / "product-backlog.md").write_text("# Backlog", encoding="utf-8")
            (scrum_dir / "definition-of-done.md").write_text("# DoD", encoding="utf-8")
            (scrum_dir / "ceremonies.md").write_text("# Cerimônias", encoding="utf-8")

            for sp in ["sprint-01", "sprint-02"]:
                sp_dir = scrum_dir / sp
                sp_dir.mkdir(parents=True, exist_ok=True)
                (sp_dir / "sprint-goal.md").write_text("# Goal", encoding="utf-8")
                (sp_dir / "sprint-backlog.md").write_text("# Backlog", encoding="utf-8")
                (sp_dir / "retrospective.md").write_text("# Retro\nStatus: Concluído", encoding="utf-8")
                (sp_dir / "review.md").write_text(
                    "# Review\nStatus: Concluído\nP90 medido: 450ms\n"
                    "1. O que prometemos: Entregar\n2. O que entregamos: Entregue\n"
                    "3. O que conseguimos demonstrar: Demo\n4. O que não conseguimos demonstrar: Nada\n"
                    "5. Que evidência comprova: Testes\n6. Que decisão mudou: ADR\n",
                    encoding="utf-8",
                )

            req_dir = docs_dir / "docs" / "requisitos"
            req_dir.mkdir(parents=True, exist_ok=True)
            (req_dir / "catalogo-requisitos.md").write_text("# Requisitos\nHU11: Must Have\nHU13\nHU14\nHU15\nHU16", encoding="utf-8")
            (req_dir / "matriz-rastreabilidade.md").write_text(
                "# Matriz\n| GQ | ADR | HU |\n" + "".join(f"| GQ{i:02d} | ADR-001 | HU01 |\n" for i in range(1, 13)),
                encoding="utf-8",
            )

            # 7. Code - Datasets and Schemas
            ml_ds_dir = code_dir / "backend" / "ml" / "datasets"
            ml_ds_dir.mkdir(parents=True, exist_ok=True)
            (ml_ds_dir / "sources.yaml").write_text(
                "fakebr:\n  role: linguistic_corpus\nfactchecksbr:\n  role: fact_check_evidence\nclaimpt:\n  role: methodological_auxiliary\n  notes: PT-EU",
                encoding="utf-8",
            )
            (code_dir / "backend" / "data").mkdir(parents=True, exist_ok=True)
            (code_dir / "backend" / "data" / "README.md").write_text("# Data README", encoding="utf-8")
            (code_dir / "backend" / "data" / ".gitkeep").write_text("", encoding="utf-8")
            (code_dir / "backend" / "data" / "manifest.json").write_text(
                '{"datasets": {"factchecks": {"sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}}}',
                encoding="utf-8",
            )

            schemas_dir = code_dir / "backend" / "ml" / "schemas"
            schemas_dir.mkdir(parents=True, exist_ok=True)
            (schemas_dir / "evidence.py").write_text(
                "class EvidenceRecord: pass\nclass NewsRecord: pass\nclass VerdictNormalized: pass\n",
                encoding="utf-8",
            )

            # 8. Code - Providers and Architecture
            prov_dir = code_dir / "backend" / "app" / "services" / "providers"
            prov_dir.mkdir(parents=True, exist_ok=True)
            (prov_dir / "base.py").write_text(
                "class LLMProvider:\n    async def extract_claims(self, transcript: str, video_title: str): pass\n    async def generate_reflection(self, claims, evidence): pass\n",
                encoding="utf-8",
            )
            (prov_dir / "factory.py").write_text(
                "class MockInProductionError(Exception): pass\ndef get_provider(): raise MockInProductionError()\n",
                encoding="utf-8",
            )
            (code_dir / "backend" / "tests").mkdir(parents=True, exist_ok=True)
            (code_dir / "backend" / "tests" / "test_no_mock_in_production.py").write_text("def test_mock(): pass", encoding="utf-8")
            (code_dir / "backend" / "tests" / "test_no_silent_mock_fallback.py").write_text("def test_fallback(): pass", encoding="utf-8")
            (code_dir / "backend" / "tests" / "test_provider_failure.py").write_text("def test_failure(): pass", encoding="utf-8")
            (code_dir / "backend" / "tests" / "test_retrieval_latency.py").write_text("def test_latency(): pass", encoding="utf-8")
            (code_dir / "backend" / "tests" / "test_security.py").write_text(
                "def test_security(): pass\n# rate_limit transcript limit prompt_injection\n",
                encoding="utf-8",
            )

            # 9. Code - Shared schemas & UI
            shared_dir = code_dir / "shared" / "schemas"
            shared_dir.mkdir(parents=True, exist_ok=True)
            (shared_dir / "api-schema.json").write_text(
                '{"properties": {"claims": {}, "reflectionQuestions": {}, "limitations": {}, "analysisMode": {}}}',
                encoding="utf-8",
            )
            (code_dir / "shared" / "types").mkdir(parents=True, exist_ok=True)
            (code_dir / "shared" / "types" / "api.ts").write_text("export interface SearchHit { score: number; }", encoding="utf-8")

            ext_comp = code_dir / "extension" / "src" / "panel" / "components"
            ext_comp.mkdir(parents=True, exist_ok=True)
            (ext_comp / "EvidenceCard.tsx").write_text("export const EvidenceCard = () => <div/>;", encoding="utf-8")
            (ext_comp / "ReflectionQuestions.tsx").write_text("export const ReflectionQuestions = () => <div/>;", encoding="utf-8")

            # 10. Code - Telemetry
            telem_dir = code_dir / "extension" / "src" / "telemetry"
            (telem_dir / "schema").mkdir(parents=True, exist_ok=True)
            (telem_dir / "schema" / "event.schema.json").write_text('{"title": "TelemetryEvent"}', encoding="utf-8")
            (telem_dir / "sanitize.ts").write_text("export function sanitize() { return {}; }", encoding="utf-8")
            (telem_dir / "events.test.ts").write_text("test('telemetry', () => {});", encoding="utf-8")

            # 11. Code - Act Analysis
            act_analysis = code_dir / "analysis" / "act" / "out"
            act_analysis.mkdir(parents=True, exist_ok=True)
            (act_analysis / "summary.json").write_text(summary_content, encoding="utf-8")

            # 12. Code - Security & Gitignore
            (code_dir / ".gitignore").write_text(".env*\nbackend/data/*\nanalysis/act/data/\n", encoding="utf-8")
            wf_dir = code_dir / ".github" / "workflows"
            wf_dir.mkdir(parents=True, exist_ok=True)
            (wf_dir / "ci.yml").write_text("name: CI", encoding="utf-8")
            (wf_dir / "security.yml").write_text("name: Security", encoding="utf-8")
            (wf_dir / "freeze-guard.yml").write_text("name: Freeze Guard", encoding="utf-8")

            # 13. Code - Notebook (17 sections, executed)
            nb_cells = [
                {"cell_type": "code", "execution_count": 1, "source": ["# Seção 0\n"], "outputs": []},
            ]
            for i in range(1, 17):
                nb_cells.append({"cell_type": "markdown", "source": [f"## {i}. Section {i}\n"]})
                nb_cells.append({"cell_type": "code", "execution_count": i + 1, "source": [f"print({i})\n"], "outputs": []})

            nb_dir = code_dir / "notebooks"
            nb_dir.mkdir(parents=True, exist_ok=True)
            (nb_dir / "eda_datasets.ipynb").write_text(json.dumps({"cells": nb_cells}), encoding="utf-8")

        repo = RepoAccess(docs_repo=docs_dir, code_repo=code_dir)
        return docs_dir, code_dir, repo

    return _factory
