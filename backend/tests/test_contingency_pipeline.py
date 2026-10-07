"""Testes do Plano de Contingência Multinível e Aprofundamento do Machine Learning.

Valida a resiliência do sistema perante falhas simultâneas de:
- Provedores de LLM (Ollama / Remote API);
- APIs externas de Fact Check (Google Fact Check Tools API);
- Extração de alegações por ML no modo offline.
"""

import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from app.config import settings
from app.providers.types import ProviderUnavailableError
from app.schemas import AnalyzeRequest, ClassifyRequest
from app.services.classifier_service import classifier_service
from app.services.fact_checker import FactCheckerService
from ml.classifier.claim_extractor import extract_candidate_claims, score_claim_saliency
from ml.classifier.features import explain_linguistic_triggers


def test_offline_claim_extractor_filters_youtube_fillers():
    """O extrator offline deve descartar saudações e pedidos de inscrição/like do YouTube."""
    transcript = (
        "Olá pessoal, sejam muito bem-vindos a mais um vídeo do nosso canal! "
        "Não se esqueça de deixar o seu like e se inscrever no canal agora mesmo. "
        "O Ministério da Saúde anunciou vacinação obrigatória contra a dengue nas capitais. "
        "Circula boato de que o chá de casca de banana cura diabetes e zera glicose em três dias. "
        "Deixe seu comentário abaixo e até a próxima pessoal!"
    )
    claims = extract_candidate_claims(transcript, max_claims=3)

    assert len(claims) >= 1
    # Nenhuma frase extraída pode ser ruído de call-to-action
    for c in claims:
        assert "deixe o seu like" not in c.lower()
        assert "sejam muito bem-vindos" not in c.lower()
        assert "inscrever no canal" not in c.lower()

    # Deve ter identificado a alegação factual
    assert any("cura diabetes" in c.lower() or "ministério da saúde" in c.lower() for c in claims)


def test_offline_claim_extractor_saliency_scoring():
    """Sentenças factuais com verbos de asserção pontuam acima de frases neutras."""
    factual = "A Anvisa aprovou o registro da vacina contra a dengue após estudos clínicos."
    filler = "Muito obrigado por assistir este vídeo de hoje com a gente."

    score_factual = score_claim_saliency(factual)
    score_filler = score_claim_saliency(filler)

    assert score_factual > 0.60
    assert score_filler < 0.20


def test_linguistic_triggers_explanation():
    """Valida a detecção e explicação de gatilhos linguísticos em textos desinformativos e institucionais."""
    sensational_text = "URGENTE!! BOMBA!! REMÉDIO MILAGROSO CURA TODAS AS DOENÇAS E ELES ESTÃO ESCONDENDO DE VOCÊ!!!"
    triggers_sensational = explain_linguistic_triggers(sensational_text)

    assert len(triggers_sensational) > 0
    assert any("sensacionalismo" in t.lower() for t in triggers_sensational)
    assert any("maiúsculas" in t.lower() for t in triggers_sensational)

    credible_text = "Segundo relatório oficial da Fiocruz e dados do Ministério da Saúde publicados nesta semana."
    triggers_credible = explain_linguistic_triggers(credible_text)

    assert len(triggers_credible) > 0
    assert any("institucionais" in t.lower() for t in triggers_credible)


@pytest.mark.asyncio
async def test_full_contingency_when_llm_and_google_api_fail(monkeypatch):
    """Cenário de contingência crítica: LLM em timeout/erro e Google Fact Check indisponível."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")

    service = FactCheckerService()
    req = AnalyzeRequest(
        videoId="video-contingency-test",
        videoTitle="Notícia urgente sobre economia e vacina",
        channelName="Notícias Rápidas",
        transcript=(
            "Atenção para as notícias de hoje. "
            "Banco Central anunciou cobrança de taxa de quinze por cento sobre transferências via Pix entre pessoas físicas. "
            "Além disso o chá de casca de banana cura diabetes em três dias sem insulina segundo médico. "
            "Acompanhe os detalhes e compartilhe com todos."
        ),
        durationSeconds=180,
    )

    with (
        patch(
            "app.providers.mock.MockProvider.extract_claims",
            new_callable=AsyncMock,
            side_effect=ProviderUnavailableError("Provedor LLM fora do ar"),
        ),
        patch(
            "app.services.fact_check_client.FactCheckClient.search_claims",
            new_callable=AsyncMock,
            return_value=[],  # Simula Google Fact Check indisponível / 403
        ),
    ):
        response = await service.analyze(req)

        # O backend não quebra e responde em modo de contingência Evidence-Only
        assert response.analysisMode == "evidence_only"
        assert response.videoId == req.videoId
        assert len(response.claims) > 0

        # Verifica se as alegações foram extraídas e avaliadas
        claim_texts = [c.text for c in response.claims]
        assert any("pix" in t.lower() or "banana" in t.lower() or "notícia" in t.lower() for t in claim_texts)

        # Perguntas de reflexão presentes mesmo sem IA
        for c in response.claims:
            assert len(c.reflectionQuestions) == 3


def test_classifier_service_heuristic_reasons_and_tone():
    """Classificador supervisionado enriquece a resposta com razões heurísticas e tom epistêmico."""
    result = classifier_service.classify(
        "URGENTE: BOMBA! VENENO MORTAL NAS VACINAS FOI REVELADO E PROIBIDO NO MUNDO INTEIRO!!!"
    )

    assert result["label"] in ["fake", "unverified"]
    assert len(result["heuristic_reasons"]) > 0
    assert result["epistemic_tone"] == "sensational_dogmatic"
