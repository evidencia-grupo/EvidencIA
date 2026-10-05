"""Testes unitários de execução para OllamaProvider e RemoteLLMProvider.

Garante cobertura dos fluxos de sucesso, erros de rede e respostas anômalas,
assegurando a aderência ao limiar de cobertura exigido pelo CI/CD.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.providers.ollama import OllamaProvider
from app.providers.remote import RemoteLLMProvider
from app.providers.types import Claim, ProviderUnavailableError


@pytest.mark.asyncio
async def test_ollama_is_available():
    provider = OllamaProvider(base_url="http://test-ollama:11434")

    # Caso de sucesso (status 200)
    mock_resp_ok = MagicMock()
    mock_resp_ok.status_code = 200
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp_ok
        assert await provider.is_available() is True

    # Caso de erro / exceção
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Connection refused")
        assert await provider.is_available() is False


@pytest.mark.asyncio
async def test_ollama_extract_claims_success():
    provider = OllamaProvider(base_url="http://test-ollama:11434")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {
            "content": '{"claims": [{"text": "Vacina reduz mortes", "search_query": "vacina mortes"}]}'
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        claims = await provider.extract_claims("Transcrição sobre vacinas", "Vídeo Vacina")
        assert len(claims) == 1
        assert claims[0].text == "Vacina reduz mortes"
        assert claims[0].search_query == "vacina mortes"


@pytest.mark.asyncio
async def test_ollama_extract_claims_http_error():
    provider = OllamaProvider(base_url="http://test-ollama:11434")
    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        with pytest.raises(ProviderUnavailableError, match="Ollama retornou HTTP 500"):
            await provider.extract_claims("Transcrição", "Título")


@pytest.mark.asyncio
async def test_ollama_extract_claims_empty_claims():
    provider = OllamaProvider(base_url="http://test-ollama:11434")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"message": {"content": '{"claims": []}'}}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        assert await provider.extract_claims("Transcrição", "Título") == []


@pytest.mark.asyncio
async def test_ollama_extract_claims_connection_failure():
    provider = OllamaProvider(base_url="http://test-ollama:11434")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Timeout de rede")
        with pytest.raises(ProviderUnavailableError, match="Falha de conexão com Ollama"):
            await provider.extract_claims("Transcrição", "Título")


@pytest.mark.asyncio
async def test_ollama_generate_reflection():
    provider = OllamaProvider()
    questions = await provider.generate_reflection([Claim(text="Afirmação específica")], [])
    assert len(questions) >= 3
    assert any("fontes primárias" in q for q in questions)


@pytest.mark.asyncio
async def test_remote_extract_claims_missing_base_url():
    provider = RemoteLLMProvider(base_url="")
    with pytest.raises(ProviderUnavailableError, match="REMOTE_LLM_BASE_URL não configurada"):
        await provider.extract_claims("Transcrição", "Título")


@pytest.mark.asyncio
async def test_remote_extract_claims_success():
    provider = RemoteLLMProvider(
        base_url="https://api.openai.test/v1",
        api_key="sk-test-key",
        model="gpt-test",
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"claims": [{"text": "PIX cobra taxa", "search_query": "pix taxa"}]}'
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        claims = await provider.extract_claims("Transcrição", "Título")
        assert len(claims) == 1
        assert claims[0].text == "PIX cobra taxa"


@pytest.mark.asyncio
async def test_remote_extract_claims_http_error():
    provider = RemoteLLMProvider(base_url="https://api.openai.test/v1")
    mock_resp = MagicMock()
    mock_resp.status_code = 502

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        with pytest.raises(ProviderUnavailableError, match="Provedor remoto respondeu HTTP 502"):
            await provider.extract_claims("Transcrição", "Título")


@pytest.mark.asyncio
async def test_remote_extract_claims_empty_or_malformed():
    provider = RemoteLLMProvider(base_url="https://api.openai.test/v1")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": '{"claims": []}'}}]}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        assert await provider.extract_claims("Transcrição", "Título") == []


@pytest.mark.asyncio
async def test_remote_extract_claims_network_failure():
    provider = RemoteLLMProvider(base_url="https://api.openai.test/v1")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = Exception("Conexão interrompida")
        with pytest.raises(ProviderUnavailableError, match="Falha de comunicação com provedor remoto"):
            await provider.extract_claims("Transcrição", "Título")


@pytest.mark.asyncio
async def test_remote_generate_reflection():
    provider = RemoteLLMProvider()
    questions = await provider.generate_reflection([Claim(text="Afirmação específica")], [])
    assert len(questions) >= 3
