"""Testes de resiliência e suporte ao modo Evidence-Only sob falha externa (ARC-06 / Issue #37).

Garante que sob timeout ou indisponibilidade do provedor de LLM:
1. O backend não cai (zero crashes).
2. Degrada graciosamente para analysisMode="evidence_only".
3. Evidências recuperadas de corpora verificados (FactChecks.br) são retornadas.
4. Limitações explicam a indisponibilidade da síntese de linguagem.
"""

import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from app.config import settings
from app.providers.factory import ProviderUnavailableError
from app.schemas import AnalyzeRequest
from app.services.fact_checker import FactCheckerService


@pytest.fixture
def sample_request():
    return AnalyzeRequest(
        videoId="test-resilience-vid",
        videoTitle="Chá de casca de banana cura diabetes",
        channelName="Canal Saúde",
        transcript="Circula nas redes que chá de casca de banana cura diabetes e zera glicose em 3 dias sem remédio.",
        uploadDate="2026-05-10T12:00:00Z",
    )


@pytest.mark.asyncio
async def test_provider_unavailable_falls_back_to_evidence_only(sample_request, monkeypatch):
    """Quando o provider levanta ProviderUnavailableError, o serviço opera em modo evidence_only."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")

    service = FactCheckerService()

    with patch(
        "app.providers.mock.MockProvider.extract_claims",
        new_callable=AsyncMock,
        side_effect=ProviderUnavailableError("Daemon Ollama ou cluster inacessível"),
    ):
        response = await service.analyze(sample_request)

        assert response.analysisMode == "evidence_only"
        assert response.videoId == sample_request.videoId
        assert len(response.limitations) > 0
        assert any("evidence-only" in lim.lower() for lim in response.limitations)
        assert len(response.claims) > 0
        # Deve ter recuperado a evidência correspondente do dataset curado brasileiro
        assert any(len(c.evidence) > 0 for c in response.claims)
        assert any(c.uncertainty in ["contradicted", "supported", "contextualized"] for c in response.claims)


@pytest.mark.asyncio
async def test_provider_timeout_falls_back_to_evidence_only(sample_request, monkeypatch):
    """Quando a chamada de extração excede o timeout, degrada para modo evidence_only."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")
    monkeypatch.setattr(settings, "LLM_TIMEOUT_SECONDS", 0.05)

    service = FactCheckerService()

    async def slow_extract(*args, **kwargs):
        await asyncio.sleep(0.5)
        return []

    with patch("app.providers.mock.MockProvider.extract_claims", side_effect=slow_extract):
        response = await service.analyze(sample_request)

        assert response.analysisMode == "evidence_only"
        assert len(response.claims) > 0
        assert len(response.limitations) > 0
