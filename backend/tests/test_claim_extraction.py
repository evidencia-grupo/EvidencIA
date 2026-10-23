from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.schemas import AnalyzeRequest
from app.services.fact_check_client import (
    FactCheckClient,
    extract_domain_from_url,
    normalize_rating_to_status,
)
from app.services.fact_checker import FactCheckerService
from ml.classifier.claim_extractor import extract_candidate_claims, score_claim_saliency

client = TestClient(app)


def test_claim_extraction_isolated_listing():
    """
    As alegações extraídas pela IA devem ser listadas isoladamente,
    com identificador único, texto individual e relação explícita com as evidências.
    """
    payload = {
        "videoId": "vid-amanda-biologia",
        "videoTitle": "Descobertas Recentes sobre Vacinas de RNA",
        "channelName": "Biologia Aplicada",
        "transcript": (
            "Olá pessoal, bem-vindos ao canal! "
            "Hoje vamos mostrar que o novo estudo publicado comprovou a eficácia da vacina em ensaios clínicos controlados. "
            "Por outro lado, circulam boatos de que essa vacina causa cura milagrosa em 3 dias sem remédio. "
            "Existem também estudos preliminares em debate sobre a duração dos anticorpos na população."
        ),
        "language": "pt-BR",
    }

    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    claims = data["claims"]
    assert len(claims) >= 1, "Deveriam ser extraídas alegações atômicas da transcrição"

    claim_ids = set()
    for claim in claims:
        assert claim["id"] not in claim_ids
        claim_ids.add(claim["id"])

        assert len(claim["text"]) > 10
        assert claim["uncertainty"] in ["supported", "contradicted", "contextualized", "conflicting", "insufficient_evidence"]


def test_claim_extraction_non_dogmatic_verdicts():
    """
    O sistema não deve impor vereditos dogmáticos,
    mantendo foco na apresentação factual e analítica para fichamento acadêmico.
    """
    payload = {
        "videoId": "vid-pesquisa-climatica",
        "videoTitle": "Análise Climática e Projeções do IPCC",
        "channelName": "Geografia Hoje",
        "transcript": (
            "Segundo dados oficiais e relatórios consolidados do IPCC, a temperatura média global subiu 1.1 graus. "
            "Entretanto, projeções sobre o impacto na agricultura local ainda são estudos preliminares com metodologias em debate."
        ),
    }

    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    for claim in data["claims"]:
        text_lower = claim["text"].lower()
        assert "óbvio" not in text_lower
        assert "ridículo" not in text_lower
        assert "absurdo" not in text_lower


def test_fact_check_client_rating_normalization():
    """
    Testa a normalização de vereditos do padrão ClaimReview da Google Fact Check API
    para o enum ClaimVerificationStatus do EvidencIA.
    """
    assert normalize_rating_to_status("Falso") == "contraditada"
    assert normalize_rating_to_status("Mentira") == "contraditada"
    assert normalize_rating_to_status("Enganoso") == "contraditada"
    assert normalize_rating_to_status("Inverídico") == "contraditada"

    assert normalize_rating_to_status("Verdadeiro") == "apoiada"
    assert normalize_rating_to_status("Fato") == "apoiada"
    assert normalize_rating_to_status("Comprovado") == "apoiada"

    assert normalize_rating_to_status("Distorcido") == "inconclusiva"
    assert normalize_rating_to_status("Fora de contexto") == "inconclusiva"
    assert normalize_rating_to_status("Exagerado") == "inconclusiva"
    assert normalize_rating_to_status("Sem comprovação") == "inconclusiva"
    assert normalize_rating_to_status("Desconhecido Qualquer") == "inconclusiva"


def test_extract_domain_from_url():
    """Testa extração de domínio a partir de URLs HTTP/HTTPS."""
    assert extract_domain_from_url("https://www.lupa.uol.com.br/checagem") == "lupa.uol.com.br"
    assert extract_domain_from_url("http://aosfatos.org/noticia") == "aosfatos.org"
    assert extract_domain_from_url("sem-protocolo") == "agenciachecagem.org"


def test_fact_check_client_parsing():
    """
    Testa a interpretação do payload estruturado da Google Fact Check Tools API.
    """
    sample_api_response = {
        "claims": [
            {
                "text": "O chá de boldo cura gastrite em 24 horas",
                "claimant": "Vídeos em redes sociais",
                "claimDate": "2026-05-10T00:00:00Z",
                "claimReview": [
                    {
                        "publisher": {
                            "name": "Agência Lupa",
                            "site": "lupa.uol.com.br",
                        },
                        "url": "https://lupa.uol.com.br/verificacao/cha-boldo",
                        "title": "É falso que chá de boldo cura gastrite em 24h",
                        "reviewDate": "2026-05-12T00:00:00Z",
                        "textualRating": "Falso",
                        "languageCode": "pt-BR",
                    }
                ],
            },
            {
                "text": "Alegação sem revisões indexadas",
                "claimReview": [],
            },
        ]
    }

    client_fc = FactCheckClient(api_key="mock_key")
    parsed = client_fc.parse_claims_response(sample_api_response)

    assert len(parsed) == 1
    item = parsed[0]
    assert item["claim_text"] == "O chá de boldo cura gastrite em 24 horas"
    assert item["status"] == "contraditada"
    assert "Agência Lupa" in item["evidence_summary"]

    source = item["source"]
    assert source.domain == "lupa.uol.com.br"
    assert source.url == "https://lupa.uol.com.br/verificacao/cha-boldo"


@pytest.mark.asyncio
async def test_fact_check_client_offline_resilience():
    """
    Garante que a ausência de chave de API externa não causa exceção
    e degrada com segurança em modo offline.
    """
    offline_client = FactCheckClient(api_key="")
    results = await offline_client.search_claims("Qualquer afirmação")
    assert results == []


