"""Testes semânticos e contratuais da Fase 2 (Confiança da Evidência, ADR-006)."""

import pytest
from app.schemas import AnalyzeRequest
from app.services.brazilian_fact_matcher import brazilian_fact_matcher
from app.services.fact_checker import FactCheckerService


@pytest.mark.asyncio
async def test_claim_video_strictly_separated_from_fact_check_claim(monkeypatch):
    """Caso 1: O ClaimCard deve conter a fala/título do vídeo, NUNCA o claim_text da base de fact-checking."""
    service = FactCheckerService()
    req = AnalyzeRequest(
        videoId="test-video-id",
        videoTitle="Vídeo Polêmico sobre Vacinas e Saúde Pública",
        channelName="Canal Exemplo",
        transcript="Neste vídeo nós discutimos sobre diabetes e remédios caseiros amplamente divulgados.",
        durationSeconds=120,
    )
    # Força modo evidence_only para checar se o título do vídeo é preservado
    res = await service.analyze(req)
    assert len(res.claims) > 0
    # A alegação principal deve ser a fala/título do vídeo, não o texto da checagem
    assert res.claims[0].text != "Chá milagroso caseiro cura diabetes em 3 dias"
    assert res.claims[0].text in (req.videoTitle, "Neste vídeo nós discutimos sobre diabetes e remédios caseiros amplamente divulgados.")


def test_lexical_overlap_moderate_defaults_to_contextualizes():
    """Caso 2: Match lexical moderado sem alinhamento semântico estrito não pode assumir 'contradicts'."""
    text = "Conversa sobre vacinas de rna e saude com duvidas sobre prazos"
    match = brazilian_fact_matcher.find_match(text, threshold=0.15)
    assert match is not None
    assert match["relation"] == "contextualizes"
    assert match["evidence"].relation == "contextualizes"
    assert "contextualizada" in match["evidence"].matchReason.lower()


def test_strong_contradiction_yields_contradicts():
    """Caso 3: Afirmação idêntica a boato desmentido gera 'contradicts'."""
    text = "Chá de casca de banana cura diabetes e zera a glicose no sangue segundo receita caseira"
    match = brazilian_fact_matcher.find_match(text)
    assert match is not None
    assert match["relation"] == "contradicts"
    assert match["evidence"].relation == "contradicts"


@pytest.mark.asyncio
async def test_insufficient_evidence_state(monkeypatch):
    """Caso 4: Nenhuma fonte encontrada resulta no estado explícito 'insufficient_evidence'."""
    service = FactCheckerService()
    req = AnalyzeRequest(
        videoId="unrelated-vid",
        videoTitle="Construindo um castelo de areia na praia de Santos",
        channelName="Vlog do Mar",
        transcript="Hoje fomos para a praia e construímos um castelo de areia bem grande com as crianças.",
        durationSeconds=60,
    )
    res = await service.analyze(req)
    for claim in res.claims:
        if not claim.evidence:
            assert claim.uncertainty == "insufficient_evidence"


@pytest.mark.asyncio
async def test_timestamps_and_snippet_extracted():
    """Caso 5: Geração de timestamps relativos e trecho da transcrição."""
    service = FactCheckerService()
    transcript = "Introdução longa inicial. Especialistas afirmam que o chá cura diabetes rapidamente. Conclusão do vídeo."
    snippet, t_start, t_end = service._extract_snippet_and_timestamps(
        transcript, "o chá cura diabetes rapidamente", duration_seconds=100
    )
    assert snippet is not None
    assert "chá cura diabetes" in snippet
    assert t_start is not None
    assert t_start > 0
    assert t_end is not None
    assert t_end > t_start
