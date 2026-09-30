/**
 * Contrato de Dados Oficial — EvidencIA Backend Proxy & Extension Client
 * Rastreabilidade: documentation/docs/tecnico/contrato-api.md
 */

export type VerificationClassification =
  | "verdadeiro"
  | "moderado"
  | "falso"
  | "inconclusivo";

export type ClaimVerificationStatus =
  | "apoiada"
  | "contraditada"
  | "inconclusiva";

export interface AnalyzeRequest {
  videoId: string;
  videoTitle: string;
  channelName: string;
  uploadDate?: string;
  durationSeconds?: number;
  transcript: string;
  language?: string;
}

export interface VerificationClaim {
  id: string;
  text: string;
  status: ClaimVerificationStatus;
  evidenceSummary: string;
  confidence: number;
}

export interface FactCheckingSource {
  id: string;
  title: string;
  url: string;
  domain: string;
  reliabilityScore: number;
  publishedAt?: string;
}

export interface TemporalContext {
  publicationYear?: number | null;
  isOldContent: boolean;
  message: string;
}

export interface AnalyzeResponse {
  analysisMode: "demo" | "live";
  videoId: string;
  videoTitle: string;
  channelName: string;
  uploadDate?: string | null;
  temporalContext: TemporalContext;
  analyzedAt: string;
  score: number; // 0 a 100
  classification: VerificationClassification;
  summary: string;
  claims: VerificationClaim[];
  sources: FactCheckingSource[];
  processingTimeMs: number;
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
