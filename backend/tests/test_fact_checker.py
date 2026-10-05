import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.schemas import AnalyzeRequest
from app.services.fact_checker import FactCheckerService


def request(text="dados"):
    return AnalyzeRequest(videoId="video", videoTitle="Título", channelName="Canal", transcript=(text + " ") * 60)


@pytest.mark.asyncio
@pytest.mark.parametrize("text,classification", [("dados", "verdadeiro"), ("talvez", "falso"), ("alegação", "moderado")])
async def test_demo_classifications(monkeypatch, text, classification):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    result = await FactCheckerService().analyze(request(text))
    assert result.classification == classification
    assert result.analysisMode == "demo"
    assert len(result.reflectionQuestions) >= 3
    assert all(question.endswith("?") for question in result.reflectionQuestions)


def test_unimplemented_provider_never_returns_fake_success(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "not-integrated")
    response = TestClient(app).post("/api/v1/analyze", json=request().model_dump())
    assert response.status_code == 503
    assert "IA própria ainda está em preparação" in response.json()["detail"]


def test_timeout_becomes_504(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    monkeypatch.setattr(settings, "LLM_TIMEOUT_SECONDS", 0.001)
    response = TestClient(app).post("/api/v1/analyze", json=request().model_dump())
    assert response.status_code == 504


@pytest.mark.asyncio
async def test_cancellation_is_propagated(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    task = asyncio.create_task(FactCheckerService().analyze(request()))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
