from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.providers.mock import MockProvider
from app.providers.ollama import OllamaProvider
from app.providers.remote import RemoteLLMProvider
from app.providers.types import Claim, ProviderUnavailableError
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.fact_checker import FactCheckerService


def request():
    return AnalyzeRequest(videoId="atomic", videoTitle="Título com uma afirmação factual", channelName="Canal", uploadDate="2021-04-15", transcript="Eu prefiro filmes de comédia. Na minha opinião, este filme é muito bonito.")


@pytest.mark.asyncio
async def test_opinions_produce_empty_claims_without_evidence_lookup():
    provider = MockProvider()
    assert await provider.extract_claims(request().transcript, request().videoTitle) == []
    with patch("app.services.fact_checker.get_provider", return_value=provider), patch("app.services.fact_checker.brazilian_fact_matcher.find_match") as match, patch("app.services.fact_checker.fact_check_client.search_claims", new_callable=AsyncMock) as search:
        result = await FactCheckerService().analyze(request())
    assert result.claims == []
    assert result.analysisMode == "evidence_first"
    match.assert_not_called()
    search.assert_not_called()
    assert not {"score", "classification", "summary"} & result.model_dump().keys()


@pytest.mark.asyncio
async def test_unique_atomic_claims_with_individual_questions_and_temporal_context():
    provider = MagicMock()
    provider.extract_claims = AsyncMock(return_value=[Claim(id="duplicate", text="A população aumentou em 2021."), Claim(id="duplicate", text="O PIB diminuiu em 2021.")])
    provider.generate_reflection = AsyncMock(side_effect=lambda claims, evidence: [f"Que fontes ajudam a investigar {claims[0].text}?", "Qual era o período estudado?", "Que dados independentes existem?"])
    with patch("app.services.fact_checker.get_provider", return_value=provider), patch("app.services.fact_checker.brazilian_fact_matcher.find_match", return_value=None), patch("app.services.fact_checker.fact_check_client.search_claims", new_callable=AsyncMock, return_value=[]):
        result = await FactCheckerService().analyze(request())
    assert len({claim.id for claim in result.claims}) == 2
    assert [claim.text for claim in result.claims] == ["A população aumentou em 2021.", "O PIB diminuiu em 2021."]
    for claim in result.claims:
        assert claim.uncertainty == "insufficient_evidence"
        assert claim.temporalContext.videoPublishedAt == "2021-04-15"
        assert claim.text in claim.reflectionQuestions[0]
    assert all(len(call.args[0]) == 1 for call in provider.generate_reflection.call_args_list)
    AnalyzeResponse.model_validate(result.model_dump())
    with pytest.raises(ValidationError):
        AnalyzeResponse.model_validate({**result.model_dump(), "score": 90})
    broken = result.model_dump()
    del broken["claims"][0]["temporalContext"]
    with pytest.raises(ValidationError):
        AnalyzeResponse.model_validate(broken)


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", [OllamaProvider(), RemoteLLMProvider(base_url="https://example.test")])
async def test_providers_distinguish_valid_empty_extraction_from_malformed_response(provider):
    response = MagicMock(status_code=200)
    def payload(content):
        return {"message": {"content": content}, "choices": [{"message": {"content": content}}]}
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=response) as post:
        response.json.return_value = payload('{"claims": []}')
        assert await provider.extract_claims(request().transcript, request().videoTitle) == []
        prompt = post.call_args.kwargs["json"]["messages"][0]["content"]
        assert "uma única proposição" in prompt
        for invalid in ['{}', '{"claims": null}', '{"claims": [{"text": ""}]}']:
            response.json.return_value = payload(invalid)
            with pytest.raises(ProviderUnavailableError):
                await provider.extract_claims(request().transcript, request().videoTitle)
