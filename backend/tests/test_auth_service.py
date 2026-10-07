"""Testes de autenticação, rotação e proteção de tokens efêmeros (ADR-002, RNF-01)."""

import time
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


def test_expired_token_rejection(monkeypatch):
    """Garante que tokens vencidos sejam rejeitados com HTTP 403."""
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)
    client = TestClient(app)

    # Cria token propositalmente expirado no passado
    past_timestamp = int(time.time()) - 3600
    payload = f"inst-expired-id.{past_timestamp}"
    signature = auth_service._sign(payload)
    expired_token = f"{payload}.{signature}"

    # Verificação direta no serviço
    assert auth_service.verify_token(expired_token) is None

    # Chamada ao endpoint protegido com token expirado
    resp = client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {expired_token}"},
        json={"videoId": "test_video", "rating": "positive"},
    )
    assert resp.status_code == 403
    assert "inválida ou expirada" in resp.json()["detail"]


def test_token_rotation_and_renewal():
    """Valida o ciclo de rotação: obtenção de novo token sem interrupção de serviço."""
    client = TestClient(app)
    inst_id = "inst-rotation-test-uuid"

    # 1. Emissão inicial
    resp1 = client.post(
        "/api/v1/auth/token",
        json={"installationId": inst_id, "clientVersion": "1.0.0"},
    )
    assert resp1.status_code == 200
    token1 = resp1.json()["token"]

    # 2. Rotação / renovação de token
    resp2 = client.post(
        "/api/v1/auth/token",
        json={"installationId": inst_id, "clientVersion": "1.0.0"},
    )
    assert resp2.status_code == 200
    token2 = resp2.json()["token"]

    # Ambos são válidos para a mesma instalação
    v1 = auth_service.verify_token(token1)
    v2 = auth_service.verify_token(token2)
    assert v1["installation_id"] == inst_id
    assert v2["installation_id"] == inst_id
