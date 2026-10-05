from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_submit_positive_feedback_success():
    payload = {
        "videoId": "vid-123",
        "rating": "positive",
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"
    assert "sucesso" in data["message"].lower()


def test_submit_negative_feedback_with_reason_success():
    payload = {
        "videoId": "vid-456",
        "rating": "negative",
        "reason": "outdated_sources",
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "received"


def test_submit_feedback_invalid_rating():
    payload = {
        "videoId": "vid-123",
        "rating": "bom",  # Não é positive/negative
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 422


def test_submit_feedback_empty_video_id():
    payload = {
        "videoId": "",
        "rating": "positive",
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 422


def test_submit_feedback_lgpd_forbids_extra_fields():
    # RNF-05 / LGPD: Nenhum dado pessoal ou PII deve ser aceito na carga
    payload = {
        "videoId": "vid-123",
        "rating": "positive",
        "user_email": "helena@escola.com.br",
        "tracking_id": "track-999",
    }
    response = client.post("/api/v1/feedback", json=payload)
    assert response.status_code == 422
