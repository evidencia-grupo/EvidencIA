import { expect, it } from "vitest";
import { isAnalysis } from "./response-validation";

const valid = {
  videoId: "video",
  analysisMode: "evidence_first",
  videoTitle: "Título do Vídeo",
  channelName: "Canal Científico",
  publishedAt: "2021-04-15T00:00:00Z",
  processingTimeMs: 200,
  limitations: [],
  claims: [
    {
      id: "clm-01",
      text: "Texto da alegação",
      temporalContext: { videoPublishedAt: "2021-04-15T00:00:00Z" },
      uncertainty: "supported",
      reflectionQuestions: ["Pergunta 1?", "Pergunta 2?", "Pergunta 3?"],
      evidence: [
        {
          sourceId: "src-01",
          relation: "supports",
          title: "Estudo formal",
          url: "https://example.org/paper",
          publisher: "Agência de Checagem",
          publishedAt: "2021-04-15T00:00:00Z",
          provenance: { dataset: "factchecksbr", indexedAt: "2026-01-01T00:00:00Z" },
        },
      ],
    },
  ],
};

it("aceita contrato evidence-first completo", () => {
  expect(isAnalysis(valid, "video")).toBe(true);
});

it("rejeita perguntas reflexivas inválidas", () => {
  const invalidQuestionSets: unknown[] = [
    ["Pergunta 1?"],
    ["Pergunta 1?", "Pergunta 2?", ""],
    ["Pergunta 1?", "Pergunta 2?", 3],
  ];
  for (const reflectionQuestions of invalidQuestionSets) {
    const invalid = {
      ...valid,
      claims: [{ ...valid.claims[0], reflectionQuestions }],
    };
    expect(isAnalysis(invalid, "video")).toBe(false);
  }
});

it.each([
  null,
  {},
  { ...valid, videoId: "other" },
  { ...valid, videoTitle: "" },
  { ...valid, channelName: "" },
  { ...valid, publishedAt: "bad-date" },
  { ...valid, processingTimeMs: -1 },
  { ...valid, analysisMode: "invalid_mode" },
  { ...valid, claims: null },
  { ...valid, claims: [null] },
  { ...valid, claims: [{ ...valid.claims[0], uncertainty: "invalid_uncertainty" }] },
])("rejeita contrato inválido %s", (input) => {
  expect(isAnalysis(input, "video")).toBe(false);
});

it.each(["invalid-url", "http://example.org", "ftp://example.org"])(
  "rejeita URL não segura ou sem protocolo HTTPS: %s",
  (url) => {
    const invalidEvidence = {
      ...valid,
      claims: [
        {
          ...valid.claims[0],
          evidence: [{ ...valid.claims[0].evidence[0], url }],
        },
      ],
    };
    expect(isAnalysis(invalidEvidence, "video")).toBe(false);
  }
);
