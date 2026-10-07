"""Aceitação de RF-14/RF-15: seleção, startup, deadline e Evidence-Only."""

import asyncio
import json
import logging
import os
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings, settings
from app.main import app
from app.providers.base import LLMProvider
from app.providers.factory import get_provider
from app.providers.mock import MockLLMProvider, MockProvider
from app.providers.ollama import OllamaProvider
from app.providers.remote import RemoteLLMProvider
from app.providers.types import Claim, MockInProductionError, ProviderUnavailableError
from app.schemas import AnalyzeRequest
from app.services.evidence_retrieval import retrieve_evidence
from app.services.fact_checker import FactCheckerService
from ml.retrieval.search import SearchHit, _search_chroma
from ml.schemas.evidence import EvidenceRecord


@pytest.fixture
def sample_request():
    return AnalyzeRequest(
        videoId="llm-acceptance",
        videoTitle="Chá de casca de banana cura diabetes",
        channelName="Saúde",
        transcript="Circula nas redes que chá de casca de banana cura diabetes e zera glicose em 3 dias sem remédio.",
        uploadDate="2026-05-10T12:00:00Z",
    )


@pytest.fixture
def record():
    return EvidenceRecord(
        evidence_id="factchecksbr:lupa:banana",
        dataset="factchecksbr",
        dataset_version="2026-10",
        claim_text="Chá de casca de banana cura diabetes",
        review_title="Checagem sobre chá",
        review_url="https://example.test/checagem",
        publisher="Agência de checagem",
        evidence_summary="Não há evidências para essa cura.",
        verdict_normalized="contradicted",
        provenance={
            "source_url": "https://example.test/dataset",
            "content_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "ingested_at": "2026-10-01T00:00:00Z",
        },
    )


def test_interface_is_abstract_and_mock_name_compatible():
    assert MockProvider is MockLLMProvider
    with pytest.raises(TypeError):
        LLMProvider()

    class Incomplete(LLMProvider):
        async def extract_claims(self, transcript, video_title):
            return []

    with pytest.raises(TypeError):
        Incomplete()


@pytest.mark.parametrize(
    "name,endpoint",
    [("ollama", "http://localhost:11434/api/chat"), ("remote", "https://gateway.test/v1/chat/completions")],
)
def test_configuration_routes_extraction_and_reflection_at_startup(name, endpoint, sample_request, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", name)
    monkeypatch.setenv("REMOTE_LLM_BASE_URL", "https://gateway.test/v1")
    monkeypatch.setenv("REMOTE_LLM_API_KEY", "test-secret")
    config = Settings(_env_file=None)
    monkeypatch.setattr(settings, "LLM_PROVIDER", config.LLM_PROVIDER)
    assert get_provider().name == name
    contents = iter(
        [
            json.dumps({"claims": [{"text": sample_request.videoTitle}]}),
            json.dumps(
                {"questions": ["Quais fontes existem?", "Qual é a data da fonte?", "Que dados independentes existem?"]}
            ),
        ]
    )

    async def post(url, **kwargs):
        content = next(contents)
        payload = (
            {"message": {"content": content}} if name == "ollama" else {"choices": [{"message": {"content": content}}]}
        )
        return httpx.Response(200, json=payload)

    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=post)) as infer:
        with TestClient(app) as client:
            result = client.post("/api/v1/analyze", json=sample_request.model_dump())
        assert result.status_code == 200
        assert result.json()["analysisMode"] == "evidence_first"
        assert infer.await_count == 2
        assert all(call.args[0] == endpoint for call in infer.call_args_list)
        if name == "remote":
            assert all(call.kwargs["headers"]["Authorization"] == "Bearer test-secret" for call in infer.call_args_list)
        assert sample_request.videoTitle in infer.call_args_list[1].kwargs["json"]["messages"][1]["content"]


@pytest.mark.parametrize("alias", ["ENV", "ENVIRONMENT", "APP_ENV", "NODE_ENV"])
def test_production_alias_cannot_be_masked_by_development(alias, monkeypatch, caplog):
    monkeypatch.setenv(alias, "  PrOdUcTiOn  ")
    with caplog.at_level(logging.CRITICAL, logger="app.audit"), pytest.raises(MockInProductionError):
        get_provider("mock", "development")
    assert caplog.records[-1].event == "mock_in_production_blocked"
    assert caplog.records[-1].provider == "mock"
    assert caplog.records[-1].environment == "production"


