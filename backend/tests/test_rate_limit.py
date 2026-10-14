"""Testes funcionais de Rate Limiting (RNF-04)."""

from fastapi.testclient import TestClient

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


def _request(peer: str, forwarded: str | None = None):
    from starlette.requests import Request

    headers = [(b"x-forwarded-for", forwarded.encode())] if forwarded is not None else []
    return Request({"type": "http", "method": "GET", "path": "/", "headers": headers, "client": (peer, 1234)})


def test_client_key_ignores_forwarded_header_without_trusted_proxy(monkeypatch):
    """Sem proxy confiável (padrão), X-Forwarded-For é ignorado: o cliente não escolhe a própria chave."""
    from app.config import settings
    from app.limiter import client_key

    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 0)
    assert client_key(_request("10.0.0.5", "1.2.3.4")) == "10.0.0.5"


def test_client_key_uses_address_appended_by_trusted_proxy(monkeypatch):
    """Atrás de 1 proxy, cada cliente tem sua chave e a entrada falsificada à esquerda é ignorada."""
    from app.config import settings
    from app.limiter import client_key

    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)
    assert client_key(_request("10.0.0.5", "203.0.113.7")) == "203.0.113.7"
    assert client_key(_request("10.0.0.5", "203.0.113.8")) == "203.0.113.8"
    assert client_key(_request("10.0.0.5", "6.6.6.6, 203.0.113.7")) == "203.0.113.7"


def test_client_key_falls_back_when_chain_is_shorter_than_hops(monkeypatch):
    """Cadeia menor que o número de saltos (requisição sem passar pelo proxy) usa o par TCP."""
    from app.config import settings
    from app.limiter import client_key

    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 2)
    assert client_key(_request("10.0.0.5", "203.0.113.7")) == "10.0.0.5"
    assert client_key(_request("10.0.0.5")) == "10.0.0.5"
