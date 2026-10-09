import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import List, Optional

from app.config import settings
from app.providers.reflection_catalog import REFLECTION_QUESTIONS
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

    FALLBACK_REFLECTION_QUESTIONS = REFLECTION_QUESTIONS[:3]

    def __init__(self):
        self.provider: Optional[LLMProvider] = None

    def initialize_provider(self) -> None:
        self.provider = get_provider(settings.LLM_PROVIDER, settings.ENV or settings.ENVIRONMENT)

    @staticmethod
    def _build_temporal_context(upload_date: Optional[str]) -> TemporalContext:
        published_at = upload_date or ""
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

        normalized = [question.strip() for question in questions if isinstance(question, str)]
        if len(set(normalized)) == 3 and all(q in REFLECTION_QUESTIONS for q in normalized):
            return normalized
        return cls.FALLBACK_REFLECTION_QUESTIONS.copy()

    @staticmethod
    def _extract_snippet_and_timestamps(transcript, claim_text, duration_seconds=None, segments=None):
        # Character position is never converted into a video timestamp.
        def normalize(text):
            return " ".join(text.casefold().split()).strip(" .!?")
        target = normalize(claim_text)
        if not target or target not in normalize(transcript):
            return None, None, None
        if segments:
            # Use only an exact contiguous span of real caption segments.
            for index, segment in enumerate(segments):
                texts = []
                for last in segments[index:]:
                    texts.append(last.text)
                    joined = " ".join(texts)
                    if target in normalize(joined):
                        if target not in normalize(" ".join(texts[:-1])):
                            first = index
                            stop = index + len(texts)
                            while first + 1 < stop and target in normalize(" ".join(s.text for s in segments[first + 1:stop])):
                                first += 1
                            return " ".join(s.text for s in segments[first:stop]), segments[first].start, last.start + last.duration
                        break
                    if len(joined) > len(claim_text) + 1000:
                        break
        return claim_text, None, None

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        start_time = time.perf_counter()
        published_at = request.uploadDate or ""
        temporal_ctx = self._build_temporal_context(request.uploadDate)

        # 1. Obtenção do provedor via Factory (lança MockInProductionError se configurado indevidamente)
        provider = None if request.analysisMode == "evidence_only" else get_provider(
            provider_name=getattr(settings, "LLM_PROVIDER", None),
            app_env=settings.ENV or settings.ENVIRONMENT,
        )

        analysis_mode = request.analysisMode
        limitations: List[str] = []
        if provider is not None and provider.is_mock is True:
            limitations.append("Modo demonstração: extração determinística e amostras locais; não é checagem validada de produção.")
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
            if provider is not None:
                provider_claims = await asyncio.wait_for(
                    provider.extract_claims(request.transcript, request.videoTitle),
                    timeout=timeout_limit,
                )
                transcript_words = " ".join(request.transcript.casefold().split())
                grounded = [claim for claim in provider_claims
                            if claim.text.strip(" .!?").strip() and " ".join(claim.text.casefold().strip(" .!?").split()) in transcript_words]
                if len(grounded) != len(provider_claims):
                    limitations.append("Alegações sem trecho correspondente na transcrição foram descartadas.")
                provider_claims = grounded
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
                        # A search hit establishes relevance, not propositional equivalence.
                        status_str = "inconclusiva"
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
                                publishedAt=src.publishedAt or "",
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
                    request.transcript, claim_text, request.durationSeconds, request.segments
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
            candidate_claims = extract_candidate_claims(request.transcript, max_claims=3)
            if not candidate_claims:
                whole_match = None if retrieved else brazilian_fact_matcher.find_match(request.transcript)
                if retrieved or (whole_match and whole_match.get("evidence")):
                    candidate_claims = [request.transcript]
            for index, text in enumerate(candidate_claims):
                matched = None if retrieved else brazilian_fact_matcher.find_match(text)
                evidence_list = [evidence for _, evidence in retrieved]
                if not evidence_list and matched and matched.get("evidence"):
                    evidence_list = [matched["evidence"]]
                uncertainty = "insufficient_evidence"
                if evidence_list:
                    relation = evidence_list[0].relation
                    uncertainty = {"supports": "supported", "contradicts": "contradicted"}.get(relation, "contextualized")
                snippet, t_start, t_end = self._extract_snippet_and_timestamps(
                    request.transcript, text, request.durationSeconds, request.segments
                )
                claims.append(Claim(
                    id=f"clm-{index + 1:02d}", text=text, transcriptSnippet=snippet,
                    timestampStart=t_start, timestampEnd=t_end, temporalContext=temporal_ctx,
                    evidence=evidence_list, uncertainty=uncertainty, reflectionQuestions=[],
                ))
            if not claims:
                limitations.append("Não foi possível identificar alegações verificáveis sem inferência de linguagem.")

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
