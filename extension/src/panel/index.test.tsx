// @vitest-environment jsdom
import { beforeEach, afterEach, expect, it, vi } from "vitest";
import { render } from "preact";
import { act } from "preact/test-utils";
import type { AnalyzeResponse } from "../../../shared/types/api";

let App: typeof import("./index").App;

const data: AnalyzeResponse = {
  videoId: "video",
  videoTitle: "Vídeo histórico",
  channelName: "Canal de teste",
  publishedAt: "2021-04-15T00:00:00Z",
  analysisMode: "evidence_first",
  processingTimeMs: 20,
  limitations: [],
  claims: [
    {
      id: "clm-01",
      text: "Alegação de teste",
      uncertainty: "supported",
          reflectionQuestions: [
            "Que evidências ajudam a avaliar esta alegação?",
            "Quais fontes independentes podem ser consultadas?",
            "Que contexto adicional pode ser relevante?",
          ],
      temporalContext: { videoPublishedAt: "2021-04-15T00:00:00Z", note: "Contexto de 2021" },
      evidence: [
        {
          sourceId: "src-01",
          relation: "supports",
          title: "Fonte de teste",
          url: "https://example.org/paper",
          publisher: "Agência Teste",
          publishedAt: "2021-04-15T00:00:00Z",
          snippet: "Trecho comprobatório de teste",
          provenance: { dataset: "factchecksbr", indexedAt: "2026-01-01T00:00:00Z" },
        },
      ],
    },
  ],
};

function message(msg: unknown, origin = "https://www.youtube.com", source: MessageEventSource | null = window.parent) {
  act(() => { window.dispatchEvent(new MessageEvent("message", { data: msg, origin, source })); });
}

beforeEach(async () => {
  document.body.innerHTML = '<div id="app"></div>';
  ({ App } = await import("./index"));
  act(() => render(<App />, document.getElementById("app")!));
});

afterEach(() => act(() => render(null, document.getElementById("app")!)));

it("sincroniza início, sucesso, erros e limpa resultado anterior", () => {
  expect(document.body.textContent).toContain("para iniciar");
  message({ type: "ANALYSIS_START" });
  expect(document.querySelector('[role="status"]')?.textContent).toContain("analisando as alegações");
  message({ type: "ANALYSIS_SUCCESS", data });
  expect(document.body.textContent).toContain("Vídeo histórico");
  expect(document.body.textContent).toContain("Canal de teste");
  expect(document.body.textContent).toContain("15 de abril de 2021");
  expect(document.body.textContent).toContain("Contexto de 2021");
  act(() => document.querySelector<HTMLButtonElement>(".claim-toggle")!.click());
  const reflection = document.querySelector(".reflection-section");
  expect(reflection?.querySelectorAll("li")).toHaveLength(3);
  expect(reflection?.textContent).not.toMatch(/certo|errado/i);
  expect(document.querySelector("a")?.getAttribute("rel")).toBe("noopener noreferrer");
  expect(document.body.textContent).toContain("Alegação de teste");
  expect(document.body.textContent).toContain("Fonte de teste");
  expect(document.querySelector("a")?.getAttribute("rel")).toBe("noopener noreferrer");
  message({ type: "ANALYSIS_ERROR", error: "Parece que sua internet caiu." });
  expect(document.body.textContent).toContain("Parece que sua internet caiu.");
  expect(document.body.textContent).not.toContain("Vídeo histórico");
  message({ type: "ANALYSIS_ERROR" });
  expect(document.body.textContent).toContain("Não conseguimos checar este vídeo agora");
  message({ type: "NO_CAPTIONS_AVAILABLE" });
  expect(document.body.textContent).toContain("Este vídeo não tem legendas");
  message({ type: "ANALYSIS_START" });
  expect(document.querySelector('[role="alert"]')).toBeNull();
});
it("exibe três perguntas neutras de fallback quando não há reflexão no claim", () => {
  const claims = [{ ...data.claims[0], reflectionQuestions: undefined }];
  message({ type: "ANALYSIS_SUCCESS", data: { ...data, claims } });
  act(() => document.querySelector<HTMLButtonElement>(".claim-toggle")!.click());
  const reflection = document.querySelector(".reflection-section");
  expect(reflection?.querySelectorAll("li")).toHaveLength(3);
  expect(reflection?.textContent).not.toMatch(/certo|errado/i);
});
it("exibe banner de modo Evidence-Only sob degradação por falha externa", () => {
  message({
    type: "ANALYSIS_SUCCESS",
    data: {
      ...data,
      analysisMode: "evidence_only",
      limitations: ["Síntese indisponível temporariamente."],
    },
  });
  expect(document.body.textContent).toContain("Modo Exclusivo de Evidências");
  expect(document.body.textContent).toContain("Síntese indisponível temporariamente.");
});

it("exibe alerta de incerteza no topo quando as evidências são insuficientes", () => {
  message({
    type: "ANALYSIS_SUCCESS",
    data: {
      ...data,
      claims: [
        {
          id: "clm-02",
          text: "Alegação sem evidência",
          uncertainty: "insufficient_evidence",
          temporalContext: { videoPublishedAt: "2026-01-01T00:00:00Z" },
          evidence: [],
        },
      ],
    },
  });
  const alert = document.querySelector(".uncertainty-alert");
  expect(alert?.getAttribute("role")).toBe("alert");
  expect(alert?.textContent).toContain("Evidências documentais insuficientes");
});

