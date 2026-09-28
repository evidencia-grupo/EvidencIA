import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.fact_check_client import FactCheckClient, normalize_rating_to_status

client = TestClient(app)


def test_hu04_claim_extraction_isolated_listing():
    """
    Critério HU04: As alegações extraídas pela IA devem ser listadas isoladamente,
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
    assert len(claims) >= 2, "Deveriam ser extraídas múltiplas alegações atômicas da transcrição"

    claim_ids = set()
    for claim in claims:
        # Cada alegação deve ser isolada com ID único
        assert claim["id"] not in claim_ids
        claim_ids.add(claim["id"])

        assert len(claim["text"]) > 10
        assert claim["status"] in ["apoiada", "contraditada", "inconclusiva"]
        assert len(claim["evidenceSummary"]) > 20
        assert 0.0 <= claim["confidence"] <= 1.0


def test_hu04_non_dogmatic_verdicts():
    """
    Critério HU04: O sistema não deve impor vereditos dogmáticos,
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
        summary_lower = claim["evidenceSummary"].lower()
        # Vereditos dogmáticos agressivos proibidos; deve utilizar linguagem acadêmica e factual
        assert "óbvio" not in summary_lower
        assert "ridículo" not in summary_lower
        assert "absurdo" not in summary_lower


def test_hu04_fact_check_client_rating_normalization():
    """
    Testa a normalização de vereditos do padrão ClaimReview da Google Fact Check API
    para o enum ClaimVerificationStatus do EvidencIA.
    """
    assert normalize_rating_to_status("Falso") == "contraditada"
    assert normalize_rating_to_status("Mentira") == "contraditada"
    assert normalize_rating_to_status("Enganoso") == "contraditada"

    assert normalize_rating_to_status("Verdadeiro") == "apoiada"
    assert normalize_rating_to_status("Fato") == "apoiada"
    assert normalize_rating_to_status("Comprovado") == "apoiada"

    assert normalize_rating_to_status("Distorcido") == "inconclusiva"
    assert normalize_rating_to_status("Fora de contexto") == "inconclusiva"
    assert normalize_rating_to_status("Exagerado") == "inconclusiva"
    assert normalize_rating_to_status("Sem comprovação") == "inconclusiva"


def test_hu04_fact_check_client_parsing():
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
            }
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
    assert source.reliabilityScore >= 0.95
    assert source.url == "https://lupa.uol.com.br/verificacao/cha-boldo"


@pytest.mark.asyncio
async def test_hu04_fact_check_client_offline_resilience():
    """
    Garante que a ausência de chave de API externa não causa exceção
    e degrada com segurança em modo offline.
    """
    offline_client = FactCheckClient(api_key=None)
    results = await offline_client.search_claims("Qualquer afirmação")
    assert results == []
