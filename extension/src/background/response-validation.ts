import type { AnalyzeResponse } from "../../../shared/types/api";

function isHttps(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && !url.username && !url.password;
  } catch {
    return false;
  }
}

/** Valida dados externos sob o contrato Evidence-First (ADR-006). */
export function isAnalysis(value: unknown, videoId: string): value is AnalyzeResponse {
  if (!value || typeof value !== "object") return false;
  const data = value as AnalyzeResponse;

  return (
    data.videoId === videoId &&
    (data.analysisMode === "evidence_first" || data.analysisMode === "evidence_only") &&
    typeof data.videoTitle === "string" &&
    data.videoTitle.trim().length > 0 &&
    typeof data.channelName === "string" &&
    data.channelName.trim().length > 0 &&
    typeof data.publishedAt === "string" &&
    Number.isFinite(Date.parse(data.publishedAt)) &&
    Number.isFinite(data.processingTimeMs) &&
    data.processingTimeMs >= 0 &&
    Array.isArray(data.limitations) &&
    Array.isArray(data.claims) &&
    data.claims.every(
      (claim) =>
        claim &&
        typeof claim.id === "string" &&
        claim.id.trim().length > 0 &&
        typeof claim.text === "string" &&
        claim.text.trim().length > 0 &&
        (claim.reflectionQuestions === undefined ||
          (Array.isArray(claim.reflectionQuestions) &&
            claim.reflectionQuestions.length === 3 &&
            claim.reflectionQuestions.every((question) => typeof question === "string" && question.trim().length > 0))) &&
        Boolean(claim.temporalContext) &&
        typeof claim.temporalContext.videoPublishedAt === "string" &&
        [
          "supported",
          "contradicted",
          "contextualized",
          "conflicting",
          "insufficient_evidence",
        ].includes(claim.uncertainty) &&
        Array.isArray(claim.evidence) &&
        claim.evidence.every(
          (ev) =>
            ev &&
            typeof ev.sourceId === "string" &&
            ["supports", "contradicts", "contextualizes"].includes(ev.relation) &&
            typeof ev.title === "string" &&
            typeof ev.url === "string" &&
            isHttps(ev.url) &&
            typeof ev.publisher === "string" &&
            typeof ev.publishedAt === "string" &&
            Boolean(ev.provenance) &&
            typeof ev.provenance.dataset === "string"
        )
    )
  );
}
