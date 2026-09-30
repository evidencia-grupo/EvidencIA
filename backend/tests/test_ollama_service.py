import pytest
from app.services.ollama_service import OllamaService


@pytest.mark.asyncio
async def test_ollama_service_resilience_when_offline():
    """Garante que o serviço Ollama degrada graciosamente se o daemon local não estiver ativo."""
    # Instancia serviço apontando para porta inexistente para simular offline
    offline_ollama = OllamaService(base_url="http://127.0.0.1:54321", timeout_seconds=0.5)

    is_up = await offline_ollama.is_available()
    assert is_up is False

    claims = await offline_ollama.extract_claims_with_qwen("Texto de teste", "Título")
    assert claims is None

    summary = await offline_ollama.generate_accessible_summary_with_qwen([], "moderado", 50, "Título")
    assert summary is None


def test_ollama_service_configuration():
    """Valida as configurações padrão do Ollama e Qwen 2.5-3B."""
    service = OllamaService()
    assert "11434" in service.base_url
    assert "qwen" in service.model.lower()
