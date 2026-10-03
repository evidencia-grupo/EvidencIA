"""Testes para garantir ausência de fallback silencioso para mock em serviços de produção.

DÍVIDA TÉCNICA DOCUMENTADA (ADR-001 / Sprint 1):
Atualmente, FactCheckerService possui caminhos de fallback silencioso para heurísticas
embutidas e fontes estáticas caso o provider Ollama/Qwen falhe ou retorne None.
Este teste anteriormente estava marcado como xfail temporário.
Na Sprint 2 (issue 'Failure/timeout handling'), os fallbacks silenciosos foram removidos
e o teste agora passa como PASSED diretamente.

Ocorrências identificadas de fallback silencioso em backend/app/services/fact_checker.py:
1. Linhas 64-65: Branch direto para `_mock_analysis` quando `settings.LLM_PROVIDER == "mock"`.
2. Linhas 85-88: `if not extracted_propositions: _extract_check_worthy_claims(...)` (heurísticas regex embutidas).
3. Linhas 142-161: `if not sources:` injeção de fontes estáticas pré-fabricadas (SciELO / Agência Pública).
4. Linhas 199-205: `if not summary: synthesis_service.generate_accessible_summary(...)` (síntese por template fixo).
5. Linhas 296-438: Método inteiro `_mock_analysis(...)` embutido no serviço orquestrador.

Refs: ADR-001, IS-11, S2-06.
"""

import ast
import os


def test_no_silent_fallback_in_fact_checker():
    """Varre FactCheckerService à procura de métodos e blocos de fallback para mock ou dados estáticos."""
    fact_checker_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "app", "services", "fact_checker.py")
    )
    assert os.path.exists(fact_checker_path), "fact_checker.py não encontrado"

    with open(fact_checker_path, "r", encoding="utf-8") as f:
        content = f.read()
        tree = ast.parse(content, filename=fact_checker_path)

    detected_fallbacks = []

    # 1. Procura método _mock_analysis
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "_mock_analysis":
                detected_fallbacks.append("Método '_mock_analysis' presente em FactCheckerService")

    # 2. Procura referências a fallback de fontes estáticas ("src-01", "scielo.br")
    if "src-01" in content and "scielo.br" in content:
        detected_fallbacks.append("Injeção de fontes estáticas de fallback encontrada em fact_checker.py")

    # 3. Procura heurísticas regex embutidas como fallback de extração
    if "_extract_check_worthy_claims" in content:
        detected_fallbacks.append("Heurística analítica embutida '_extract_check_worthy_claims' presente")

    # O teste deve falhar se qualquer fallback silencioso for encontrado
    assert not detected_fallbacks, f"Fallbacks silenciosos detectados em produção: {detected_fallbacks}"
