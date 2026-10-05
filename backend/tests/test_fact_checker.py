import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.schemas import AnalyzeRequest
from app.services.fact_checker import FactCheckerService
from app.providers.types import ProviderUnavailableError


def request(text="dados"):
    return AnalyzeRequest(videoId="video", videoTitle="Título", channelName="Canal", transcript=(text + " ") * 60)


@pytest.mark.asyncio
async def test_evidence_first_analysis(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    result = await FactCheckerService().analyze(request())
    assert result.analysisMode == "evidence_first"
    assert len(result.claims) > 0
    assert result.claims[0].uncertainty in [
        "supported",
        "contradicted",
        "contextualized",
        "conflicting",
        "insufficient_evidence",
    ]
    questions = result.claims[0].reflectionQuestions
    assert len(questions) == 3
    assert all(question.endswith("?") for question in questions)
    assert not any(word in " ".join(questions).lower() for word in ("certo", "errado", "verdadeiro", "falso"))


@pytest.mark.asyncio
async def test_non_neutral_provider_questions_use_fallback(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    with patch(
        "app.providers.mock.MockProvider.generate_reflection",
        new=AsyncMock(return_value=["O vídeo está errado?", "Pergunta 2?", "Pergunta 3?"]),
    ):
        result = await FactCheckerService().analyze(request())

    questions = result.claims[0].reflectionQuestions
    assert len(questions) == 3
    assert not any(word in " ".join(questions).lower() for word in ("certo", "errado", "verdadeiro", "falso"))


@pytest.mark.asyncio
async def test_evidence_only_analysis_still_includes_reflection_questions(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    with patch(
        "app.providers.mock.MockProvider.extract_claims",
        new=AsyncMock(side_effect=ProviderUnavailableError("offline")),
    ):
        result = await FactCheckerService().analyze(request())

    assert result.analysisMode == "evidence_only"
    assert result.claims == []
    assert result.limitations


def test_unimplemented_provider_never_returns_fake_success(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "not-integrated")
    response = TestClient(app).post("/api/v1/analyze", json=request().model_dump())
    assert response.status_code == 503
    assert "Falha ao consultar serviços upstream" in response.json()["detail"]


@pytest.mark.asyncio
async def test_cancellation_is_propagated(monkeypatch):
    from unittest.mock import patch

    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")

    async def slow_extract(*args, **kwargs):
        await asyncio.sleep(5)
        return []

    with patch("app.providers.mock.MockProvider.extract_claims", side_effect=slow_extract):
        task = asyncio.create_task(FactCheckerService().analyze(request()))
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
