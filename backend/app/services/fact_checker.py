import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import List, Optional

from app.config import settings
from app.providers.base import LLMProvider
from app.providers.factory import get_provider
from app.services.evidence_retrieval import retrieve_evidence
from app.providers.types import Claim as ProviderClaim, EvidenceRef as ProviderEvidenceRef
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    Claim,
    Evidence,
    EvidenceProvenance,
    TemporalContext,
    UncertaintyState,
)
from app.services.brazilian_fact_matcher import brazilian_fact_matcher
from app.services.classifier_service import classifier_service
from app.services.fact_check_client import fact_check_client
from ml.classifier.claim_extractor import extract_candidate_claims

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

    FALLBACK_REFLECTION_QUESTIONS = [
        "Que evidências independentes poderiam ajudar a avaliar esta alegação?",
        "Quais aspectos das fontes, como autoria, data e método, vale a pena verificar?",
        "Que contexto ou evidência adicional ajudaria você a formar sua própria interpretação?",
    ]

    def __init__(self):
        self.provider: Optional[LLMProvider] = None

    def initialize_provider(self) -> None:
        self.provider = get_provider(settings.LLM_PROVIDER, settings.ENV or settings.ENVIRONMENT)

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

    @classmethod
    def _normalize_reflection_questions(cls, questions: Optional[List[str]]) -> List[str]:
        if not questions or len(questions) != 3:
            return cls.FALLBACK_REFLECTION_QUESTIONS.copy()

        forbidden_verdict = re.compile(r"\b(certo|errado|verdadeiro|falso|mentira|mentiroso|correto|incorreto)\b", re.IGNORECASE)
        normalized = [question.strip() for question in questions if isinstance(question, str)]
        if (
            len(normalized) == 3
            and all(question.endswith("?") and not forbidden_verdict.search(question) for question in normalized)
        ):
            return normalized
        return cls.FALLBACK_REFLECTION_QUESTIONS.copy()

    @staticmethod
    def _extract_snippet_and_timestamps(
        transcript: str,
        claim_text: str,
        duration_seconds: Optional[int],
    ) -> tuple[Optional[str], Optional[float], Optional[float]]:
        if not transcript or not claim_text:
            return None, None, None

        lower_transcript = transcript.lower()
        search_terms = re.findall(r"\b[a-zA-ZáéíóúãõçÁÉÍÓÚÃÕÇ]{4,}\b", claim_text.lower())
        pos = -1

        sub = claim_text[: min(30, len(claim_text))].lower()
        pos = lower_transcript.find(sub)
        if pos == -1 and search_terms:
            for term in search_terms:
                pos = lower_transcript.find(term)
                if pos != -1:
                    break

        if pos == -1:
            return None, None, None

        start_char = max(0, pos - 20)
        end_char = min(len(transcript), pos + len(claim_text) + 40)
        snippet = transcript[start_char:end_char].strip()

        t_start = None
        t_end = None
        if duration_seconds and duration_seconds > 0 and len(transcript) > 0:
            t_start = round((pos / len(transcript)) * duration_seconds, 1)
            t_end = round(min(duration_seconds, t_start + 15.0), 1)

        return snippet, t_start, t_end

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        start_time = time.perf_counter()
        published_at = request.uploadDate or datetime.now(timezone.utc).isoformat()
        temporal_ctx = self._build_temporal_context(request.uploadDate)

        # 1. Obtenção do provedor via Factory (lança MockInProductionError se configurado indevidamente)
        provider = get_provider(
            provider_name=getattr(settings, "LLM_PROVIDER", None),
            app_env=settings.ENV or settings.ENVIRONMENT,
        )

        analysis_mode = "evidence_first"
        limitations: List[str] = []
        provider_claims: List[ProviderClaim] = []

        # 2. Extração de alegações via LLM com timeout resiliente (RF-14, RNF-01, RNF-06)
        timeout_limit = settings.LLM_TIMEOUT_SECONDS
        llm_elapsed = 0.0
        llm_start = time.perf_counter()
        unavailable_message = (
            "Síntese de linguagem temporariamente indisponível; "
            "operando em modo Evidence-Only a partir de bases de checagem curadas."
        )
        try:
            provider_claims = await asyncio.wait_for(
                provider.extract_claims(request.transcript, request.videoTitle),
                timeout=timeout_limit,
            )
        except Exception as exc:
            logger.warning("llm_evidence_only: extração indisponível (%s)", type(exc).__name__)
            analysis_mode = "evidence_only"
            limitations.append(unavailable_message)
        finally:
            llm_elapsed += time.perf_counter() - llm_start

        claims: List[Claim] = []

        # 3. Processamento no modo Evidence-First
        if analysis_mode == "evidence_first":
            for idx, p_claim in enumerate(provider_claims):
                claim_id = f"clm-{idx + 1:02d}"
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
                        publisher_display = src.publisher or src.domain
                        evidence_list.append(
                            Evidence(
                                sourceId=src.id,
                                relation=rel,
                                title=src.title,
                                url=src.url,
                                publishedAt=src.publishedAt or published_at,
                                publisher=publisher_display,
                                snippet=item.get("evidence_summary"),
                                matchReason=f"Correspondência temática com a checagem apurada por {publisher_display}.",
                                provenance=EvidenceProvenance(
                                    dataset="google_fact_check",
                                    indexedAt=datetime.now(timezone.utc).isoformat(),
                                ),
                            )
                        )
                    else:
                        # Prioridade 3: Estado explícito de evidência insuficiente (RF-12, ADR-006)
                        evidence_list = []
                        uncertainty = "insufficient_evidence"
                        ml_diag = classifier_service.classify(claim_text)
                        if ml_diag.get("heuristic_reasons"):
                            reasons = "; ".join(ml_diag["heuristic_reasons"])
                            ml_note = f"Análise linguística (ML): {reasons}"
                            existing_note = temporal_ctx.note
                            temporal_ctx = TemporalContext(
                                claimDate=temporal_ctx.claimDate,
                                videoPublishedAt=temporal_ctx.videoPublishedAt,
                                note=f"{existing_note} | {ml_note}" if existing_note else ml_note,
                            )

                snippet, t_start, t_end = self._extract_snippet_and_timestamps(
                    request.transcript, claim_text, request.durationSeconds
                )

                claims.append(
                    Claim(
                        id=claim_id,
                        text=claim_text,
                        transcriptSnippet=snippet,
                        timestampStart=t_start,
                        timestampEnd=t_end,
                        temporalContext=temporal_ctx,
                        evidence=evidence_list,
                        uncertainty=uncertainty,
                        reflectionQuestions=[],
                    )
                )

            # Perguntas e evidências pertencem somente à alegação investigada.
            for p_claim, claim in zip(provider_claims, claims):
                evidence_refs = [
                    ProviderEvidenceRef(
                        evidence_id=item.sourceId,
                        claim_text=claim.text,
                        summary=item.snippet,
                        source_url=item.url,
                    )
                    for item in claim.evidence
                ]
                llm_start = time.perf_counter()
                try:
                    reflections = await asyncio.wait_for(
                        provider.generate_reflection([p_claim], evidence_refs),
                        timeout=max(0.0, timeout_limit - llm_elapsed),
                    )
                    claim.reflectionQuestions = self._normalize_reflection_questions(reflections)
                except Exception as ref_exc:
                    logger.warning("llm_evidence_only: reflexão indisponível (%s)", type(ref_exc).__name__)
                    analysis_mode = "evidence_only"
                    limitations.append(unavailable_message)
                    # Preserva todas as evidências já recuperadas e interrompe inferências.
                    break
                finally:
                    llm_elapsed += time.perf_counter() - llm_start

        # 5. Processamento no modo Evidence-Only (Fallback sem LLM)
        else:
            analysis_mode = "evidence_only"
            retrieved = await asyncio.to_thread(retrieve_evidence, request.transcript)
            for index, (text, evidence) in enumerate(retrieved):
                claims.append(Claim(
                    id=f"clm-{index + 1:02d}", text=text, temporalContext=temporal_ctx,
                    evidence=[evidence], uncertainty="contextualized", reflectionQuestions=[],
                ))
            matched = None if claims else brazilian_fact_matcher.find_match(request.transcript)
            if not claims and not matched:
                matched = brazilian_fact_matcher.find_match(request.videoTitle)

            if matched and matched.get("evidence"):
                evidence_list = [matched["evidence"]]
                rel = matched.get("relation", "contextualizes")
                uncertainty = (
                    "supported"
                    if rel == "supports"
                    else ("contradicted" if rel == "contradicts" else "contextualized")
                )
                # No modo Evidence-Only, ClaimCard SEMPRE representa o vídeo real (título/áudio),
                # NUNCA o claim_text da base de fact-checking externa.
                claims.append(
                    Claim(
                        id="clm-01",
                        text=request.videoTitle,
                        transcriptSnippet=request.transcript[:120].strip() if request.transcript else None,
                        timestampStart=0.0,
                        timestampEnd=min(15.0, float(request.durationSeconds or 15.0)),
                        temporalContext=temporal_ctx,
                        evidence=evidence_list,
                        uncertainty=uncertainty,
                        reflectionQuestions=[],
                    )
                )
            if not claims and not matched:
                # Contingência Nível 2: Extrator de Alegações por ML diretamente da transcrição
                candidate_claims = extract_candidate_claims(request.transcript, max_claims=3)
                for c_idx, candidate_text in enumerate(candidate_claims):
                    c_matched = brazilian_fact_matcher.find_match(candidate_text)
                    c_evidence = [c_matched["evidence"]] if c_matched and c_matched.get("evidence") else []
                    if c_matched and c_matched.get("evidence"):
                        c_rel = c_matched.get("relation", "contextualizes")
                        c_unc = "supported" if c_rel == "supports" else ("contradicted" if c_rel == "contradicts" else "contextualized")
                        c_temporal = temporal_ctx
                    else:
                        c_unc = "insufficient_evidence"
                        ml_diag = classifier_service.classify(candidate_text)
                        c_temporal = temporal_ctx
                        if ml_diag.get("heuristic_reasons"):
                            ml_note = f"Análise linguística (ML): {'; '.join(ml_diag['heuristic_reasons'])}"
                            c_temporal = TemporalContext(
                                claimDate=temporal_ctx.claimDate,
                                videoPublishedAt=temporal_ctx.videoPublishedAt,
                                note=f"{temporal_ctx.note} | {ml_note}" if temporal_ctx.note else ml_note,
                            )
                    c_snip, c_start, c_end = self._extract_snippet_and_timestamps(
                        request.transcript, candidate_text, request.durationSeconds
                    )
                    claims.append(
                        Claim(
                            id=f"clm-{c_idx + 1:02d}",
                            text=candidate_text,
                            transcriptSnippet=c_snip,
                            timestampStart=c_start,
                            timestampEnd=c_end,
                            temporalContext=c_temporal,
                            evidence=c_evidence,
                            uncertainty=c_unc,
                            reflectionQuestions=[],
                        )
                    )

            if not claims:
                limitations.append("Não foi possível identificar alegações verificáveis durante a falha de extração.")

        for claim in claims:
            if not claim.reflectionQuestions:
                claim.reflectionQuestions = self.FALLBACK_REFLECTION_QUESTIONS.copy()

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
