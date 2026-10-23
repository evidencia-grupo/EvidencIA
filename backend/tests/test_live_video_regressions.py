"""Regressões do teste com vídeo real (jeJ6CWQozMw): IA remota e perguntas retóricas."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.providers.claim_saliency import score_claim_saliency
from app.providers.remote import RemoteLLMProvider
from app.providers.types import ProviderUnavailableError
from ml.classifier.claim_extractor import extract_candidate_claims

QUESTION = 'Lembra do café sem açúcar com gosto de "pneu queimado" que você provou no primeiro dia?'
FACT = 'E hoje ele já é chamado por muitos cientistas de "Diabetes Tipo 3".'


def test_rhetorical_question_is_not_a_claim():
    assert score_claim_saliency(QUESTION) == 0.0
    claims = extract_candidate_claims(f"{QUESTION} O Ministério da Saúde anunciou que a vacina contra a dengue chegou a 2 milhões de doses.")
    assert claims and not any("café" in claim for claim in claims)


@pytest.mark.asyncio
async def test_one_oversized_claim_does_not_discard_the_valid_ones():
    provider = RemoteLLMProvider(base_url="https://llm.example/v1", api_key="k", model="m")
    raw = {"claims": [{"text": "palavra " * 40}, {"text": FACT}]}
    with patch.object(provider, "_chat", new=AsyncMock(return_value=json.dumps(raw))):
        claims = await provider.extract_claims(FACT, "Título")
    assert [claim.text for claim in claims] == [FACT]


def _client_returning(response):
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.post = AsyncMock(return_value=response)
    return client


@pytest.mark.asyncio
async def test_openrouter_request_lists_fallback_models():
    provider = RemoteLLMProvider(base_url="https://openrouter.ai/api/v1", api_key="k", model="primary:free")
    ok = httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})
    client = _client_returning(ok)
    with patch("app.providers.remote.httpx.AsyncClient", return_value=client), \
            patch("app.providers.remote.settings.REMOTE_LLM_FALLBACK_MODELS", "backup-a:free, primary:free ,backup-b:free"):
        await provider._chat({"model": "primary:free", "messages": []})
    sent = client.post.await_args.kwargs["json"]
    assert sent["models"] == ["primary:free", "backup-a:free", "backup-b:free"]


@pytest.mark.asyncio
async def test_http_error_keeps_status_and_reason_for_diagnosis():
    provider = RemoteLLMProvider(base_url="https://openrouter.ai/api/v1", api_key="k", model="m")
    limited = httpx.Response(429, text='{"error":{"message":"Rate limit exceeded: free-models-per-day"}}')
    with patch("app.providers.remote.httpx.AsyncClient", return_value=_client_returning(limited)):
        with pytest.raises(ProviderUnavailableError, match="HTTP 429.*Rate limit"):
            await provider._chat({"model": "m", "messages": []})


TITLE = "Cortar Todo o Açúcar é REALMENTE Bom para Saúde? (Desafio de 14 Dias)"
GLYCOGEN = "Seu estoque de glicogênio (aquele açúcar de reserva armazenado no fígado e músculos) zerou"


def test_search_queries_go_from_full_claim_to_keywords_to_video_topic():
    from app.services.fact_check_client import claim_search_queries

    queries = claim_search_queries(GLYCOGEN, TITLE, search_query="glicogênio zerou")
    assert queries[0] == ("glicogênio zerou", False)
    assert queries[1] == (GLYCOGEN, False)
    assert ("açúcar glicogênio", False) in queries
    assert queries[-3:] == [("açúcar cortar", True), ("açúcar saúde", True), ("açúcar", True)]
    # Palavras genéricas e de ligação nunca viram consulta.
    assert not any(word in query.split() for query, _ in queries[2:] for word in ("aquele", "seu", "realmente"))


@pytest.mark.asyncio
async def test_first_query_with_results_wins_in_preference_order():
    from app.services.fact_check_client import FactCheckClient

    client = FactCheckClient()
    client.api_key = "k"
    pair = {"source": "pair", "claim_text": "Estoque de glicogênio no fígado e músculos zera ao cortar açúcar"}
    hits = {"açúcar cortar": [{"source": "topic"}], "açúcar glicogênio": [pair]}
    with patch.object(client, "search_claims", new=AsyncMock(side_effect=lambda q, max_results: hits.get(q, []))):
        assert await client.search_for_claim(GLYCOGEN, None, TITLE) == ([pair], False)
    hits.pop("açúcar glicogênio")
    with patch.object(client, "search_claims", new=AsyncMock(side_effect=lambda q, max_results: hits.get(q, []))):
        assert await client.search_for_claim(GLYCOGEN, None, TITLE) == ([{"source": "topic"}], True)


@pytest.mark.asyncio
async def test_claim_query_result_must_share_the_claim_concepts():
    """DEMO-004: "vacinas preso" devolvia checagem sobre indenizações por vacina."""
    from app.services.fact_check_client import FactCheckClient

    client = FactCheckClient()
    client.api_key = "k"
    claim = "Bill Gates foi preso por causa das vacinas contra a covid."
    unrelated = {"claim_text": "Número de indenizações por vacinas contra covid é baixo", "source": MagicMock(title="Estadão: indenizações")}
    related = {"claim_text": "Bill Gates foi preso por crimes ligados às vacinas", "source": MagicMock(title="Lupa: Bill Gates")}
    with patch.object(client, "search_claims", new=AsyncMock(return_value=[unrelated])):
        assert await client.search_for_claim(claim) == ([], False)
    with patch.object(client, "search_claims", new=AsyncMock(return_value=[unrelated, related])):
        assert await client.search_for_claim(claim) == ([related], False)
