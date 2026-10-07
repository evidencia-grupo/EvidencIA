"""Testes semânticos, adversariais e contratuais da Fase 2 e Release Candidate (ADR-006)."""

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
    assert "relacionada" in match["evidence"].matchReason.lower() or "contextualizada" in match["evidence"].matchReason.lower()


def test_strong_contradiction_yields_contradicts():
    """Caso 3: Afirmação idêntica a boato desmentido gera 'contradicts'."""
    text = "Chá de casca de banana cura diabetes e zera a glicose no sangue em 3 dias"
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


# =========================================================================
# BATERIA DE TESTES ADVERSARIAIS EPISTÊMICOS (Seção 4 do Fechamento)
# =========================================================================

def test_adversarial_similar_text_different_semantics_defaults_to_contextualizes():
    """Cenário Adversarial 1: Textos parecidos lexicamente mas com predicado diferente."""
    text = "Uso culinário de água morna com limão para temperar saladas e pratos gourmet saudáveis"
    match = brazilian_fact_matcher.find_match(text, threshold=0.20)
    if match:
        assert match["relation"] == "contextualizes", "Não pode contradizer uma receita culinária"
        assert match["evidence"].relation == "contextualizes"


def test_adversarial_same_entity_different_conclusion_does_not_falsely_contradict():
    """Cenário Adversarial 2: Mesma entidade (Anvisa / vacina), predicado e conclusão distintos."""
    text = "A Anvisa realizou reunião extraordinária para avaliar a importação de lotes de insumos hospitalares"
    match = brazilian_fact_matcher.find_match(text, threshold=0.15)
    if match:
        assert match["relation"] == "contextualizes"


def test_adversarial_same_news_different_temporal_context():
    """Cenário Adversarial 3: Mesmo tema econômico, mas contexto temporal histórico diferente."""
    text = "O Brasil registrou superávit comercial histórico na balança comercial durante o início dos anos 2000"
    match = brazilian_fact_matcher.find_match(text, threshold=0.20)
    if match:
        assert match["relation"] == "contextualizes"


def test_adversarial_explicitly_contradicted_claim():
    """Cenário Adversarial 4: Alegação explicitamente idêntica a boato desmentido."""
    text = "Consumir água morna com limão pela manhã neutraliza o pH do corpo e previne infecções virais"
    match = brazilian_fact_matcher.find_match(text)
    assert match is not None
    assert match["relation"] == "contradicts"


def test_adversarial_debunking_video_with_negation_does_not_yield_contradicts():
    """Cenário Adversarial 4b: Vídeo desmentindo o boato (negação explícita) NÃO pode receber 'contradicts'."""
    text = "Médicos e cientistas alertam que NÃO é verdade que chá de casca de banana cura diabetes"
    match = brazilian_fact_matcher.find_match(text)
    assert match is not None
    assert match["relation"] == "contextualizes", "Vídeo que desmente boato não pode ser rotulado como contradito pela checagem"


def test_adversarial_only_related_claim():
    """Cenário Adversarial 5: Alegação apenas tematicamente relacionada."""
    text = "Debates acadêmicos sobre pesquisas de vitamina D e saúde preventiva geral"
    match = brazilian_fact_matcher.find_match(text, threshold=0.15)
    if match:
        assert match["relation"] == "contextualizes"


def test_adversarial_absence_of_evidence():
    """Cenário Adversarial 6: Ausência total de evidência (assunto sem correspondência)."""
    text = "O telescópio James Webb fotografou uma nova galáxia espiral distante a bilhões de anos-luz"
    match = brazilian_fact_matcher.find_match(text)
    assert match is None
