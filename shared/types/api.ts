/**
 * Contrato de Dados Oficial — EvidencIA Backend Proxy & Extension Client
 * Arquitetura Evidence-First (ADR-006)
 * Rastreabilidade: documentation/docs/arquitetura/contrato-api.md (RF-06, RF-12, RF-13, RF-14)
 */

export interface AnalyzeRequest {
  videoId: string;
  videoTitle: string;
  channelName: string;
  uploadDate?: string;
  durationSeconds?: number;
  transcript: string;
  language?: string;
}

export type EvidenceRelation = "supports" | "contradicts" | "contextualizes";

export type UncertaintyState =
  | "supported"
  | "contradicted"
  | "contextualized"
  | "conflicting"
  | "insufficient_evidence";

export interface EvidenceProvenance {
  dataset: string;
  indexedAt: string;
  contentHash?: string;
}

export interface TemporalContext {
  claimDate?: string;
  videoPublishedAt: string;
  note?: string;
}

export interface Evidence {
  sourceId: string;
  relation: EvidenceRelation;
  title: string;
  url: string;
  publishedAt: string;
  publisher: string;
  snippet?: string;
  matchReason?: string;
  provenance: EvidenceProvenance;
}

export interface Claim {
  id: string;
  text: string;
  transcriptSnippet?: string;
  timestampStart?: number;
  timestampEnd?: number;
  temporalContext: TemporalContext;
  evidence: Evidence[];
  uncertainty: UncertaintyState;
  reflectionQuestions?: string[];
}

export interface AnalyzeResponse {
  videoId: string;
  analysisMode: "evidence_first" | "evidence_only";
  videoTitle: string;
  channelName: string;
  publishedAt: string;
  processingTimeMs: number;
  claims: Claim[];
  limitations: string[];
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  services: {
    llmConnector: string;
    searchConnector: string;
    cacheStore: string;
    [key: string]: string;
  };
  timestamp: string;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  field?: string;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: ApiErrorDetail[];
    timestamp: string;
  };
}

/**
 * Estrutura de persistência do cache local (chrome.storage.local)
 * Rastreabilidade: ADR-003 e RNF-01 / RNF-05
 */
export interface LocalCacheEntry extends AnalyzeResponse {
  timestamp: number;
  ttl: number; // Padrão: 86400000 ms (24h)
}

export type FeedbackRating = "positive" | "negative";

export type FeedbackReason =
  | "outdated_sources"
  | "insufficient_evidence"
  | "inaccurate"
  | "other";

export interface FeedbackRequest {
  videoId: string;
  rating: FeedbackRating;
  reason?: FeedbackReason;
}

export interface FeedbackResponse {
  status: "received";
  message: string;
}

