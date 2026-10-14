"""Segmentação de legendas automáticas (ASR) sem pontuação — issue #67."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.providers.mock import MockLLMProvider
from app.providers.types import Claim as ProviderClaim
from app.schemas import AnalyzeRequest
from app.services.fact_checker import FactCheckerService
from ml.classifier.claim_extractor import (
    MAX_CLAIM_WORDS,
    _segment_unpunctuated_stream,
    extract_candidate_claims,
    segment_transcript,
    shorten_claim,
)

ASR_SENTENCE = (
    "olá pessoal hoje vamos falar sobre saúde e alimentação no dia a dia "
    "segundo estudos recentes o consumo de açúcar aumentou muito entre jovens brasileiros nos últimos anos "
    "então o ministério da saúde anunciou uma campanha nacional de prevenção ao diabetes nas escolas públicas "
    "mas muita gente ainda acredita que o chá de canela cura diabetes em poucos dias sem remédio "
    "porque existem vídeos espalhando essa ideia sem nenhuma comprovação científica sólida "
)
ASR_TRANSCRIPT = (ASR_SENTENCE * 20).strip()


def _words(text):
    return " ".join(text.casefold().strip(" .!?").split())


def test_unpunctuated_stream_becomes_short_sentences():
    sentences = segment_transcript(ASR_TRANSCRIPT)

    assert len(sentences) > 20
    transcript = _words(ASR_TRANSCRIPT)
    for sentence in sentences:
        assert 1 <= len(sentence.split()) <= 25
        assert sentence[0].isupper()
        assert sentence.endswith(".")
        # Cada frase continua sendo um trecho literal da transcrição.
        assert _words(sentence) in transcript


def test_breaks_before_discourse_markers():
    sentences = _segment_unpunctuated_stream(ASR_SENTENCE)

    assert any(sentence.startswith("Segundo estudos") for sentence in sentences)
    assert any(sentence.startswith("Então o ministério") for sentence in sentences)
    assert any(sentence.startswith("Mas muita gente") for sentence in sentences)


def test_forces_break_without_markers():
    stream = " ".join(f"palavra{index}" for index in range(100))
    sentences = _segment_unpunctuated_stream(stream)

    assert all(len(sentence.split()) <= 25 for sentence in sentences)
    assert " ".join(s.rstrip(".") for s in sentences).casefold() == stream


def test_punctuated_transcript_is_kept_as_is():
    transcript = "A Anvisa aprovou a vacina. O governo anunciou a campanha nacional!"
    assert segment_transcript(transcript) == ["A Anvisa aprovou a vacina.", "O governo anunciou a campanha nacional!"]


def test_shorten_claim_keeps_short_text_and_reduces_long_text():
    short = "O ministério da saúde anunciou uma campanha."
    assert shorten_claim(short) == short
    shortened = shorten_claim(ASR_SENTENCE)
    assert len(shortened.split()) <= MAX_CLAIM_WORDS
    assert _words(shortened) in _words(ASR_SENTENCE)


def test_offline_extractor_finds_claims_in_asr_transcript():
    claims = extract_candidate_claims(ASR_TRANSCRIPT, max_claims=3)

    assert claims
    assert all(len(claim.split()) <= MAX_CLAIM_WORDS for claim in claims)


@pytest.mark.asyncio
async def test_mock_provider_does_not_return_whole_transcript():
    claims = await MockLLMProvider().extract_claims(ASR_TRANSCRIPT, "Vídeo")

    assert claims
    assert all(len(claim.text.split()) <= MAX_CLAIM_WORDS for claim in claims)


def _segments_for(transcript, words_per_segment=6):
    words = transcript.split()
    return [
        {"text": " ".join(words[i:i + words_per_segment]), "start": float(i), "duration": 2.0}
        for i in range(0, len(words), words_per_segment)
    ]


@pytest.mark.asyncio
async def test_long_provider_claim_is_shortened_and_keeps_timestamp():
    segments = _segments_for(ASR_TRANSCRIPT)
    request = AnalyzeRequest(
        videoId="asr", videoTitle="Vídeo", channelName="Canal", transcript=ASR_TRANSCRIPT,
        segments=segments, analysisMode="evidence_first",
    )
    provider = MagicMock(is_mock=False)
    provider.extract_claims = AsyncMock(return_value=[ProviderClaim(text=ASR_SENTENCE)])
    provider.generate_reflection = AsyncMock(return_value=[])

    with patch("app.services.fact_checker.get_provider", return_value=provider), \
            patch("app.services.fact_checker.brazilian_fact_matcher.find_match", return_value=None), \
            patch("app.services.fact_checker.fact_check_client.search_claims", new=AsyncMock(return_value=[])):
        result = await FactCheckerService().analyze(request)

    assert len(result.claims) == 1
    claim = result.claims[0]
    assert len(claim.text.split()) <= MAX_CLAIM_WORDS
    assert claim.timestampStart is not None
    assert _words(claim.text) in _words(claim.transcriptSnippet)
