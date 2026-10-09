"""Impede que presença de chave ou mock seja confundida com operação real."""
import importlib.util
import json
from pathlib import Path

import httpx

spec = importlib.util.spec_from_file_location("readiness_cli", Path(__file__).resolve().parents[2] / "scripts/check_readiness.py")
readiness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readiness)


def test_demo_never_becomes_live_when_key_is_present(monkeypatch):
    monkeypatch.setattr(readiness.settings, "LLM_PROVIDER", "mock")
    monkeypatch.setattr(readiness.settings, "GOOGLE_FACT_CHECK_API_KEY", "private-test-value")
    result = readiness.inspect_readiness()
    assert result["demo_mode"]
    assert not result["live_prerequisites_present"]
    assert not result["external_search_verified"]
    assert "private-test-value" not in json.dumps(result)


def test_missing_ollama_model_is_not_available(monkeypatch):
    monkeypatch.setattr(readiness.settings, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(readiness.settings, "OLLAMA_MODEL", "requested:3b")
    monkeypatch.setattr(readiness.importlib.util, "find_spec", lambda _: None)
    monkeypatch.setattr(httpx, "get", lambda *a, **kw: httpx.Response(200, json={"models": [{"name": "other:9b"}]}, request=httpx.Request("GET", "http://localhost/api/tags")))
    result = readiness.inspect_readiness(check_services=True)
    assert result["provider_available"] is False
    assert any("Modelo configurado ausente" in warning for warning in result["warnings"])


def test_unchecked_provider_is_not_confirmed(monkeypatch):
    monkeypatch.setattr(readiness.settings, "LLM_PROVIDER", "ollama")
    result = readiness.inspect_readiness(check_services=False)
    assert result["provider_available"] is None
    assert not result["live_prerequisites_present"]