from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("alias", ["ENV", "ENVIRONMENT"])
def test_uvicorn_aborts_before_serving_when_mock_is_configured_in_production(alias):
    environment = dict(os.environ, LLM_PROVIDER="mock", PYTHONDONTWRITEBYTECODE="1")
    for key in ("ENV", "ENVIRONMENT", "APP_ENV", "NODE_ENV"):
        environment.pop(key, None)
    environment[alias] = "production"
    result = subprocess.run(
        [sys.executable, "-m", "uvicorn", "app.main:app"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
        cwd=backend_dir,
    )
    assert result.returncode == 3
    assert "mock_in_production_blocked" in result.stderr
    assert "Application startup failed" in result.stderr


def test_env_alias_and_default_deadline():
    config = Settings(_env_file=None, ENV="production", LLM_PROVIDER="remote")
    assert config.ENV == "production"
    assert config.LLM_TIMEOUT_SECONDS == 15
    assert config.OLLAMA_TIMEOUT_SECONDS == 15
    assert config.REMOTE_LLM_TIMEOUT_SECONDS == 15
    for bad in [0, -1, 16, float("nan"), float("inf")]:
        with pytest.raises(ValidationError):
            Settings(_env_file=None, LLM_TIMEOUT_SECONDS=bad)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error", [ProviderUnavailableError("offline"), httpx.ReadTimeout("timeout"), RuntimeError("broken API")]
)
async def test_extraction_failure_returns_vector_evidence(sample_request, record, error):
    provider = MagicMock()
    provider.extract_claims = AsyncMock(side_effect=error)
    provider.generate_reflection = AsyncMock()
    hit = SearchHit(record.evidence_id, 0.9, record, record.provenance)
    with (
        patch("app.services.fact_checker.get_provider", return_value=provider),
        patch("app.services.evidence_retrieval.search", return_value=[hit]) as search,
        patch("app.services.fact_checker.brazilian_fact_matcher.find_match") as lexical,
    ):
        result = await FactCheckerService().analyze(sample_request)
    search.assert_called_once_with(sample_request.transcript, k=5)
    lexical.assert_not_called()
    provider.generate_reflection.assert_not_awaited()
    assert result.analysisMode == "evidence_only"
    assert result.claims[0].evidence[0].url == record.review_url
    assert (
        result.claims[0].evidence[0].provenance.contentHash
        == "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    )
    assert result.claims[0].evidence[0].publishedAt == ""
    assert result.claims[0].uncertainty == "contextualized"
    assert any("temporariamente indisponível" in message for message in result.limitations)


@pytest.mark.asyncio
@pytest.mark.parametrize("stage", ["extraction", "reflection"])
async def test_real_timeout_cancels_inference_and_preserves_evidence(stage, sample_request, monkeypatch):
    cancelled = asyncio.Event()

    async def slow(*args):
        try:
            await asyncio.sleep(1)
        finally:
            cancelled.set()

    provider = MagicMock()
    provider.extract_claims = AsyncMock(
        return_value=[Claim(text=sample_request.videoTitle), Claim(text=sample_request.videoTitle)]
    )
    provider.generate_reflection = AsyncMock(side_effect=ProviderUnavailableError("offline"))
    setattr(provider, "extract_claims" if stage == "extraction" else "generate_reflection", AsyncMock(side_effect=slow))
    monkeypatch.setattr(settings, "LLM_TIMEOUT_SECONDS", 0.01)
    with patch("app.services.fact_checker.get_provider", return_value=provider):
        result = await FactCheckerService().analyze(sample_request)
    assert cancelled.is_set()
    assert result.analysisMode == "evidence_only"
    assert all(claim.evidence for claim in result.claims)
    assert result.claims
    if stage == "reflection":
        assert len(result.claims) == 2
        provider.generate_reflection.assert_awaited_once()
    assert all(len(claim.reflectionQuestions) == 3 for claim in result.claims)


@pytest.mark.asyncio
async def test_llm_budget_is_shared_across_extraction_and_reflections(sample_request):
    clock = [100.0]
    provider = MagicMock()

    async def extract(*args):
        clock[0] += 2
        return [Claim(text=sample_request.videoTitle), Claim(text=sample_request.videoTitle)]

    async def reflect(*args):
        clock[0] += 1
        return ["Que fontes existem?", "Qual é a data?", "Que dados independentes existem?"]

    provider.extract_claims = AsyncMock(side_effect=extract)
    provider.generate_reflection = AsyncMock(side_effect=reflect)
    wait_for = asyncio.wait_for
    with (
        patch("app.services.fact_checker.get_provider", return_value=provider),
        patch("app.services.fact_checker.time.perf_counter", side_effect=lambda: clock[0]),
        patch("app.services.fact_checker.asyncio.wait_for", wraps=wait_for) as wait,
    ):
        result = await FactCheckerService().analyze(sample_request)
    assert [call.kwargs["timeout"] for call in wait.call_args_list] == [15.0, 13.0, 12.0]
    assert result.analysisMode == "evidence_first"


@pytest.mark.parametrize(
    "raw",
    [
        "{}",
        '{"questions": null}',
        '{"questions": [1, 2, 3]}',
        '{"questions": ["A?", "B?"]}',
        '{"questions": ["A", "B?", "C?"]}',
        "invalid JSON",
    ],
)
@pytest.mark.parametrize("cls", [OllamaProvider, RemoteLLMProvider])
@pytest.mark.asyncio
async def test_malformed_reflection_is_a_provider_failure(cls, raw):
    provider = cls()
    with patch.object(provider, "_chat", new=AsyncMock(return_value=raw)):
        with pytest.raises(ProviderUnavailableError):
            await provider.generate_reflection([Claim(text="Alegação")], [])


@pytest.mark.parametrize("cls", [OllamaProvider, RemoteLLMProvider])
@pytest.mark.parametrize("response", [503, httpx.ReadTimeout("offline")])
@pytest.mark.asyncio
async def test_reflection_http_failure_is_a_provider_failure(cls, response):
    provider = cls(base_url="https://gateway.test/v1")
    mock = (
        AsyncMock(side_effect=response)
        if isinstance(response, Exception)
        else AsyncMock(return_value=httpx.Response(response))
    )
    with patch("httpx.AsyncClient.post", new=mock), pytest.raises(ProviderUnavailableError):
        await provider.generate_reflection([Claim(text="Alegação")], [])


def test_retrieval_does_not_invent_sources_for_unhydrated_or_non_factual_hits(record):
    missing_source = record.model_copy(update={"review_url": None})
    missing_provenance = record.model_copy(update={"provenance": None})
    hits = [
        SearchHit("unknown", 0.9, None, None),
        SearchHit(record.evidence_id, 0.8, missing_source, record.provenance),
        SearchHit(record.evidence_id, 0.7, missing_provenance, None),
    ]
    with patch("app.services.evidence_retrieval.search", return_value=hits):
        assert retrieve_evidence("consulta") == []
    with patch("app.services.evidence_retrieval.search", side_effect=RuntimeError("index offline")):
        assert retrieve_evidence("consulta") == []


@pytest.mark.parametrize("record_json,expected", [("valid", True), (None, False), ("invalid", False)])
def test_chroma_hydrates_canonical_evidence_and_provenance(record, record_json, expected, tmp_path, monkeypatch):
    metadata = {"record_json": record.model_dump_json() if record_json == "valid" else record_json}
    collection = MagicMock()
    collection.query.return_value = {
        "ids": [[record.evidence_id]],
        "distances": [[0.2]],
        "documents": [[record.claim_text]],
        "metadatas": [[metadata]],
    }
    chroma = SimpleNamespace(PersistentClient=lambda **kwargs: SimpleNamespace(get_collection=lambda name: collection))
    monkeypatch.setitem(sys.modules, "chromadb", chroma)
    with patch("ml.embeddings.encoder.default_encoder.encode", return_value=[[0.1, 0.2]]):
        hits = _search_chroma("banana", k=5, filters=None, collection_name="test", chroma_dir=str(tmp_path))
    assert (hits[0].record == record) is expected
    assert (hits[0].provenance == record.provenance) is expected


def test_index_preserves_record_for_vector_evidence(record, tmp_path, monkeypatch):
    from ml.retrieval.index import build_index

    silver = tmp_path / "silver"
    silver.mkdir()
    (silver / "facts.jsonl").write_text(record.model_dump_json() + "\n")
    collection = MagicMock()
    chroma = SimpleNamespace(
        PersistentClient=lambda **kwargs: SimpleNamespace(get_or_create_collection=lambda **kwargs: collection)
    )
    monkeypatch.setitem(sys.modules, "chromadb", chroma)
    with patch("ml.embeddings.encoder.EmbeddingEncoder.encode", return_value=[[0.1, 0.2]]):
        build_index(str(silver), chroma_dir=str(tmp_path / "chroma"))
    stored = collection.upsert.call_args.kwargs["metadatas"][0]["record_json"]
    assert EvidenceRecord.model_validate_json(stored) == record


def test_production_in_env_file_cannot_be_hidden_by_another_alias(tmp_path, monkeypatch, caplog):
    env_file = tmp_path / ".env"
    env_file.write_text("ENV=development\nENVIRONMENT=production\nLLM_PROVIDER=mock\n")
    config = Settings(_env_file=env_file)
    with patch("app.providers.factory.settings", config), caplog.at_level(logging.CRITICAL, logger="app.audit"):
        with pytest.raises(MockInProductionError):
            get_provider("mock", "development")
    assert caplog.records[-1].event == "mock_in_production_blocked"
