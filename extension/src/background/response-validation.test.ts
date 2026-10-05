import { expect, it } from "vitest";
import { isAnalysis } from "./response-validation";
const valid = { videoId: "video", videoTitle: "Título", channelName: "Canal", uploadDate: "2021-04-15T00:00:00Z", temporalContext: { publicationYear: 2021, isOldContent: true, message: "Contexto de 2021" }, analysisMode: "live", score: 50, classification: "moderado", summary: "Síntese", analyzedAt: "2026-09-28T00:00:00Z", processingTimeMs: 200, claims: [{ id: "a", text: "texto", evidenceSummary: "evidência", status: "apoiada", confidence: 0.7 }], sources: [{ id: "a", title: "Fonte", domain: "example.org", url: "https://example.org/paper", reliabilityScore: 0.9 }] };
it("aceita contrato completo", () => expect(isAnalysis(valid, "video")).toBe(true));
it("aceita três perguntas reflexivas válidas", () => expect(isAnalysis({ ...valid, reflectionQuestions: ["Pergunta 1?", "Pergunta 2?", "Pergunta 3?"] }, "video")).toBe(true));
it.each([null, ["Pergunta 1?"], ["Pergunta 1?", "Pergunta 2?", ""], ["Pergunta 1?", "Pergunta 2?", 3]])(
  "rejeita perguntas reflexivas inválidas %s",
  reflectionQuestions => expect(isAnalysis({ ...valid, reflectionQuestions }, "video")).toBe(false),
);
it.each([null, {}, { ...valid, videoId: "other" }, { ...valid, videoTitle: "" }, { ...valid, channelName: "" }, { ...valid, uploadDate: "bad" }, { ...valid, temporalContext: null }, { ...valid, score: 101 }, { ...valid, classification: "unknown" }, { ...valid, summary: " " }, { ...valid, analyzedAt: "bad" }, { ...valid, processingTimeMs: -1 }, { ...valid, analysisMode: undefined }, { ...valid, claims: null }, { ...valid, claims: [null] }, { ...valid, claims: [{ ...valid.claims[0], confidence: 2 }] }, { ...valid, sources: null }, { ...valid, sources: [null] }, { ...valid, sources: [{ ...valid.sources[0], url: "javascript:alert(1)" }] }, { ...valid, sources: [{ ...valid.sources[0], reliabilityScore: -1 }] }])("rejeita contrato inválido %s", input => expect(isAnalysis(input, "video")).toBe(false));

it.each(["invalid", "https://user:pass@example.org", "http://example.org"])("rejeita URL %s", url => {
  expect(isAnalysis({ ...valid, sources: [{ ...valid.sources[0], url }] }, "video")).toBe(false);
});
