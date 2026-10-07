import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.config import settings
from app.limiter import limiter
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AuthTokenRequest,
    AuthTokenResponse,
    ClassifyRequest,
    ClassifyResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
)
from app.services.auth_service import auth_service, get_current_client
from app.services.classifier_service import classifier_service
from app.services.fact_checker import fact_checker_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Fact-Checking"])


@router.post(
    "/auth/token",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Emite credencial de acesso efêmera para instância da extensão",
)
@limiter.limit("30/minute")
async def issue_token(
    request: Request,
    body: AuthTokenRequest,
):
    token = auth_service.create_token(body.installationId)
    return AuthTokenResponse(
        token=token,
        tokenType="Bearer",
        expiresIn=auth_service.ttl_seconds,
    )


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Submete a transcrição do vídeo para análise de veracidade",
)
@limiter.limit(f"{settings.RATE_LIMIT_MAX_PER_MINUTE}/minute")
async def analyze_video(
    request: Request,
    payload: AnalyzeRequest,
    client: dict = Depends(get_current_client),
    x_client_version: Optional[str] = Header(None, description="Versão da extensão cliente"),
):
    # Validação de payload mínimo útil (422 Unprocessable Entity para transcrições curtas)
    if len(payload.transcript.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A transcrição enviada contém menos de 50 caracteres úteis para inferência.",
        )

    try:
        response = await fact_checker_service.analyze(payload)
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
    "/health/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe para monitoramento de processo ativo",
)
async def liveness_check():
    return LivenessResponse(
        status="alive",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe para validação de conectividade de subsistemas",
)
async def readiness_check():
    provider_status = "operational" if fact_checker_service.provider is not None else "not_ready"
    retrieval_status = "operational"
    classifier_status = "operational" if classifier_service.model is not None else "not_ready"
    is_ready = provider_status == "operational" and classifier_status == "operational"

    components = {
        "provider": provider_status,
        "retrieval": retrieval_status,
        "classifier": classifier_status,
    }
    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "components": components},
        )
    return ReadinessResponse(
        status="ready",
        components=components,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Verifica integridade do backend proxy e serviços conectados",
)
async def health_check():
    if fact_checker_service.provider is None:
        try:
            fact_checker_service.initialize_provider()
        except Exception:
            pass

    is_mock = settings.LLM_PROVIDER == "mock"
    overall_status = "degraded" if is_mock else ("operational" if fact_checker_service.provider else "down")
    llm_desc = "demo" if is_mock else ("operational" if fact_checker_service.provider else "not_initialized")

    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        services={
            "llmConnector": llm_desc,
            "searchConnector": "operational" if settings.GOOGLE_FACT_CHECK_API_KEY else "local_corpus_only",
            "cacheStore": "operational",
            "classifier": "operational",
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Recebe avaliação voluntária e anônima de utilidade da análise (RF-10, RNF-05)",
)
@limiter.limit(f"{settings.RATE_LIMIT_MAX_PER_MINUTE}/minute")
async def submit_feedback(
    request: Request,
    payload: FeedbackRequest,
    client: dict = Depends(get_current_client),
):
    """
    Registra avaliação anônima da utilidade das evidências e perguntas recebidas.
    Em estrito cumprimento à LGPD (RNF-05), nenhum dado pessoal identificável ou
    endereço IP de rastreamento é persistido.
    """
    logger.info(
        f"Feedback anônimo recebido: videoId={payload.videoId}, rating={payload.rating}, reason={payload.reason}"
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
@limiter.limit(f"{settings.RATE_LIMIT_MAX_PER_MINUTE}/minute")
async def classify_claim(
    request: Request,
    payload: ClassifyRequest,
    client: dict = Depends(get_current_client),
):
    """
    Submete uma alegação ou sentença avulsa para classificação estatística supervisionada.
    Retorna as probabilidades calculadas, o score de confiança calibrado e a aceitação conforme o limiar.
    """
    result = classifier_service.classify(payload.text, threshold=payload.threshold)
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