@pytest.mark.asyncio
async def test_fact_check_client_search_network_success():
    """Valida requisição HTTP à API do Google Fact Check quando chave está presente."""
    mock_payload = {
        "claims": [
            {
                "text": "Vacina de RNA altera DNA humano",
                "claimReview": [
                    {
                        "publisher": {"name": "Aos Fatos", "site": "aosfatos.org"},
                        "url": "https://aosfatos.org/vacina",
                        "title": "Não é verdade que vacina altera DNA",
                        "textualRating": "Falso",
                    }
                ],
            }
        ]
    }

    from unittest.mock import MagicMock

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload
        mock_get.return_value = mock_resp

        client_fc = FactCheckClient(api_key="dummy_valid_key")
        res = await client_fc.search_claims("vacina rna altera dna")
        assert len(res) == 1
        assert res[0]["status"] == "contraditada"


@pytest.mark.asyncio
async def test_fact_check_client_search_error_handling():
    """Valida tratamento seguro de erros HTTP 500 ou exceções de rede."""
    from unittest.mock import MagicMock

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_get.return_value = mock_resp

        client_fc = FactCheckClient(api_key="dummy_valid_key")
        res = await client_fc.search_claims("termo")
        assert res == []

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=Exception("Connection timed out")):
        client_fc = FactCheckClient(api_key="dummy_valid_key")
        res = await client_fc.search_claims("termo")
        assert res == []


def test_brazilian_fact_matcher_heuristics():
    """Testa a correspondência semântica e lexical do BrazilianFactMatcher com checagens brasileiras."""
    from app.services.brazilian_fact_matcher import brazilian_fact_matcher

    match_contra = brazilian_fact_matcher.find_match("Chá de casca de banana cura diabetes e zera a glicose")
    assert match_contra is not None
    assert match_contra["relation"] == "contextualizes"
    assert match_contra["evidence"].publisher == "Agência Lupa"

    match_apoiada = brazilian_fact_matcher.find_match("Vacinas passam por três fases de ensaios clínicos prévios antes de aprovação")
    assert match_apoiada is not None
    assert match_apoiada["relation"] == "contextualizes"


@pytest.mark.asyncio
async def test_claim_extraction_execute_analysis_development_pipeline(monkeypatch):
    """Testa o pipeline completo de orquestração sob LLM_PROVIDER='mock'."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "mock")

    req = AnalyzeRequest(
        videoId="vid-dev-01",
        videoTitle="Estudos Clínicos e Descobertas",
        channelName="Ciência Hoje",
        transcript=(
            "Um novo estudo com dados oficiais comprovou a eficácia do tratamento em ensaios clínicos controlados. "
            "Por outro lado, boatos na internet afirmam que existe cura milagrosa em 3 dias sem remédio."
        ),
    )

    resp = await FactCheckerService().analyze(req)
    assert resp.videoId == "vid-dev-01"
    assert len(resp.claims) >= 1
    assert resp.analysisMode == "evidence_first"


TV_OPENINGS_AND_CTAS = [
    "Boa noite, está começando agora o seu telejornal.",
    "Bom dia, o programa está no ar e você fica conosco até o fim.",
    "Fique conosco porque depois do intervalo tem muito mais.",
    "Hoje vamos falar de saúde com o nosso convidado especial.",
    "Se inscreva no canal e ative o sininho para não perder nada.",
    "Deixe o seu like e compartilhe com os amigos da família.",
    "Fala pessoal, tudo certo com vocês nesta semana?",
]


@pytest.mark.parametrize("sentence", TV_OPENINGS_AND_CTAS)
def test_tv_openings_and_calls_to_action_have_zero_saliency(sentence):
    from app.providers.claim_saliency import score_claim_saliency as provider_saliency

    assert provider_saliency(sentence) == 0.0
    assert score_claim_saliency(sentence) == 0.0


def test_no_greeting_or_call_to_action_becomes_a_claim():
    transcript = " ".join(TV_OPENINGS_AND_CTAS) + (
        " O Ministério da Saúde anunciou que a vacina contra a dengue chegou a 2 milhões de doses aplicadas."
    )
    claims = extract_candidate_claims(transcript, max_claims=5)
    assert claims == ["O Ministério da Saúde anunciou que a vacina contra a dengue chegou a 2 milhões de doses aplicadas"]


def test_short_factual_claim_after_greeting_is_kept():
    from app.providers.claim_saliency import score_claim_saliency as provider_saliency

    assert provider_saliency("Boa noite, a Anvisa aprovou a vacina em 2023.") > 1.0


# DEMO-004: frases reais (OYrx2Du7nJY, GdrNq1NXKYI) que o extrator determinístico aceitava.
@pytest.mark.parametrize("sentence", [
    "Então, a partir de hoje, aqui no Bora Brasil, exibiremos semanalmente, toda semana, uma checagem exclusiva feita pela Lupa",
    "Tudo que for válido na vida real tem que ser na vida digital",
    "A saúde tem que ter conhecimento científico em todas as decisões",
    "Ou seja, um absurdo do absurdo negar a vacina para as crianças do país",
    "Eu acredito que a vacina é a melhor coisa que aconteceu para o Brasil",
])
def test_opinions_and_program_announcements_are_not_claims(sentence):
    from ml.classifier.claim_extractor import is_conversational_filler
    # O mesmo filtro descarta a frase quando ela vem do LLM.
    assert is_conversational_filler(sentence)
    assert not extract_candidate_claims(sentence + ".")


def test_factual_sentence_survives_opinion_filter():
    fact = "E temos laboratórios importantes como a Fiocruz e o Butantan produzindo vacinas no Brasil"
    assert extract_candidate_claims(fact + ".") == [fact]
