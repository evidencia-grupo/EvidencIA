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
    assert data["analysisMode"] == "evidence_first"
    assert data["videoId"] == "test-vid-123"
    assert data["videoTitle"] == payload["videoTitle"]
    assert data["channelName"] == payload["channelName"]
    assert data["publishedAt"] == payload["uploadDate"]
    assert "score" not in data
    assert "classification" not in data
    assert len(data["claims"]) > 0
    for claim in data["claims"]:
        assert "id" in claim
        assert "text" in claim
        assert "uncertainty" in claim
        assert "evidence" in claim
        assert "temporalContext" in claim
        assert claim["temporalContext"]["videoPublishedAt"] == payload["uploadDate"]
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

    assert historical["claims"][0]["temporalContext"]["videoPublishedAt"] == "2021-04-15T00:00:00Z"
    assert "score" not in historical
    assert historical["claims"][0]["uncertainty"] == current["claims"][0]["uncertainty"]


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


def test_cors_preflight_allows_chrome_extension():
    """Valida permissão de preflight OPTIONS para extensões Chrome."""
    response = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": "chrome-extension://abcdefghijklmnopabcdefghijklmnop",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,X-Client-Version",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "chrome-extension://abcdefghijklmnopabcdefghijklmnop"


def test_classify_claim_endpoint():
    """Valida o endpoint POST /api/v1/classify para classificação ML."""
    # Teste de afirmação com forte teor de fake
    res_fake = client.post("/api/v1/classify", json={"text": "Chá milagroso caseiro cura diabetes em 3 dias"})
    assert res_fake.status_code == 200
    data_fake = res_fake.json()
    assert data_fake["dominant_label"] == "fake"
    assert "fake" in data_fake["probabilities"]
    assert "true" in data_fake["probabilities"]
    assert data_fake["confidence"] >= 0.50

    # Teste com limiar rigoroso provocando abstenção
    res_strict = client.post("/api/v1/classify", json={"text": "Afirmação genérica sem termos fortes", "threshold": 0.99})
    assert res_strict.status_code == 200
    data_strict = res_strict.json()
    assert data_strict["accepted"] is False
    assert data_strict["label"] == "unverified"

