from datetime import datetime, timezone

import pytest
from app.config import settings
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_provider(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")


def test_health_check():
    """Valida o endpoint de health check."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["services"]["llmConnector"] == "demo"
    assert data["version"] == "1.0.0"
    assert "services" in data
    assert "timestamp" in data


def test_analyze_video_success():
    """Valida o fluxo com transcrição válida e conformidade com o contrato."""
    current_year = datetime.now(timezone.utc).year
    payload = {
        "videoId": "test-vid-123",
        "videoTitle": "Vídeo Teste de Notícia Científica",
        "channelName": "Ciência Hoje",
        "uploadDate": f"{current_year}-09-28T10:00:00Z",
        "durationSeconds": 300,
        "transcript": "Este é um texto longo de teste com dados e evidências para validar se o modelo de fact-checking consegue extrair as alegações e pontuar com sucesso.",
        "language": "pt-BR",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["analysisMode"] == "demo"
    assert data["videoId"] == "test-vid-123"
    assert data["videoTitle"] == payload["videoTitle"]
    assert data["channelName"] == payload["channelName"]
    assert data["uploadDate"] == payload["uploadDate"]
    assert data["temporalContext"] == {
        "publicationYear": current_year,
        "isOldContent": False,
        "message": f"As alegações foram apresentadas em {current_year}; mudanças posteriores não tornam falsa uma afirmação correta à época.",
    }
    assert 0 <= data["score"] <= 100
    assert data["classification"] in ["verdadeiro", "moderado", "falso", "inconclusivo"]
    assert len(data["claims"]) > 0
    assert len(data["sources"]) > 0
    assert data["processingTimeMs"] >= 0


def test_temporal_context_does_not_change_verdict():
    """Uma data antiga contextualiza a análise sem rebaixar uma alegação válida à época."""
    base_payload = {
        "videoId": "test-vid-context",
        "videoTitle": "Registro histórico",
        "channelName": "Arquivo Público",
        "transcript": "Este estudo apresenta dados históricos verificáveis e evidências documentais suficientes para a análise factual.",
    }
    current = client.post("/api/v1/analyze", json={**base_payload, "uploadDate": "2026-04-15T00:00:00Z"}).json()
    historical = client.post("/api/v1/analyze", json={**base_payload, "uploadDate": "2021-04-15T00:00:00Z"}).json()

    assert historical["temporalContext"]["publicationYear"] == 2021
    assert historical["temporalContext"]["isOldContent"] is True
    assert historical["classification"] == current["classification"] == "verdadeiro"
    assert historical["score"] == current["score"]
    assert [claim["status"] for claim in historical["claims"]] == [claim["status"] for claim in current["claims"]]


def test_analyze_video_short_transcript():
    """Valida rejeição de transcrição curta (< 50 caracteres) com HTTP 422."""
    payload = {
        "videoId": "test-vid-short",
        "videoTitle": "Vídeo Curto",
        "channelName": "Canal",
        "transcript": "Texto muito curto",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_video_missing_fields():
    """Valida erro 422 em campos obrigatórios ausentes."""
    payload = {
        "videoId": "vid-incomplete",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422
