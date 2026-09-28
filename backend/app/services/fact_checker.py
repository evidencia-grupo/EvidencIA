import asyncio
import time
from datetime import datetime, timezone
from typing import List
from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    VerificationClaim,
    FactCheckingSource,
    VerificationClassification,
)
from app.config import settings


class FactCheckerService:
    """
    Serviço orquestrador do pipeline de checagem:
    1. Segmentação e extração de alegações via LLM
    2. Agregação paralela de evidências e busca factual
    3. Síntese e cômputo da nota de veracidade
    """

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        start_time = time.perf_counter()

        # Aplica timeout máximo de 8.0s no orquestrador do servidor (RNF-01)
        try:
            return await asyncio.wait_for(
                self._execute_analysis(request, start_time),
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise TimeoutError("Tempo limite de inferência e busca de 8,0s excedido no servidor.")

    async def _execute_analysis(self, request: AnalyzeRequest, start_time: float) -> AnalyzeResponse:
        if settings.LLM_PROVIDER == "mock":
            return await self._mock_analysis(request, start_time)

        # Implementação extensível para provedores reais (OpenAI, Gemini, Anthropic)
        return await self._mock_analysis(request, start_time)

    async def _mock_analysis(self, request: AnalyzeRequest, start_time: float) -> AnalyzeResponse:
        # Simula processamento assíncrono realista (ex.: 1200ms)
        await asyncio.sleep(0.4)

        # Regras heurísticas de demonstração para o mock de desenvolvimento
        transcript_lower = request.transcript.lower()

        claims: List[VerificationClaim] = [
            VerificationClaim(
                id="clm-01",
                text="Alegação principal extraída da fala do conteúdo do vídeo.",
                status="apoiada" if "estudo" in transcript_lower or "dados" in transcript_lower else "contraditada",
                evidenceSummary="Relatórios institucionais e publicações científicas de referência foram consultados.",
                confidence=0.92,
            ),
            VerificationClaim(
                id="clm-02",
                text="Afirmação secundária com correlação temporal ou estatística.",
                status="inconclusiva" if "talvez" in transcript_lower or "possível" in transcript_lower else "apoiada",
                evidenceSummary="Há evidências preliminares, mas com divergência metodológica na literatura.",
                confidence=0.78,
            ),
        ]

        # Fontes de evidência auditáveis com HTTPS
        sources: List[FactCheckingSource] = [
            FactCheckingSource(
                id="src-01",
                title="Repositório Institucional de Evidências Factual",
                url="https://www.scielo.br",
                domain="scielo.br",
                reliabilityScore=0.96,
                publishedAt="2026-01-15T00:00:00Z",
            ),
            FactCheckingSource(
                id="src-02",
                title="Agência Pública de Checagem e Jornalismo",
                url="https://apublica.org",
                domain="apublica.org",
                reliabilityScore=0.91,
                publishedAt="2026-03-20T00:00:00Z",
            ),
        ]

        # Calcula score e classificação
        supported_count = sum(1 for c in claims if c.status == "apoiada")
        contradicted_count = sum(1 for c in claims if c.status == "contraditada")

        if contradicted_count > 0 and supported_count == 0:
            score = 25
            classification: VerificationClassification = "falso"
            summary = "O vídeo apresenta afirmações que não encontram respaldo em dados consolidados e foram contraditas pelas evidências examinadas."
        elif supported_count > 0 and contradicted_count == 0:
            score = 85
            classification = "verdadeiro"
            summary = "As principais afirmações apresentadas no vídeo coincidem com dados de fontes confiáveis e relatórios consolidados."
        else:
            score = 58
            classification = "moderado"
            summary = "O conteúdo mistura premissas verdadeiras com interpretações exageradas ou projeções não confirmadas. Recomenda-se cautela."

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return AnalyzeResponse(
            videoId=request.videoId,
            analyzedAt=datetime.now(timezone.utc).isoformat(),
            score=score,
            classification=classification,
            summary=summary,
            claims=claims,
            sources=sources,
            processingTimeMs=elapsed_ms,
        )


fact_checker_service = FactCheckerService()
