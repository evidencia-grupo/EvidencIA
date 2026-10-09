#!/usr/bin/env python3
"""Diagnóstico local explícito; não imprime credenciais nem emite vereditos."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
settings = importlib.import_module("app.config").settings


def inspect_readiness(check_services: bool = False) -> dict:
    provider = settings.LLM_PROVIDER.strip().lower()
    result = {
        "scope": "local_configuration",
        "provider": provider,
        "demo_mode": provider == "mock",
        "external_search_configured": bool(settings.GOOGLE_FACT_CHECK_API_KEY),
        "external_search_verified": False,
        "vector_dependencies_installed": all(importlib.util.find_spec(name) is not None for name in ("chromadb", "sentence_transformers")),
        "vector_index_directory_exists": (ROOT / "backend/data/chroma").is_dir(),
        "vector_index_records": None,
        "provider_available": True if provider == "mock" else None,
        "warnings": [],
    }
    if result["external_search_configured"]:
        result["warnings"].append("Chave de busca presente; validade e quota da API externa ainda não verificadas.")
    if provider == "mock":
        result["warnings"].append("Provedor mock: demonstração local, sem inferência de um LLM real.")
    elif provider == "ollama":
        result["configured_model"] = settings.OLLAMA_MODEL
        if check_services:
            import httpx
            try:
                response = httpx.get(settings.OLLAMA_BASE_URL.rstrip("/") + "/api/tags", timeout=3, follow_redirects=False)
                response.raise_for_status()
                available = [item.get("name") for item in response.json().get("models", []) if isinstance(item, dict)]
                expected = settings.OLLAMA_MODEL
                result["provider_available"] = expected in available or (":" not in expected and expected + ":latest" in available)
                if not result["provider_available"]:
                    result["warnings"].append("Modelo configurado ausente no Ollama. Instale esse modelo ou configure o nome listado em ollama list.")
            except (httpx.HTTPError, ValueError, TypeError):
                result["provider_available"] = False
                result["warnings"].append("Ollama indisponível ou resposta inválida no diagnóstico local.")
    elif provider == "remote":
        result["remote_configuration_complete"] = all((settings.REMOTE_LLM_BASE_URL, settings.REMOTE_LLM_MODEL, settings.REMOTE_LLM_API_KEY))
        result["warnings"].append("Configuração remota não comprova disponibilidade; execute um teste com o provedor provisionado.")
    else:
        result["provider_available"] = False
        result["warnings"].append("LLM_PROVIDER desconhecido.")
    if check_services and result["vector_dependencies_installed"] and result["vector_index_directory_exists"]:
        try:
            import chromadb
            client = chromadb.PersistentClient(path=str(ROOT / "backend/data/chroma"))
            result["vector_index_records"] = client.get_collection("evidencia").count()
        except Exception:  # noqa: BLE001 - isolate optional index failures without exposing exception data
            result["warnings"].append("Não foi possível consultar a coleção evidencia; verifique a indexação e suas dependências.")
    if not result["external_search_configured"] and not result["vector_index_records"]:
        result["warnings"].append("Nenhum canal de evidências confirmado. Checagens podem permanecer inconclusivas; siga o guia de indexação e busca.")
    result["live_prerequisites_present"] = (
        not result["demo_mode"] and result["provider_available"] is True
        and bool(result["external_search_configured"] or result["vector_index_records"])
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-services", action="store_true", help="Consultar Ollama e a coleção local; não envia transcrições.")
    parser.add_argument("--require-live", action="store_true", help="Falhar quando faltam os pré-requisitos locais de LLM real e busca; não verifica a validade da chave externa.")
    args = parser.parse_args()
    result = inspect_readiness(args.check_services)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if args.require_live and not result["live_prerequisites_present"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
