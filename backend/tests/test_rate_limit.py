"""Testes funcionais de Rate Limiting (RNF-04)."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.limiter import limiter


def test_rate_limit_exceeded_returns_429(monkeypatch):
    """Garante que requisições excedentes além do limite resultem em HTTP 429 Too Many Requests."""
    client = TestClient(app)
    
    # Reset storage do limiter para isolamento
    limiter.reset()

    # Dispara rajada para o endpoint de emissão de token com limite de 30/minute
    statuses = []
    for _ in range(35):
        resp = client.post("/api/v1/auth/token", json={"installationId": "test-installation-id-12345"})
        statuses.append(resp.status_code)

    assert 200 in statuses
    assert 429 in statuses
    assert statuses[-1] == 429

    # Limpa estado para testes subsequentes
    limiter.reset()
