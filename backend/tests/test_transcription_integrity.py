import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.providers.ollama import OllamaProvider
from app.providers.remote import RemoteLLMProvider
from app.providers.types import Claim as ProviderClaim
from app.providers.reflection_catalog import REFLECTION_QUESTIONS
from app.schemas import AnalyzeRequest, Evidence
from app.services.fact_checker import FactCheckerService


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", [OllamaProvider(), RemoteLLMProvider(base_url="https://provider.example/v1")])
async def test_provider_receives_tail_of_full_transcript(provider):
    tail = "O estudo científico apresentou resultados depois de dez anos de pesquisa."
    transcript = "Introdução contextual sem alegações. " * 200 + tail
    with patch.object(provider, "_chat", new=AsyncMock(return_value=json.dumps({"claims": [{"text": tail}]}))) as chat:
        result = await provider.extract_claims(transcript, "Título")
    content = chat.call_args.args[0]["messages"][1]["content"]
    assert transcript in content
    assert result[0].text == tail


@pytest.mark.asyncio
async def test_evidence_only_retrieves_each_proposition_separately():
    first = "A vacina foi aprovada após estudos clínicos realizados por pesquisadores."
    second = "O banco central divulgou dados econômicos sobre a inflação no último ano."
    req = AnalyzeRequest(videoId="video", videoTitle="v", channelName="c", transcript=first+" "+second, analysisMode="evidence_only")
    def retrieve(text):
        return [(text, Evidence(sourceId="saude" if text==first else "economia", relation="contextualizes", title=text, url="https://example.test/review", publishedAt="", publisher="Fonte",provenance={"dataset":"test","indexedAt":"2026-10-09T00:00:00Z"}))]
    with patch("app.services.fact_checker.extract_candidate_claims", return_value=[first,second]), patch("app.services.fact_checker.retrieve_evidence", side_effect=retrieve) as search:
        result = await FactCheckerService().analyze(req)
    assert [c.args[0] for c in search.call_args_list]==[first,second]
    assert [c.evidence[0].sourceId for c in result.claims]==["saude","economia"]


@pytest.mark.asyncio
async def test_linguistic_note_does_not_leak_between_claims():
    first = "Uma vacina apresentou resultados em estudos clínicos com participantes."
    second = "O banco central divulgou dados econômicos sobre a inflação no último ano."
    req = AnalyzeRequest(videoId="video", videoTitle="v", channelName="c", transcript=first+" "+second)
    provider = MagicMock(is_mock=False,extract_claims=AsyncMock(return_value=[ProviderClaim(text=first),ProviderClaim(text=second)]),generate_reflection=AsyncMock(return_value=REFLECTION_QUESTIONS[:3]))
    source=Evidence(sourceId="economia",relation="contextualizes",title=second,url="https://example.test/review",publishedAt="",publisher="Fonte",provenance={"dataset":"test","indexedAt":"2026-10-09T00:00:00Z"})
    with patch("app.services.fact_checker.get_provider",return_value=provider), patch("app.services.fact_checker.brazilian_fact_matcher.find_match",side_effect=[None,{"evidence":source,"relation":"contextualizes"}]), patch("app.services.fact_checker.fact_check_client.search_claims",new=AsyncMock(return_value=[])),patch("app.services.fact_checker.classifier_service.classify",return_value={"heuristic_reasons":["Nota exclusiva da primeira alegação"]}):
        result=await FactCheckerService().analyze(req)
    assert "Nota exclusiva" in result.claims[0].temporalContext.note
    assert result.claims[1].temporalContext.note is None
