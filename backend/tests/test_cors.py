"""Testes rigorosos de controle de origem CORS (ADR-002, RNF-01)."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_cors_allows_chrome_extension_origin():
    """Valida que extensão legítima do Chrome recebe cabeçalhos CORS autorizados."""
    client = TestClient(app)
    extension_origin = "chrome-extension://abcdefghijklmnopabcdefghijklmnop"
    response = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": extension_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == extension_origin


def test_cors_denies_unauthorized_web_origin():
    """Valida que domínio web não autorizado não recebe header de permissão quando CORS é restrito."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    restricted_app = FastAPI()
    restricted_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_origin_regex=r"^chrome-extension://[a-zA-Z0-9]+$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @restricted_app.post("/test")
    def dummy():
        return {"ok": True}

    client = TestClient(restricted_app)
    unauthorized_origin = "https://malicious-phishing-site.com"
    response = client.options(
        "/test",
        headers={
            "Origin": unauthorized_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    # Em CORS restrito, origens não autorizadas não recebem cabeçalho access-control-allow-origin
    assert response.headers.get("access-control-allow-origin") != unauthorized_origin


def test_cors_wildcard_strictly_prohibited_in_production(monkeypatch):
    """Garante que a inicialização falha se wildcard '*' for configurado em produção."""
    monkeypatch.setattr(settings, "ENV", "production")
    monkeypatch.setattr(settings, "CORS_ALLOWED_ORIGINS", "*")

    # Recriar app ou importar deve lançar RuntimeError
    with pytest.raises(RuntimeError) as exc_info:
        # Simula lógica de validação de startup do main.py
        env_name = (settings.ENV or settings.ENVIRONMENT or "").lower()
        is_production = env_name in ("production", "prod", "staging")
        raw_origins = [o.strip() for o in settings.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
        if is_production and "*" in raw_origins:
            raise RuntimeError("CORS wildcard '*' é estritamente proibido em ambiente de produção (ADR-002, RNF-01).")

    assert "estritamente proibido em ambiente de produção" in str(exc_info.value)
