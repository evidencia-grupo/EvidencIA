import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Header, status
from typing import Optional

from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    HealthResponse,
    FeedbackRequest,
    FeedbackResponse,
    ClassifyRequest,
    ClassifyResponse,
)
from app.config import settings
from app.services.fact_checker import fact_checker_service
from app.services.classifier_service import classifier_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Fact-Checking"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Submete a transcrição do vídeo para análise de veracidade",
)
async def analyze_video(
    request: AnalyzeRequest,
    x_client_version: Optional[str] = Header(None, description="Versão da extensão cliente"),
):
    # Validação de payload mínimo útil (422 Unprocessable Entity para transcrições curtas)
    if len(request.transcript.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A transcrição enviada contém menos de 50 caracteres úteis para inferência.",
        )

    try:
        response = await fact_checker_service.analyze(request)
        return response
    except TimeoutError as te:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(te),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Falha ao consultar serviços upstream de IA e busca: {str(exc)}",
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verifica integridade do backend proxy e serviços conectados",
)
async def health_check():
    return HealthResponse(
        status="degraded",
        version="1.0.0",
        services={
            "llmConnector": "demo" if settings.LLM_PROVIDER == "mock" else "not_integrated",
            "searchConnector": "not_integrated",
            "cacheStore": "operational",
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Recebe avaliação voluntária e anônima de utilidade da análise (RF-10, RNF-05)",
)
async def submit_feedback(
    request: FeedbackRequest,
):
    """
    Registra avaliação anônima da utilidade das evidências e perguntas recebidas.
    Em estrito cumprimento à LGPD (RNF-05), nenhum dado pessoal identificável ou
    endereço IP de rastreamento é persistido.
    """
    logger.info(
        f"Feedback anônimo recebido: videoId={request.videoId}, rating={request.rating}, reason={request.reason}"
    )
    return FeedbackResponse(
        status="received",
        message="Feedback anônimo registrado com sucesso.",
    )


@router.post(
    "/classify",
    response_model=ClassifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Classifica o teor da alegação com modelo estatístico supervisionado",
)
async def classify_claim(request: ClassifyRequest):
    """
    Submete uma alegação ou sentença avulsa para classificação estatística supervisionada.
    Retorna as probabilidades calculadas, o score de confiança calibrado e a aceitação conforme o limiar.
    """
    result = classifier_service.classify(request.text, threshold=request.threshold)
    return ClassifyResponse(
        label=result["label"],
        dominant_label=result["dominant_label"],
        verdict_pt=result["verdict_pt"],
        confidence=result["confidence"],
        accepted=result["accepted"],
        threshold=result["threshold"],
        probabilities=result["probabilities"],
        top_features=[[feat, score] for feat, score in result["top_features"]],
    )

