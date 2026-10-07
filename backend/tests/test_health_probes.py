"""Testes de liveness, readiness e health probe desacoplado."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.fact_checker import fact_checker_service


def test_liveness_probe_returns_alive():
    """Valida que /health/live responde 200 com status alive."""
    client = TestClient(app)
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_readiness_probe_returns_ready():
    """Valida que /health/ready responde 200 com subsistemas operacionais."""
    client = TestClient(app)
    # Garante inicialização
    if fact_checker_service.provider is None:
        fact_checker_service.initialize_provider()

    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["components"]["provider"] == "operational"
    assert data["components"]["classifier"] == "operational"
    assert data["components"]["retrieval"] == "operational"


def test_readiness_probe_returns_503_when_subsystem_down(monkeypatch):
    """Valida que /health/ready retorna 503 quando um subsistema crítico não está operacional."""
    client = TestClient(app)
    # Simula falha do provider
    monkeypatch.setattr(fact_checker_service, "provider", None)

    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["status"] == "not_ready"
    assert detail["components"]["provider"] == "not_ready"


def test_health_check_dynamic_status():
    """Valida que /health reflete o estado dinâmico dos conectores."""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("operational", "degraded")
    assert "llmConnector" in data["services"]
    assert "classifier" in data["services"]
    assert "searchConnector" in data["services"]
