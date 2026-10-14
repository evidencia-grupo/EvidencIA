"""Testes de conformidade com o protocolo LLMProvider.

Garante que todos os providers implementam o contrato tipado esperado:
- isinstance(x, LLMProvider) é True em tempo de execução via @runtime_checkable.
- Métodos extract_claims e generate_reflection são assíncronos.
- MockProvider retorna estruturas de dados canônicas (Claim, list[str]).

Refs: ADR-001, IS-11.
"""

import importlib.util
import inspect
import json
import re
from pathlib import Path

from app.providers.base import LLMProvider
from app.providers.mock import MockProvider
from app.providers.ollama import OllamaProvider
from app.providers.reflection_catalog import REFLECTION_QUESTIONS
from app.providers.remote import RemoteLLMProvider
from app.providers.types import Claim


def test_mock_provider_implements_llm_provider():
    """MockProvider deve implementar o protocolo LLMProvider."""
    provider = MockProvider()
    assert isinstance(provider, LLMProvider)
    assert provider.name == "mock"
    assert provider.is_mock is True


def test_ollama_provider_implements_llm_provider():
    """OllamaProvider deve implementar o protocolo LLMProvider."""
    provider = OllamaProvider()
    assert isinstance(provider, LLMProvider)
    assert provider.name == "ollama"
    assert provider.is_mock is False


def test_remote_provider_implements_llm_provider():
    """RemoteLLMProvider deve implementar o protocolo LLMProvider."""
    provider = RemoteLLMProvider()
    assert isinstance(provider, LLMProvider)
    assert provider.name == "remote"
    assert provider.is_mock is False


def test_provider_method_signatures():
    """Garante que as assinaturas dos métodos em todos os provedores são corrotinas assíncronas."""
    for cls in [MockProvider, OllamaProvider, RemoteLLMProvider]:
        instance = cls()
        assert inspect.iscoroutinefunction(instance.extract_claims), f"{cls.__name__}.extract_claims deve ser async"
        assert inspect.iscoroutinefunction(instance.generate_reflection), f"{cls.__name__}.generate_reflection deve ser async"


def test_mock_provider_returns_valid_claims_and_reflections():
    """Execução assíncrona do MockProvider deve retornar instâncias de Claim e perguntas em str."""
    import asyncio

    async def _run():
        provider = MockProvider()

        claims = await provider.extract_claims("Transcritor de teste para validação de extração.", "Vídeo de Teste")
        assert isinstance(claims, list)
        assert len(claims) > 0
        assert isinstance(claims[0], Claim)
        assert len(claims[0].text) > 0

        reflections = await provider.generate_reflection(claims, evidence=[])
        assert isinstance(reflections, list)
        assert len(reflections) >= 2
        for q in reflections:
            assert isinstance(q, str)
            assert q.endswith("?")

    asyncio.run(_run())


def _load_contract_generator():
    script = Path(__file__).resolve().parents[2] / "scripts" / "generate_contracts.py"
    spec = importlib.util.spec_from_file_location("generate_contracts", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_contracts_match_python_sources():
    """ARCH-001: catálogo de reflexão, JSON Schema e tipos TS idênticos ao gerado a partir do Python."""
    stale = [str(path) for path, content in _load_contract_generator().build().items()
             if path.read_text(encoding="utf-8") != content]
    assert stale == []


def test_reflection_catalog_items_match_typescript():
    """Mesmos itens, na mesma ordem, em reflection_catalog.py e shared/reflection-catalog.ts."""
    ts = (Path(__file__).resolve().parents[2] / "shared" / "reflection-catalog.ts").read_text(encoding="utf-8")
    array = re.search(r"REFLECTION_QUESTIONS = (\[.*\]) as const;", ts, re.S)
    assert array is not None
    assert json.loads(array.group(1)) == list(REFLECTION_QUESTIONS)


def test_mock_provider_skips_greetings_and_channel_calls():
    """No modo de demonstração, saudações e pedidos de inscrição não viram alegações."""
    import asyncio

    transcript = ("Olá pessoal, bem-vindos ao canal. Hoje vamos falar de saúde. "
                  "A vacina contra a dengue foi incorporada ao SUS em dezembro de 2023. Deixe seu like e se inscreva.")
    claims = asyncio.run(MockProvider().extract_claims(transcript, "Título"))
    assert [c.text for c in claims] == ["A vacina contra a dengue foi incorporada ao SUS em dezembro de 2023."]
