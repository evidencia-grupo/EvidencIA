import json
from unittest.mock import AsyncMock, patch
import pytest
from app.services.ollama_service import OllamaService


@pytest.mark.asyncio
async def test_ollama_service_resilience_when_offline():
    """Garante que o serviço Ollama degrada graciosamente se o daemon local não estiver ativo."""
    offline_ollama = OllamaService(base_url="http://127.0.0.1:54321", timeout_seconds=0.5)

    is_up = await offline_ollama.is_available()
    assert is_up is False

    claims = await offline_ollama.extract_claims_with_qwen("Texto de teste", "Título")
    assert claims is None

    summary = await offline_ollama.generate_accessible_summary_with_qwen([], "Título")
    assert summary is None


def test_ollama_service_configuration():
    """Valida as configurações padrão do Ollama e Qwen 2.5-3B."""
    service = OllamaService()
    assert "11434" in service.base_url
    assert "qwen" in service.model.lower()


@pytest.mark.asyncio
async def test_ollama_service_is_available_online():
    """Valida checagem de integridade quando o Ollama está online."""
    from unittest.mock import MagicMock

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        service = OllamaService()
        assert await service.is_available() is True


@pytest.mark.asyncio
async def test_ollama_service_extract_claims_success():
    """Valida extração estruturada de alegações via Qwen quando o modelo responde com JSON válido."""
    from unittest.mock import MagicMock

    mock_claims_payload = {
        "claims": [
            {
                "text": "O estudo comprovou a eficácia da vacina",
                "search_query": "eficacia vacina estudo",
                "status": "apoiada",
                "evidence_summary": "Ensaios clínicos publicados corroboram.",
                "confidence": 0.95,
            }
        ]
    }
    mock_ollama_response = {
        "message": {
            "role": "assistant",
            "content": json.dumps(mock_claims_payload),
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_ollama_response
        mock_post.return_value = mock_resp

        service = OllamaService()
        claims = await service.extract_claims_with_qwen("Transcrição do vídeo", "Título")
        assert claims is not None
        assert len(claims) == 1
        assert claims[0]["text"] == "O estudo comprovou a eficácia da vacina"
        assert claims[0]["status"] == "apoiada"


@pytest.mark.asyncio
async def test_ollama_service_extract_claims_errors():
    """Valida tratamento seguro contra respostas HTTP de erro ou JSON inválido."""
    from unittest.mock import MagicMock

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Model Error"
        mock_post.return_value = mock_resp

        service = OllamaService()
        claims = await service.extract_claims_with_qwen("Transcrição", "Título")
        assert claims is None

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"message": {"content": "not-valid-json"}}
        mock_post.return_value = mock_resp

        service = OllamaService()
        claims = await service.extract_claims_with_qwen("Transcrição", "Título")
        assert claims is None


@pytest.mark.asyncio
async def test_ollama_service_generate_summary_lifecycle():
    """Valida síntese analítica gerada pelo Qwen em cenários de sucesso e falha."""
    from unittest.mock import MagicMock

    mock_ollama_response = {
        "message": {
            "role": "assistant",
            "content": "Olá Dona Lurdes! O vídeo traz informações verdadeiras confirmadas por fontes oficiais.",
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_ollama_response
        mock_post.return_value = mock_resp

        service = OllamaService()
        summary = await service.generate_accessible_summary_with_qwen(
            claims=[{"status": "apoiada", "text": "Fato", "evidence_summary": "Evidência"}],
            video_title="Título",
        )
        assert summary is not None
        assert "Dona Lurdes" in summary
        prompt = str(mock_post.call_args.kwargs["json"])
        assert "Nota:" not in prompt
        assert "Classificação Geral" not in prompt

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Error"
        mock_post.return_value = mock_resp

        service = OllamaService()
        summary = await service.generate_accessible_summary_with_qwen([], "Título")
        assert summary is None
