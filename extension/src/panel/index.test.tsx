// @vitest-environment jsdom
import { beforeEach, afterEach, expect, it, vi } from "vitest";
import { render } from "preact";
import { act } from "preact/test-utils";
import type { AnalyzeResponse } from "../../../shared/types/api";
let App: typeof import("./index").App;
const data: AnalyzeResponse = {
  videoId: "video", videoTitle: "Vídeo histórico", channelName: "Canal de teste", uploadDate: "2021-04-15T00:00:00Z", temporalContext: { publicationYear: 2021, isOldContent: true, message: "Contexto de 2021" }, analyzedAt: "2026-09-28T00:00:00Z", analysisMode: "demo", score: 80, classification: "verdadeiro", summary: "Síntese de teste", processingTimeMs: 20,
  claims: [{ id: "a", text: "Alegação de teste", status: "apoiada", evidenceSummary: "Evidência", confidence: 0.8 }],
  sources: [{ id: "a", title: "Fonte de teste", url: "https://example.org/paper", domain: "example.org", reliabilityScore: 0.9 }],
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
  expect(document.querySelector('[role="status"]')?.textContent).toContain("Extraindo");
  message({ type: "ANALYSIS_SUCCESS", data });
  expect(document.body.textContent).toContain(data.summary);
  expect(document.body.textContent).toContain("Vídeo histórico");
  expect(document.body.textContent).toContain("Canal de teste");
  expect(document.body.textContent).toContain("15 de abril de 2021");
  expect(document.body.textContent).toContain("Contexto de 2021");
  expect(document.body.textContent).toContain("Demonstração");
  expect(document.querySelector("a")?.getAttribute("rel")).toBe("noopener noreferrer");
  message({ type: "ANALYSIS_ERROR", error: "HTTP 503" });
  expect(document.body.textContent).toContain("HTTP 503");
  expect(document.body.textContent).not.toContain(data.summary);
  message({ type: "ANALYSIS_ERROR" });
  expect(document.body.textContent).toContain("Ocorreu uma falha");
  message({ type: "NO_CAPTIONS_AVAILABLE" });
  expect(document.body.textContent).toContain("Legendas Indisponíveis");
  message({ type: "ANALYSIS_START" });
  expect(document.querySelector('[role="alert"]')).toBeNull();
});
it.each(["verdadeiro", "moderado", "falso", "inconclusivo"] as const)("renderiza classificação %s com rótulos textuais", classification => {
  message({ type: "ANALYSIS_SUCCESS", data: { ...data, classification, analysisMode: "live", claims: ["apoiada", "contraditada", "inconclusiva"].map((status, i) => ({ ...data.claims[0], id: String(i), status })) } });
  expect(document.querySelector('[role="region"]')?.getAttribute("aria-label")).toContain(classification);
  expect(document.body.textContent).toContain("Sem comprovação conclusiva");
  expect(document.body.textContent).not.toContain("Demonstração");
});
it("exibe alerta de incerteza no topo, antes do velocímetro, quando o resultado é inconclusivo", () => {
  message({ type: "ANALYSIS_SUCCESS", data: { ...data, classification: "inconclusivo", claims: [{ ...data.claims[0], status: "inconclusiva" }] } });
  const alert = document.querySelector(".uncertainty-alert");
  expect(alert?.getAttribute("role")).toBe("alert");
  expect(alert?.textContent).toContain("Ainda não dá para confirmar");
  expect(alert?.textContent).toContain("Nenhuma fonte confiável confirma nem desmente");
  const gauge = document.querySelector('[role="region"]')!;
  expect(alert!.compareDocumentPosition(gauge) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(alert!.compareDocumentPosition(document.querySelector(".warning-badge")!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(document.querySelector(".uncertainty-sides")).toBeNull();
});
it("expõe os dois lados sem apontar vencedor quando fontes legítimas discordam", () => {
  const claims = [
    { ...data.claims[0], id: "1", status: "apoiada" as const },
    { ...data.claims[0], id: "2", status: "contraditada" as const },
    { ...data.claims[0], id: "3", status: "contraditada" as const },
  ];
  message({ type: "ANALYSIS_SUCCESS", data: { ...data, classification: "moderado", claims } });
  const alert = document.querySelector(".uncertainty-alert");
  expect(alert?.textContent).toContain("As fontes discordam entre si");
  const sides = [...document.querySelectorAll(".uncertainty-sides li")].map((li) => li.textContent);
  expect(sides).toEqual(["O que apoia1 ponto tem apoio de fontes", "O que contradiz2 pontos são contrariados por fontes"]);
  expect(alert?.textContent).not.toMatch(/vencedor|verdadeiro|falso/i);
});
it("não exibe alerta de incerteza quando as fontes concordam", () => {
  message({ type: "ANALYSIS_SUCCESS", data });
  expect(document.querySelector(".uncertainty-alert")).toBeNull();
  message({ type: "ANALYSIS_SUCCESS", data: { ...data, classification: "falso", claims: [{ ...data.claims[0], status: "contraditada" }] } });
  expect(document.querySelector(".uncertainty-alert")).toBeNull();
});
it("não cria fontes vazias nem links executáveis", () => {
  message({ type: "ANALYSIS_SUCCESS", data: { ...data, sources: [] } });
  expect(document.querySelector("a")).toBeNull();
  message({ type: "ANALYSIS_SUCCESS", data: { ...data, sources: [{ ...data.sources[0], url: "javascript:alert(1)" }] } });
  expect(document.querySelector("a")?.hasAttribute("href")).toBe(false);
});
it("ignora remetentes externos, confirma foco e fecha pelo botão/Escape", () => {
  message(null); message({ type: "UNKNOWN" });
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
