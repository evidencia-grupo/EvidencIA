from fastapi.testclient import TestClient
from app.main import app
from app.services.synthesis import FORBIDDEN_JARGONS, synthesis_service
from app.schemas import VerificationClaim

client = TestClient(app)


def test_hu02_summary_no_technical_jargon():
    """
    Critério HU02 / RF-03: A síntese não deve conter termos herméticos ou jargões técnicos,
    assegurando compreensão imediata pela persona Dona Lurdes.
    """
    dummy_claims = [
        VerificationClaim(
            id="clm-01",
            text="Alegação de teste",
            status="contraditada",
            evidenceSummary="Resumo de teste",
            confidence=0.9,
        )
    ]

    for classification in ["verdadeiro", "moderado", "falso", "inconclusivo"]:
        summary = synthesis_service.generate_accessible_summary(
            claims=dummy_claims,
            classification=classification,  # type: ignore
            score=50,
            video_title="Vídeo de Teste",
        )

        assert len(summary) > 30
        summary_lower = summary.lower()
        for jargon in FORBIDDEN_JARGONS:
            assert jargon not in summary_lower, f"Jargão técnico '{jargon}' encontrado na síntese: {summary}"


def test_hu02_summary_guidance_for_dona_lurdes():
    """
    Critério HU02: A síntese deve fornecer orientação clara sobre segurança
    e recomendação de compartilhamento sem sobrecarga cognitiva.
    """
    falso_claims = [
        VerificationClaim(
            id="c1",
            text="Chá cura doença",
            status="contraditada",
            evidenceSummary="Estudos desmentem",
            confidence=0.95,
        )
    ]
    summary_falso = synthesis_service.generate_accessible_summary(
        claims=falso_claims,
        classification="falso",
        score=20,
    )
    assert "não são verdadeiras" in summary_falso or "desmentidas" in summary_falso
    assert "não repassar" in summary_falso

    verdadeiro_claims = [
        VerificationClaim(
            id="c2",
            text="Vacina reduz internações",
            status="apoiada",
            evidenceSummary="Dados comprovam",
            confidence=0.98,
        )
    ]
    summary_verdadeiro = synthesis_service.generate_accessible_summary(
        claims=verdadeiro_claims,
        classification="verdadeiro",
        score=90,
    )
    assert "corretas" in summary_verdadeiro or "seguras" in summary_verdadeiro


def test_hu02_claims_contain_explicit_status_for_ui_grouping():
    """
    Critério HU02: As alegações devem conter separação nítida de status
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

    assert "summary" in data
    assert len(data["summary"]) > 0
    assert "claims" in data
    assert len(data["claims"]) > 0

    valid_statuses = {"apoiada", "contraditada", "inconclusiva"}
    for claim in data["claims"]:
        assert claim["status"] in valid_statuses


def test_hu02_public_access_no_registration_required():
    """
    Critério HU02: A consulta não deve exigir configurações complexas,
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