it("expõe alerta de divergência quando há alegações apoiadas e contraditas no mesmo vídeo", () => {
  const claims = [
    {
      ...data.claims[0],
      id: "1",
      uncertainty: "supported" as const,
    },
    {
      ...data.claims[0],
      id: "2",
      uncertainty: "contradicted" as const,
    },
  ];
  message({ type: "ANALYSIS_SUCCESS", data: { ...data, claims } });
  const alert = document.querySelector(".uncertainty-alert");
  expect(alert?.textContent).toContain("Evidências com divergências apuradas");
  expect(document.body.textContent).toContain("Alegações apoiadas");
  expect(document.body.textContent).toContain("Alegações contraditas");
});

it("não exibe alerta de incerteza quando todas as alegações convergem para apoiadas", () => {
  message({ type: "ANALYSIS_SUCCESS", data });
  expect(document.querySelector(".uncertainty-alert")).toBeNull();
});

it("ignora remetentes externos, confirma foco e fecha pelo botão/Escape", () => {
  message(null);
  message({ type: "UNKNOWN" });
  message({ type: "ANALYSIS_START" }, "https://evil.test");
  message({ type: "ANALYSIS_START" }, "https://www.youtube.com", null);
  expect(document.body.textContent).toContain("para iniciar");
  message({ type: "FOCUS_PANEL" });
  expect(document.activeElement?.className).toBe("close-btn");
  const post = vi.spyOn(window.parent, "postMessage");
  act(() => document.querySelector<HTMLButtonElement>(".close-btn")!.click());
  act(() => { window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" })); });
  act(() => { window.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab" })); });
  expect(post).toHaveBeenCalledTimes(2);
  expect(post).toHaveBeenCalledWith({ type: "CLOSE_PANEL" }, "https://www.youtube.com");
  post.mockRestore();
});
it("permite acionar nova tentativa pelo painel em caso de falha ou ausência de legendas (HU10)", () => {
  const post = vi.spyOn(window.parent, "postMessage");
  message({ type: "NO_CAPTIONS" });
  expect(document.body.textContent).toContain("Este vídeo não tem legendas");
  const retryBtn = document.querySelector<HTMLButtonElement>(".retry-btn");
  expect(retryBtn).not.toBeNull();
  act(() => retryBtn!.click());
  expect(post).toHaveBeenCalledWith({ type: "RETRY_ANALYSIS" }, "https://www.youtube.com");
  post.mockRestore();
});

it("avisos de carregamento, erro e falta de legendas não usam termos técnicos", () => {
  const jargon = /HTTP|SLA|servidor|transcri|instabilidade|extraindo|fetch|timeout|\berro\b \d/i;
  message({ type: "ANALYSIS_START" });
  expect(document.body.textContent).not.toMatch(jargon);
  message({ type: "ANALYSIS_ERROR" });
  expect(document.body.textContent).not.toMatch(jargon);
  message({ type: "NO_CAPTIONS_AVAILABLE" });
  expect(document.body.textContent).not.toMatch(jargon);
});

it("expande apenas evidências e perguntas da alegação selecionada sem score global", () => {
  const other = { ...data.claims[0], id: "other", text: "Outra alegação", reflectionQuestions: ["Pergunta exclusiva 1?", "Pergunta exclusiva 2?", "Pergunta exclusiva 3?"], evidence: [{ ...data.claims[0].evidence[0], sourceId: "other-source", title: "Fonte exclusiva" }] };
  message({ type: "ANALYSIS_SUCCESS", data: { ...data, claims: [...data.claims, other] } });
  expect(document.querySelectorAll(".claim-card")).toHaveLength(2);
  expect(document.querySelectorAll(".claim-evidences")).toHaveLength(0);
  const buttons = document.querySelectorAll<HTMLButtonElement>(".claim-toggle");
  act(() => buttons[0].click());
  expect(document.body.textContent).toContain("Fonte de teste");
  expect(document.body.textContent).not.toContain("Fonte exclusiva");
  act(() => buttons[1].click());
  expect(buttons[0].getAttribute("aria-expanded")).toBe("false");
  expect(buttons[1].getAttribute("aria-expanded")).toBe("true");
  expect(document.body.textContent).not.toContain("Fonte de teste");
  expect(document.body.textContent).toContain("Fonte exclusiva");
  expect(document.body.textContent).toContain("Pergunta exclusiva 1?");
  expect(document.querySelectorAll(".reflection-section")).toHaveLength(1);
  expect(document.querySelector('[role="meter"], .gauge')).toBeNull();
  expect(document.body.textContent).not.toMatch(/\d+%|veracidade/i);
  act(() => buttons[1].click());
  expect(document.querySelectorAll(".claim-evidences")).toHaveLength(0);
});
it("informa ausência de alegações sem perguntas, nota ou veredito", () => {
  message({ type: "ANALYSIS_SUCCESS", data: { ...data, claims: [] } });
  expect(document.body.textContent).toContain("Não foram identificadas alegações checáveis");
  expect(document.querySelector(".claim-card, .reflection-section")).toBeNull();
  message({ type: "ANALYSIS_SUCCESS", data: { ...data, claims: [], analysisMode: "evidence_only" } });
  expect(document.body.textContent).toContain("Não foi possível identificar");
});
it("exibe seção discreta de feedback anônimo após carregar os resultados da análise", () => {
  message({ type: "ANALYSIS_SUCCESS", data });
  const feedbackSection = document.querySelector(".feedback-section");
  expect(feedbackSection).not.toBeNull();
  expect(feedbackSection?.textContent).toContain("Esta análise foi útil para você?");
  expect(feedbackSection?.querySelector('button[aria-label="Avaliar análise como útil"]')).not.toBeNull();
  expect(feedbackSection?.querySelector('button[aria-label="Avaliar análise como não útil"]')).not.toBeNull();
});
