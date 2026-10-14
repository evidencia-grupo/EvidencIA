"""RF-06/07/12, RNF-04/06, ADR-006: noise is not factual evidence."""

import hashlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import settings
from app.providers.types import Claim
from app.schemas import AnalyzeRequest
from app.services.brazilian_fact_matcher import BrazilianFactMatcher
from app.services.fact_checker import FactCheckerService
from ml.classifier.claim_extractor import extract_candidate_claims, is_conversational_filler
from ml.datasets.dataset_downloader import load_local_sample_dataset


INTRO = "Tá começando o seu programa de saúde, com informação para toda a família."
FACT = "Chá de casca de banana cura diabetes e zera a glicose no sangue em 3 dias"


@pytest.fixture
def matcher(monkeypatch):
    monkeypatch.setattr(type(settings), "is_production", lambda self: False)
    return BrazilianFactMatcher()


@pytest.mark.parametrize("text", [
    INTRO,
    "Está começando o nosso programa Estação SUS de saúde e prevenção.",
    "Olá pessoal, hoje vamos falar de vacina, dengue, Anvisa e saúde.",
    "Se inscreva no canal para saber sobre chá de casca de banana e diabetes.",
    "Muito obrigado por assistir nosso vídeo sobre a vacina contra a dengue.",
])
def test_filler_rejected_before_loading_or_scoring(matcher, text):
    assert is_conversational_filler(text)
    matcher._dataset = []
    with patch.object(matcher, "_load") as load:
        assert matcher.find_match(text, threshold=0) is None
    load.assert_not_called()


@pytest.mark.parametrize("text", [
    "saúde", "vacina", "vacinas", "SUS", "saúde saúde saúde", "vacina vacina vacina",
    "Um programa de saúde para você.", "Programa de saúde e prevenção", "Saúde e prevenção", "vacina dengue Anvisa SUS",
    "Quero conversar sobre vacina e dengue", "Falaremos sobre saúde e programa",
    "são também muito seus suas", "", "!!!",
])
@pytest.mark.parametrize("threshold", [0, 0.30])
def test_generic_terms_do_not_match_even_with_lower_threshold(matcher, text, threshold):
    assert matcher.find_match(text, threshold=threshold) is None


@pytest.mark.parametrize("entry", load_local_sample_dataset(), ids=lambda entry: entry["id"])
def test_exact_corpus_claims_keep_relation_and_provenance(matcher, entry):
    result = matcher.find_match(entry["claim"])
    assert result is not None
    evidence = result["evidence"]
    assert evidence.sourceId == f"src-br-{entry['id']}"
    assert evidence.url == entry["review_url"]
    assert evidence.publisher == entry["publisher"]
    assert evidence.snippet == entry["evidence_summary"]
    assert evidence.publishedAt == (entry.get("published_at") or "")
    assert evidence.provenance.dataset == "demonstracao_local"
    canonical = json.dumps(entry, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert evidence.provenance.contentHash == "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
    assert evidence.relation == {
        "apoiada": "supports", "contraditada": "contradicts", "inconclusiva": "contextualizes",
    }[entry["status"]]


def test_negation_and_changed_predicate_remain_contextual(matcher):
    for text in ("Não é verdade que " + FACT, FACT.replace("cura", "não cura"),
                 FACT.replace("3 dias", "30 dias")):
        result = matcher.find_match(text)
        assert result is not None
        assert result["evidence"].relation == "contextualizes"


def test_single_word_cannot_match_a_short_entry_with_high_jaccard(matcher):
    matcher._dataset = [{"claim": "Saúde pública"}]
    assert matcher.find_match("saúde") is None


def test_threshold_still_applies_after_content_gate(matcher):
    assert matcher.find_match(FACT, threshold=2.0) is None


def test_factual_sentence_after_greeting_is_not_lost(matcher):
    candidates = extract_candidate_claims(INTRO + " " + FACT + ".")
    assert candidates == [FACT]
    assert matcher.find_match(candidates[0]) is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["evidence_first", "evidence_only"])
async def test_greeting_never_reaches_any_evidence_lookup(mode):
    provider = MagicMock(is_mock=False, extract_claims=AsyncMock(return_value=[Claim(text=INTRO)]))
    request = AnalyzeRequest(videoId="intro", videoTitle="Programa Saúde", channelName="Canal",
                             transcript=INTRO, analysisMode=mode)
    with (
        patch("app.services.fact_checker.get_provider", return_value=provider),
        patch("app.services.fact_checker.brazilian_fact_matcher.find_match") as lexical,
        patch("app.services.fact_checker.retrieve_evidence") as retrieval,
        patch("app.services.fact_checker.fact_check_client.search_claims", new_callable=AsyncMock) as external,
    ):
        result = await FactCheckerService().analyze(request)
    assert result.claims == []
    lexical.assert_not_called()
    retrieval.assert_not_called()
    external.assert_not_called()
