from fastapi.testclient import TestClient
from app.main import app
from app.services.synthesis import FORBIDDEN_JARGONS, synthesis_service

client = TestClient(app)


class DummyClaim:
    def __init__(self, id, text, status, evidenceSummary="", confidence=0.9):
        self.id = id
        self.text = text
        self.status = status
        self.evidenceSummary = evidenceSummary
        self.confidence = confidence


def test_summary_avoids_technical_jargon():
    """
    A síntese não deve conter termos herméticos ou jargões técnicos,
    assegurando compreensão imediata e acessibilidade.
    """
    dummy_claims = [
        DummyClaim(
            id="clm-01",
            text="Alegação de teste",
            status="contraditada",
            evidenceSummary="Resumo de teste",
            confidence=0.9,
        )
    ]

    summary = synthesis_service.generate_accessible_summary(claims=dummy_claims, video_title="Vídeo de Teste")
    assert len(summary) > 30
    for jargon in FORBIDDEN_JARGONS:
        assert jargon not in summary.lower()


def test_summary_guides_individual_investigation_without_global_verdict():
    claims = [DummyClaim(id="c1", text="Chá cura doença", status="contraditada")]
    summary = synthesis_service.generate_accessible_summary(claims)
    assert "separadamente" in summary
    assert "fontes, datas e perguntas" in summary
    assert "%" not in summary
    empty = synthesis_service.generate_accessible_summary([])
    assert "Não foram identificadas alegações checáveis" in empty


def test_claims_contain_explicit_status_for_ui_grouping():
    """
    As alegações devem conter separação nítida de incerteza/status
    para permitir agrupamento visual no painel lateral.
    """
    payload = {
        "videoId": "video-dona-lurdes",
        "videoTitle": "Dicas de Saúde da Semana",
        "channelName": "Saúde e Bem Estar",
        "transcript": "Olá amigas, hoje vamos falar sobre estudos recentes e dados comprovados sobre alimentação saudável.",
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "claims" in data
    assert len(data["claims"]) > 0

    valid_uncertainties = {"supported", "contradicted", "contextualized", "conflicting", "insufficient_evidence"}
    for claim in data["claims"]:
        assert claim["uncertainty"] in valid_uncertainties


def test_public_access_no_registration_required():
    """
    A consulta não deve exigir configurações complexas,
    preenchimento de cadastros ou autenticação externa.
    """
    payload = {
        "videoId": "public-video-test",
        "videoTitle": "Notícia Geral",
        "channelName": "Notícias Abertas",
        "transcript": "Esta é uma transcrição pública para verificar se a API funciona sem qualquer login ou token do usuário.",
    }
    # Requisição intencionalmente sem cabeçalho Authorization ou Cookie
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
