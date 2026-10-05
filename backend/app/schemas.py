from typing import List, Literal, Optional, Dict
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
    provenance: EvidenceProvenance = Field(..., description="Metadados de auditoria e proveniência")


class Claim(BaseModel):
    id: str = Field(..., description="Identificador único da alegação")
    text: str = Field(..., min_length=1, description="Texto da alegação extraída")
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
