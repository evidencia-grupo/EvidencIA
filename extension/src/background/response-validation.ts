import type { AnalyzeResponse } from "../../../shared/types/api";
/** Valida dados externos antes de persistir ou renderizar componentes. */
export function isAnalysis(value: unknown, videoId: string): value is AnalyzeResponse {
  if (!value || typeof value !== "object") return false;
  const data = value as AnalyzeResponse;
  return data.videoId === videoId && Number.isInteger(data.score) && data.score >= 0 && data.score <= 100
    && typeof data.videoTitle === "string" && data.videoTitle.trim().length > 0
    && typeof data.channelName === "string" && data.channelName.trim().length > 0
    && (data.uploadDate == null || Number.isFinite(Date.parse(data.uploadDate)))
    && Boolean(data.temporalContext) && typeof data.temporalContext.message === "string"
    && typeof data.temporalContext.isOldContent === "boolean"
    && (data.temporalContext.publicationYear == null || Number.isInteger(data.temporalContext.publicationYear))
    && ["verdadeiro", "moderado", "falso", "inconclusivo"].includes(data.classification)
    && typeof data.summary === "string" && data.summary.trim().length > 0
    && typeof data.analyzedAt === "string" && Number.isFinite(Date.parse(data.analyzedAt))
    && Number.isFinite(data.processingTimeMs) && data.processingTimeMs >= 0
    && (data.analysisMode === "demo" || data.analysisMode === "live")
    && Array.isArray(data.claims) && data.claims.every(claim => claim && typeof claim.id === "string"
      && typeof claim.text === "string" && typeof claim.evidenceSummary === "string"
      && ["apoiada", "contraditada", "inconclusiva"].includes(claim.status)
      && Number.isFinite(claim.confidence) && claim.confidence >= 0 && claim.confidence <= 1)
    && Array.isArray(data.sources) && data.sources.every(source => source && typeof source.id === "string"
      && typeof source.title === "string" && typeof source.domain === "string"
      && typeof source.url === "string" && isHttps(source.url)
      && Number.isFinite(source.reliabilityScore) && source.reliabilityScore >= 0 && source.reliabilityScore <= 1);
}

function isHttps(value: string): boolean {
  try { const url = new URL(value); return url.protocol === "https:" && !url.username && !url.password; }
  catch { return false; }
}
