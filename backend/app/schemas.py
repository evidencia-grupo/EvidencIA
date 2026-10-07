from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

EvidenceRelation = Literal["supports", "contradicts", "contextualizes"]
UncertaintyState = Literal[
    "supported",
    "contradicted",
    "contextualized",
    "conflicting",
    "insufficient_evidence",
]


class EvidenceProvenance(BaseModel):
    dataset: str = Field(..., description="Nome do dataset de proveniência (ex.: factchecks-br)")
    indexedAt: str = Field(..., description="Data/hora de indexação da evidência")
    contentHash: Optional[str] = Field(None, description="Hash de integridade da evidência")


class TemporalContext(BaseModel):
    claimDate: Optional[str] = Field(None, description="Data estimada da alegação")
    videoPublishedAt: str = Field(..., description="Data de publicação original do vídeo")
    note: Optional[str] = Field(None, description="Orientação de contexto temporal")


class Evidence(BaseModel):
    sourceId: str = Field(..., description="Identificador único da evidência")
    relation: EvidenceRelation = Field(..., description="Relação factual com a alegação")
    title: str = Field(..., description="Título da checagem ou estudo")
    url: str = Field(..., description="Hiperligação completa com protocolo seguro")
    publishedAt: str = Field(..., description="Data de publicação original")
    publisher: str = Field(..., description="Instituição ou agência publicadora")
    snippet: Optional[str] = Field(None, description="Trecho textual relevante da checagem")
    matchReason: Optional[str] = Field(None, description="Explicação objetiva de por que a fonte foi recuperada")
    provenance: EvidenceProvenance = Field(..., description="Metadados de auditoria e proveniência")


class Claim(BaseModel):
    id: str = Field(..., description="Identificador único da alegação")
    text: str = Field(..., min_length=1, description="Texto da alegação extraída")
    transcriptSnippet: Optional[str] = Field(None, description="Trecho textual da transcrição onde a alegação ocorre")
    timestampStart: Optional[float] = Field(None, ge=0, description="Segundo de início no vídeo")
    timestampEnd: Optional[float] = Field(None, ge=0, description="Segundo de término no vídeo")
    temporalContext: TemporalContext = Field(..., description="Contexto temporal da alegação")
    evidence: List[Evidence] = Field(default_factory=list, description="Evidências relacionadas")
    uncertainty: UncertaintyState = Field(..., description="Estado de certeza analítica")
    reflectionQuestions: Optional[List[str]] = Field(default_factory=list, description="Perguntas orientadoras neutras")


class AnalyzeRequest(BaseModel):
    videoId: str = Field(..., min_length=1, description="Identificador do vídeo no YouTube")
    videoTitle: str = Field(..., min_length=1, description="Título do vídeo")
    channelName: str = Field(..., min_length=1, description="Nome do canal do YouTube")
    uploadDate: Optional[str] = Field(None, description="Data de publicação no formato ISO 8601")
    durationSeconds: Optional[int] = Field(None, ge=0, description="Duração do vídeo em segundos")
    transcript: str = Field(..., min_length=50, description="Texto higienizado da transcrição")
    language: Optional[str] = Field("pt-BR", description="Código do idioma")


class AnalyzeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    videoId: str
    analysisMode: Literal["evidence_first", "evidence_only"]
    videoTitle: str
    channelName: str
    publishedAt: str
    processingTimeMs: int
    claims: List[Claim]
    limitations: List[str] = Field(default_factory=list, description="Ressalvas metodológicas e limitações")


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    services: Dict[str, str]
    timestamp: str


FeedbackRating = Literal["positive", "negative"]
FeedbackReason = Literal["outdated_sources", "insufficient_evidence", "inaccurate", "other"]


class FeedbackRequest(BaseModel):
    videoId: str = Field(..., min_length=1, description="Identificador do vídeo avaliado")
    rating: FeedbackRating = Field(..., description="Classificação de relevância e utilidade da análise")
    reason: Optional[FeedbackReason] = Field(None, description="Motivo opcional da classificação")

    model_config = {
        "extra": "forbid",
    }


class FeedbackResponse(BaseModel):
    status: Literal["received"] = "received"
    message: str = "Feedback anônimo registrado com sucesso."


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Texto ou proposição a ser classificada")
    threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Limiar de aceitação (default: 0.65)")


class ClassifyResponse(BaseModel):
    label: str = Field(..., description="fake, true ou unverified")
    dominant_label: str = Field(..., description="fake ou true")
    verdict_pt: str = Field(..., description="Veredito textual em português")
    confidence: float = Field(..., description="Score de confiança [0.5, 1.0]")
    accepted: bool = Field(..., description="Se a confiança superou o limiar de aceitação")
    threshold: float = Field(..., description="Limiar adotado")
    probabilities: Dict[str, float] = Field(..., description="P(fake) e P(true)")
    top_features: List[List[Any]] = Field(default_factory=list, description="Features mais discriminativas")
    heuristic_reasons: List[str] = Field(default_factory=list, description="Gatilhos linguísticos identificados")
    epistemic_tone: str = Field("neutral", description="Tom epistêmico da alegação")


class AuthTokenRequest(BaseModel):
    installationId: str = Field(..., min_length=8, description="Identificador único anônimo da instalação da extensão")
    clientVersion: Optional[str] = Field("1.0.0", description="Versão do cliente da extensão")


class AuthTokenResponse(BaseModel):
    token: str = Field(..., description="Token de acesso efêmero (JWT/HMAC)")
    tokenType: str = Field("Bearer", description="Tipo do token de autenticação")
    expiresIn: int = Field(86400, description="Tempo de vida útil em segundos (24 horas)")


class LivenessResponse(BaseModel):
    status: Literal["alive"] = "alive"
    timestamp: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    components: Dict[str, str]
    timestamp: str


