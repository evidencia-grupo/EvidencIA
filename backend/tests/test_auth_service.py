"""Testes de autenticação e proteção de tokens efêmeros (ADR-002, RNF-01)."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services.auth_service import auth_service


def test_issue_auth_token():
    """Valida emissão de token efêmero com instalação anônima."""
    client = TestClient(app)
    resp = client.post(
        "/api/v1/auth/token",
        json={"installationId": "anon-installation-uuid-987654321", "clientVersion": "1.0.0"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["tokenType"] == "Bearer"
    assert data["expiresIn"] == 86400

    # Valida estrutura do token
    verified = auth_service.verify_token(data["token"])
    assert verified is not None
    assert verified["installation_id"] == "anon-installation-uuid-987654321"


def test_auth_rejection_when_require_auth_is_true(monkeypatch):
    """Garante que requisições sem token retornem HTTP 401 quando REQUIRE_AUTH=True."""
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)
    client = TestClient(app)

    # Chamada sem cabeçalho Authorization -> 401
    resp_unauth = client.post(
        "/api/v1/feedback",
        json={"videoId": "test_video", "rating": "positive"},
    )
    assert resp_unauth.status_code == 401
    assert "Credencial de autenticação ausente" in resp_unauth.json()["detail"]

    # Chamada com token forjado/inválido -> 403
    resp_forbidden = client.post(
        "/api/v1/feedback",
        headers={"Authorization": "Bearer token_completamente_invalido.12345.signature"},
        json={"videoId": "test_video", "rating": "positive"},
    )
    assert resp_forbidden.status_code == 403
    assert "inválida ou expirada" in resp_forbidden.json()["detail"]

    # Chamada com token legítimo gerado pelo serviço -> 200
    valid_token = auth_service.create_token("inst-legit-12345")
    resp_ok = client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {valid_token}"},
        json={"videoId": "test_video", "rating": "positive"},
    )
    assert resp_ok.status_code == 200
