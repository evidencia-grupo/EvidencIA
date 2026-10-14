"""Testes do adaptador Ollama canônico (app.providers.ollama.OllamaProvider).

Migrados do antigo app.services.ollama_service (ARCH-001): o provedor canônico
nunca degrada silenciosamente para None; toda falha vira ProviderUnavailableError,
que o orquestrador converte em contingência explícita.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.ollama import OllamaProvider
from app.providers.types import Claim, ProviderUnavailableError


def _chat_response(content: str, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {"message": {"role": "assistant", "content": content}}
    return response


@pytest.mark.asyncio
async def test_ollama_provider_fails_explicitly_when_offline():
    """Daemon inacessível: indisponível no health check e erro explícito na extração."""
    offline = OllamaProvider(base_url="http://127.0.0.1:54321", timeout_seconds=0.5)

    assert await offline.is_available() is False
    with pytest.raises(ProviderUnavailableError):
        await offline.extract_claims("Texto de teste", "Título")


def test_ollama_provider_default_configuration():
    """Valida as configurações padrão do Ollama e Qwen 2.5-3B."""
    provider = OllamaProvider()
    assert "11434" in provider.base_url
    assert "qwen" in provider.model.lower()
    assert provider.is_mock is False


@pytest.mark.asyncio
async def test_ollama_provider_rejects_invalid_json():
    """Conteúdo que não é JSON vira ProviderUnavailableError, nunca alegação inventada."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _chat_response("not-valid-json")
        with pytest.raises(ProviderUnavailableError):
            await OllamaProvider().extract_claims("Transcrição", "Título")


@pytest.mark.asyncio
async def test_ollama_provider_extraction_prompt_is_evidence_first():
    """O prompt de extração não pede veredito, nota ou classificação global ao modelo."""
    payload = {"claims": [{"text": "O estudo comprovou a eficácia da vacina", "search_query": "eficacia vacina"}]}
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _chat_response(json.dumps(payload))
        claims = await OllamaProvider().extract_claims("Transcrição do vídeo", "Título")

    assert [claim.text for claim in claims] == ["O estudo comprovou a eficácia da vacina"]
    prompt = str(mock_post.call_args.kwargs["json"])
    assert "Não atribua notas ou vereditos" in prompt
    for forbidden in ("Nota:", "Classificação Geral", "veredito preliminar", "apoiada|contraditada"):
        assert forbidden not in prompt


@pytest.mark.asyncio
async def test_ollama_provider_reflection_lifecycle():
    """Reflexão: sem alegações não chama a rede; resposta inválida falha explicitamente."""
    provider = OllamaProvider()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        assert await provider.generate_reflection([], []) == []
        mock_post.assert_not_called()

    claim = Claim(id="clm-01", text="Fato", search_query="fato", confidence=0.9)
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _chat_response(json.dumps({"questions": ["Apenas uma?"]}))
        with pytest.raises(ProviderUnavailableError):
            await provider.generate_reflection([claim], [])
        prompt = str(mock_post.call_args.kwargs["json"])
        assert "Nota:" not in prompt
        assert "Classificação Geral" not in prompt

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = _chat_response("", status_code=500)
        with pytest.raises(ProviderUnavailableError, match="HTTP 500"):
            await provider.generate_reflection([claim], [])
