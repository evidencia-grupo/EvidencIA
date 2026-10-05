from typing import List, Literal, Optional, Dict
from pydantic import BaseModel, Field

VerificationClassification = Literal["verdadeiro", "moderado", "falso", "inconclusivo"]
ClaimVerificationStatus = Literal["apoiada", "contraditada", "inconclusiva"]


class AnalyzeRequest(BaseModel):
    videoId: str = Field(..., min_length=1, description="Identificador do vídeo no YouTube")
    videoTitle: str = Field(..., min_length=1, description="Título do vídeo")
    channelName: str = Field(..., min_length=1, description="Nome do canal do YouTube")
    uploadDate: Optional[str] = Field(None, description="Data de publicação no formato ISO 8601")
    durationSeconds: Optional[int] = Field(None, ge=0, description="Duração do vídeo em segundos")
    transcript: str = Field(..., min_length=50, description="Texto higienizado da transcrição")
    language: Optional[str] = Field("pt-BR", description="Código do idioma")


class VerificationClaim(BaseModel):
    id: str = Field(..., description="Identificador único da alegação")
    text: str = Field(..., description="Texto da alegação extraída da fala")
    status: ClaimVerificationStatus = Field(..., description="Status de verificação factual")
    evidenceSummary: str = Field(..., description="Resumo das evidências consultadas")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Grau de certeza (0.0 a 1.0)")
    sourceIds: List[str] = Field(default_factory=list, description="IDs das fontes usadas na checagem")


class FactCheckingSource(BaseModel):
    id: str = Field(..., description="Identificador da fonte")
    title: str = Field(..., description="Título da fonte ou matéria")
    url: str = Field(..., description="Hiperligação completa com protocolo HTTPS")
    domain: str = Field(..., description="Domínio institucional da fonte")
    reliabilityScore: float = Field(..., ge=0.0, le=1.0, description="Índice de confiabilidade")
    publishedAt: Optional[str] = Field(None, description="Data de publicação original")


class TemporalContext(BaseModel):
    publicationYear: Optional[int] = Field(None, description="Ano original de publicação do vídeo")
    isOldContent: bool = Field(..., description="Indica se o vídeo foi publicado antes do ano atual")
    message: str = Field(..., description="Orientação para interpretar as alegações no contexto da publicação")


class AnalyzeResponse(BaseModel):
    analysisMode: Literal["demo", "live"]
    videoId: str
    videoTitle: str
    channelName: str
    uploadDate: Optional[str] = None
    temporalContext: TemporalContext
    analyzedAt: str
    score: int = Field(..., ge=0, le=100, description="Índice numérico de veracidade de 0 a 100")
    classification: VerificationClassification
    summary: str = Field(..., description="Síntese analítica em linguagem clara sem jargões")
    claims: List[VerificationClaim]
    sources: List[FactCheckingSource]
    reflectionQuestions: List[str] = Field(default_factory=list, description="Perguntas neutras para investigação pessoal")
    processingTimeMs: int


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    services: Dict[str, str]
    timestamp: str
