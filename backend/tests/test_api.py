from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Valida o endpoint de health check."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "services" in data
    assert "timestamp" in data


def test_analyze_video_success():
    """Valida o fluxo com transcrição válida e conformidade com o contrato."""
    payload = {
        "videoId": "test-vid-123",
        "videoTitle": "Vídeo Teste de Notícia Científica",
        "channelName": "Ciência Hoje",
        "uploadDate": "2026-09-28T10:00:00Z",
        "durationSeconds": 300,
        "transcript": "Este é um texto longo de teste com dados e evidências para validar se o modelo de fact-checking consegue extrair as alegações e pontuar com sucesso.",
        "language": "pt-BR",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["videoId"] == "test-vid-123"
    assert 0 <= data["score"] <= 100
    assert data["classification"] in ["verdadeiro", "moderado", "falso", "inconclusivo"]
    assert len(data["claims"]) > 0
    assert len(data["sources"]) > 0
    assert data["processingTimeMs"] >= 0


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
