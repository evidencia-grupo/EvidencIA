import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import List, Optional

from app.config import settings
from app.providers.factory import get_provider, ProviderUnavailableError
from app.providers.types import Claim as ProviderClaim, Evidence as ProviderEvidence
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    Claim,
    Evidence,
    TemporalContext,
    UncertaintyState,
)
from app.services.brazilian_fact_matcher import brazilian_fact_matcher
from app.services.fact_check_client import fact_check_client

logger = logging.getLogger(__name__)


class FactCheckerService:
    """
    Serviço orquestrador do pipeline de checagem factual Evidence-First (ADR-006).
    
    Princípios:
    - Evidence-First: Apresentação atômica de evidências auditáveis por alegação,
      sem scores agregados ou autoridade algorítmica.
    - Priorização de bases brasileiras curadas (FactChecks.br).
    - Estado explícito de evidência insuficiente (RF-12).
    - Degradação graciosa para modo Evidence-Only sob timeout ou falha de IA (RF-14, RNF-06).
    """

    @staticmethod
    def _build_temporal_context(upload_date: Optional[str]) -> TemporalContext:
        published_at = upload_date or datetime.now(timezone.utc).isoformat()
        note = None
        try:
            year = datetime.fromisoformat(published_at.replace("Z", "+00:00")).year
            current_year = datetime.now(timezone.utc).year
            if year < current_year:
                note = (
                    f"As alegações foram apresentadas em {year}; "
                    "mudanças posteriores não tornam falsa uma afirmação correta à época."
                )
        except Exception:
            pass

        return TemporalContext(
            claimDate=upload_date,
            videoPublishedAt=published_at,
            note=note,
        )

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        start_time = time.perf_counter()
        published_at = request.uploadDate or datetime.now(timezone.utc).isoformat()
        temporal_ctx = self._build_temporal_context(request.uploadDate)

        # 1. Obtenção do provedor via Factory (lança MockInProductionError se configurado indevidamente)
        provider = get_provider(
            provider_name=getattr(settings, "LLM_PROVIDER", None),
            app_env=getattr(settings, "APP_ENV", None),
        )

        analysis_mode = "evidence_first"
        limitations: List[str] = []
        provider_claims: List[ProviderClaim] = []

        # 2. Extração de alegações via LLM com timeout resiliente (RF-14, RNF-01, RNF-06)
        timeout_limit = getattr(settings, "LLM_TIMEOUT_SECONDS", 8.0)
        try:
            provider_claims = await asyncio.wait_for(
                provider.extract_claims(request.transcript, request.videoTitle),
                timeout=timeout_limit,
            )
        except (asyncio.TimeoutError, ProviderUnavailableError, Exception) as exc:
            logger.warning(f"Degradação para modo Evidence-Only acionada por falha/timeout no LLMProvider: {exc}")
            analysis_mode = "evidence_only"
            limitations.append(
                "Síntese e extração por IA temporariamente indisponíveis; "
                "operando em modo Evidence-Only a partir de bases de checagem curadas."
            )

        claims: List[Claim] = []

        # 3. Processamento no modo Evidence-First
        if analysis_mode == "evidence_first" and provider_claims:
            for idx, p_claim in enumerate(provider_claims):
                claim_id = p_claim.id or f"clm-{idx + 1:02d}"
                claim_text = p_claim.text
                evidence_list: List[Evidence] = []
                uncertainty: UncertaintyState = "insufficient_evidence"

                # Prioridade 1: Casamento direto com dataset curado FactChecks.br
                matched = brazilian_fact_matcher.find_match(claim_text)
                if matched and matched.get("evidence"):
                    evidence_list.append(matched["evidence"])
                    rel = matched.get("relation", "contextualizes")
                    if rel == "supports":
                        uncertainty = "supported"
                    elif rel == "contradicts":
                        uncertainty = "contradicted"
                    else:
                        uncertainty = "contextualized"
                else:
                    # Prioridade 2: Consulta à API externa de Fact Check
                    fc_results = await fact_check_client.search_claims(claim_text)
                    if fc_results and fc_results[0].get("source"):
                        item = fc_results[0]
                        src = item["source"]
                        status_str = item.get("status", "inconclusiva")
                        rel = (
                            "supports"
                            if status_str == "apoiada"
                            else ("contradicts" if status_str == "contraditada" else "contextualizes")
                        )
                        uncertainty = (
                            "supported"
                            if rel == "supports"
                            else ("contradicted" if rel == "contradicts" else "contextualized")
                        )
                        evidence_list.append(
                            Evidence(
                                sourceId=src.id,
                                relation=rel,
                                title=src.title,
                                url=src.url,
                                publishedAt=src.publishedAt or published_at,
                                publisher=src.domain,
                                snippet=item.get("evidence_summary"),
                                provenance={
                                    "dataset": "google_fact_check",
                                    "indexedAt": datetime.now(timezone.utc).isoformat(),
                                },
                            )
                        )
                    else:
                        # Prioridade 3: Estado explícito de evidência insuficiente (RF-12, ADR-006)
                        evidence_list = []
                        uncertainty = "insufficient_evidence"

                claims.append(
                    Claim(
                        id=claim_id,
                        text=claim_text,
                        temporalContext=temporal_ctx,
                        evidence=evidence_list,
                        uncertainty=uncertainty,
                        reflectionQuestions=[],
                    )
                )

            # 4. Geração de perguntas reflexivas não-dogmáticas via LLMProvider (HU15)
            try:
                all_evidence_refs: List[ProviderEvidence] = []
                reflections = await provider.generate_reflection(provider_claims, all_evidence_refs)
                if reflections:
                    for claim in claims:
                        claim.reflectionQuestions = reflections
            except Exception as ref_exc:
                logger.debug(f"Perguntas reflexivas não geradas: {ref_exc}")

        # 5. Processamento no modo Evidence-Only (Fallback sem LLM)
        else:
            analysis_mode = "evidence_only"
            matched = brazilian_fact_matcher.find_match(request.transcript)
            if not matched:
                matched = brazilian_fact_matcher.find_match(request.videoTitle)

            if matched and matched.get("evidence"):
                evidence_list = [matched["evidence"]]
                rel = matched.get("relation", "contextualizes")
                uncertainty = (
                    "supported"
                    if rel == "supports"
                    else ("contradicted" if rel == "contradicts" else "contextualized")
                )
                claims.append(
                    Claim(
                        id="clm-01",
                        text=matched.get("claim", request.videoTitle),
                        temporalContext=temporal_ctx,
                        evidence=evidence_list,
                        uncertainty=uncertainty,
                        reflectionQuestions=[],
                    )
                )
            else:
                claims.append(
                    Claim(
                        id="clm-01",
                        text=f"Afirmação do vídeo: {request.videoTitle}",
                        temporalContext=temporal_ctx,
                        evidence=[],
                        uncertainty="insufficient_evidence",
                        reflectionQuestions=[],
                    )
                )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return AnalyzeResponse(
            videoId=request.videoId,
            analysisMode=analysis_mode,
            videoTitle=request.videoTitle,
            channelName=request.channelName,
            publishedAt=published_at,
            processingTimeMs=elapsed_ms,
            claims=claims,
            limitations=limitations,
        )


fact_checker_service = FactCheckerService()
