// @vitest-environment jsdom
// @vitest-environment-options {"url":"https://www.youtube.com/watch?v=video"}
import { expect, it, vi } from "vitest";
vi.mock("./caption-parser", () => ({ extractCaptionsFromPage: vi.fn() }));
import { extractCaptionsFromPage } from "./caption-parser";
it("confirma imediatamente, usa cache sem legendas e limita o prazo na repetição", async () => {
  vi.useFakeTimers();
  document.body.innerHTML = '<div id="above-the-fold"></div>';
  const sendMessage = vi.fn().mockResolvedValue({ success: true, data: { score: 85 } });
  vi.stubGlobal("chrome", { runtime: { getURL: (path: string) => `https://extension.test/${path}`, sendMessage } });
  await import("./content-script");
  await vi.advanceTimersByTimeAsync(1000);
  const button = document.querySelector("#evidencia-badge-host")!.shadowRoot!.querySelector("button")!;
  button.click();
  expect(button.textContent).toContain("Analisando");
  expect(button.disabled).toBe(true);
  button.click();
  await vi.advanceTimersByTimeAsync(0);
  expect(button.textContent).toContain("85%");
  expect(extractCaptionsFromPage).not.toHaveBeenCalled();
  expect(sendMessage).toHaveBeenCalledTimes(1);
  sendMessage.mockResolvedValueOnce({ success: true, data: null }).mockResolvedValueOnce({ success: true, data: { score: 70 } });
  vi.mocked(extractCaptionsFromPage).mockResolvedValue({ videoId: "video", transcript: "texto", language: "pt" });
  const start = Date.now();
  button.click();
  await vi.advanceTimersByTimeAsync(0);
  expect(button.textContent).toContain("70%");
  expect(sendMessage.mock.calls[2][0].deadline).toBe(start + 9500);
  sendMessage.mockReturnValue(new Promise(() => {}));
  button.click();
  await vi.advanceTimersByTimeAsync(9500);
  expect(button.textContent).toContain("Tentar novamente");
  expect(button.disabled).toBe(false);
  window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
  expect(document.querySelector<HTMLIFrameElement>("iframe")!.style.display).toBe("none");
  vi.useRealTimers();
});
