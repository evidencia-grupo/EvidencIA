// @vitest-environment jsdom
// @vitest-environment-options {"url":"https://www.youtube.com/watch?v=video"}
import { beforeEach, afterEach, expect, it, vi } from "vitest";
vi.mock("./caption-parser", () => ({ extractCaptionsFromPage: vi.fn() }));
import { extractCaptionsFromPage } from "./caption-parser";
const sendMessage = vi.fn();
let listeners: Array<[string, EventListenerOrEventListenerObject]>;
const realAdd = window.addEventListener.bind(window);
const button = () => document.querySelector("#evidencia-badge-host")!.shadowRoot!.querySelector("button")!;
const frame = () => document.querySelector<HTMLIFrameElement>("iframe")!;
const flush = () => vi.advanceTimersByTimeAsync(0);
function panelMessage(type: string, origin = "https://extension.test", source: MessageEventSource | null = frame().contentWindow) {
  window.dispatchEvent(new MessageEvent("message", { data: { type }, origin, source }));
}
function navigate(path: string) {
  history.replaceState({}, "", path);
  window.dispatchEvent(new Event("yt-navigate-finish"));
}
beforeEach(() => {
  vi.resetModules(); vi.useFakeTimers(); listeners = [];
  vi.spyOn(window, "addEventListener").mockImplementation((type, listener, options) => { listeners.push([type, listener]); realAdd(type, listener, options); });
  history.replaceState({}, "", "/watch?v=video");
  document.body.innerHTML = '<h1 class="ytd-watch-metadata">Título</h1><div id="channel-name">Canal</div><div id="above-the-fold"></div>';
  sendMessage.mockReset().mockResolvedValue({ success: true, data: { claims: [] } });
  vi.mocked(extractCaptionsFromPage).mockReset().mockResolvedValue({ videoId: "video", transcript: "texto", language: "pt", videoTitle: "Título", channelName: "Canal", uploadDate: "2021-04-15T00:00:00Z", durationSeconds: 120 });
  vi.stubGlobal("chrome", { runtime: { getURL: (path: string) => `https://extension.test/${path}`, sendMessage } });
});
afterEach(() => {
  for (const [type, listener] of listeners) window.removeEventListener(type, listener);
  vi.restoreAllMocks(); vi.useRealTimers();
});
it("confirma de forma síncrona e evita requisições repetidas", async () => {
  await import("./content-script");
  const key = vi.fn(); document.addEventListener("keydown", key);
  button().dispatchEvent(new KeyboardEvent("keydown", { key: " ", bubbles: true, composed: true }));
  expect(key).not.toHaveBeenCalled();
  button().dispatchEvent(new KeyboardEvent("keydown", { key: "Tab", bubbles: true, composed: true }));
  expect(key).toHaveBeenCalledTimes(1);
  document.removeEventListener("keydown", key);
  button().click();
  expect(button().textContent).toContain("Analisando");
  expect(button().getAttribute("aria-disabled")).toBe("true");
  button().dispatchEvent(new MouseEvent("click"));
  await flush();
  expect(button().textContent).toContain("Checagem concluída");
  expect(extractCaptionsFromPage).not.toHaveBeenCalled();
  expect(sendMessage).toHaveBeenCalledTimes(1);
});
it("entrega estado pendente quando o iframe fica pronto e valida remetente", async () => {
  await import("./content-script");
  const post = vi.spyOn(frame().contentWindow!, "postMessage");
  button().click(); await flush();
  panelMessage("PANEL_READY", "https://evil.test");
  panelMessage("PANEL_READY", "https://extension.test", null);
  expect(post).not.toHaveBeenCalled();
  panelMessage("PANEL_READY");
  expect(post).toHaveBeenCalledWith({ type: "ANALYSIS_SUCCESS", data: { claims: [] } }, "https://extension.test");
  panelMessage("UNKNOWN");
  panelMessage("CLOSE_PANEL");
  expect(frame().style.display).toBe("none");
  expect(document.querySelector("#evidencia-badge-host")!.shadowRoot!.activeElement).toBe(button());
  button().click(); await flush();
  expect(post).toHaveBeenCalledWith({ type: "FOCUS_PANEL" }, "https://extension.test");
  window.dispatchEvent(new KeyboardEvent("keydown", { key: "Tab" }));
  window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
  expect(frame().style.display).toBe("none");
});
it("propaga orçamento total no cache miss", async () => {
  await import("./content-script"); panelMessage("PANEL_READY");
  sendMessage.mockResolvedValueOnce({ success: true, data: null }).mockResolvedValueOnce({ success: true, data: { claims: [] } });
  const start = Date.now(); button().click(); await flush();
  expect(button().textContent).toContain("Checagem concluída");
  expect(sendMessage.mock.calls[1][0]).toMatchObject({ deadline: start + 9500, payload: { videoTitle: "Título", channelName: "Canal", uploadDate: "2021-04-15T00:00:00Z", durationSeconds: 120 } });
});
it.each([undefined, { success: false, error: "Falhou" }])("erro do worker permite nova tentativa %s", async reply => {
  await import("./content-script");
  sendMessage.mockResolvedValueOnce({ success: false }).mockResolvedValueOnce(reply);
  button().click(); await flush(); expect(button().textContent).toContain("Tentar novamente");
  expect(button().getAttribute("aria-disabled")).toBe("false");
});
it("ausência de legendas encerra carregamento; erro inesperado tem fallback", async () => {
  await import("./content-script");
  sendMessage.mockResolvedValue({ success: true, data: null });
  vi.mocked(extractCaptionsFromPage).mockResolvedValueOnce(null);
  button().click(); await flush(); expect(button().textContent).toContain("Sem legendas");
  sendMessage.mockRejectedValueOnce("erro");
  button().click(); await flush(); expect(button().textContent).toContain("Tentar novamente");
});
it("timeout aborta a extração e rejeita resposta tardia", async () => {
  await import("./content-script");
  panelMessage("PANEL_READY");
  const post = vi.spyOn(frame().contentWindow!, "postMessage");
  let resolve!: (value: unknown) => void;
  sendMessage.mockReturnValueOnce(new Promise(r => { resolve = r; }));
  button().click(); await vi.advanceTimersByTimeAsync(9500);
  expect(button().getAttribute("aria-disabled")).toBe("false");
  expect(post).toHaveBeenCalledWith(
    { type: "ANALYSIS_ERROR", error: "A checagem demorou mais do que o esperado. Tente de novo em instantes." },
    "https://extension.test",
  );
  resolve({ success: true, data: { claims: [] } }); await flush();
  expect(button().textContent).not.toContain("99%");
});
it("navegação invalida análise antiga e remove o botão fora do watch", async () => {
  await import("./content-script");
  let resolve!: (value: unknown) => void;
  sendMessage.mockReturnValueOnce(new Promise(r => { resolve = r; }));
  button().click(); navigate("/watch?v=next");
  resolve({ success: true, data: { claims: [] } }); await flush();
  expect(button().textContent).toContain("Checar Alegações");
  navigate("/"); expect(document.querySelector("#evidencia-badge-host")).toBeNull();
  navigate("/watch"); expect(document.querySelector("#evidencia-badge-host")).toBeNull();
});
it("aguarda metadados, recria iframe removido e suporta chegada pela home", async () => {
  history.replaceState({}, "", "/"); document.body.innerHTML = "";
  await import("./content-script");
  navigate("/watch?v=video"); expect(document.querySelector("#evidencia-badge-host")).toBeNull();
  document.body.insertAdjacentHTML("beforeend", '<div id="top-row"></div>');
  await vi.advanceTimersByTimeAsync(250);
  expect(button()).toBeTruthy();
  frame().remove(); button().click(); await flush(); expect(frame().isConnected).toBe(true);
  navigate("/"); document.body.innerHTML = '<ytd-watch-metadata></ytd-watch-metadata>';
  navigate("/watch?v=next"); expect(button()).toBeTruthy();
});
it("mostra no painel um aviso simples em vez do erro técnico", async () => {
  await import("./content-script"); panelMessage("PANEL_READY");
  const post = vi.spyOn(frame().contentWindow!, "postMessage");
  sendMessage.mockResolvedValueOnce({ success: false }).mockResolvedValueOnce({ success: false, error: "Falha no servidor intermediário: HTTP 503" });
  button().click(); await flush();
  const error = post.mock.calls.map(([msg]) => msg as { type: string; error?: string }).find(msg => msg.type === "ANALYSIS_ERROR")?.error;
  expect(error).toBe("Não conseguimos checar este vídeo agora. Tente de novo em instantes.");
  expect(error).not.toMatch(/HTTP|servidor/);
});
