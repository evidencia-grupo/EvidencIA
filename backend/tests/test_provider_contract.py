"""Testes de conformidade com o protocolo LLMProvider.

Garante que todos os providers implementam o contrato tipado esperado:
- isinstance(x, LLMProvider) é True em tempo de execução via @runtime_checkable.
- Métodos extract_claims e generate_reflection são assíncronos.
- MockProvider retorna estruturas de dados canônicas (Claim, list[str]).

Refs: ADR-001, IS-11.
"""

import inspect

from app.providers.base import LLMProvider
from app.providers.mock import MockProvider
from app.providers.ollama import OllamaProvider
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
