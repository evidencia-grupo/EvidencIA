// @vitest-environment jsdom
import { beforeEach, expect, it, vi } from "vitest";
import { extractCaptionsFromPage, parseCaptionBody } from "./caption-parser";
const sendMessage = vi.fn();
const text = "A transcrição de teste contém mais de cinquenta caracteres e informações suficientes para checar.";
beforeEach(() => {
  vi.stubGlobal("chrome", { runtime: { sendMessage } });
  sendMessage.mockResolvedValue({ success: true, data: [{ baseUrl: "https://www.youtube.com/api/timedtext", languageCode: "pt-BR" }] });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, text: async () => `<transcript><text>${text}</text></transcript>` }));
});
it("extrai XML, entidades e segmentos JSON3 sem timestamps", async () => {
  expect(await extractCaptionsFromPage("video")).toEqual({ videoId: "video", transcript: text, language: "pt-BR" });
  expect(parseCaptionBody('<transcript><text>A &lt; B &amp; C &#233;</text></transcript>')).toBe("A &lt; B & C é".replace("&lt;", "<"));
  expect(parseCaptionBody(JSON.stringify({ events: [{ segs: [{ utf8: text }, {}] }, {}] }))).toBe(text);
  expect(parseCaptionBody('{}')).toBe("");
  expect(() => parseCaptionBody('<broken>')).toThrow("interpretar");
});
it("usa primeira faixa se português indisponível; ausência é distinta de falha", async () => {
  sendMessage.mockResolvedValueOnce({ success: true, data: [{ baseUrl: "https://www.youtube.com/api/timedtext", languageCode: "en" }] });
  expect((await extractCaptionsFromPage("video"))?.language).toBe("en");
  sendMessage.mockResolvedValueOnce({ success: true, data: [] });
  expect(await extractCaptionsFromPage("video")).toBeNull();
});
it.each([
  [{ success: false, error: "Erro específico" }, "Erro específico"],
  [undefined, "acessar"],
  [{ success: true, data: null }, "inválida"],
  [{ success: true, data: [{ baseUrl: "https://evil.test/", languageCode: "pt" }] }, "Endereço"],
])("trata resposta inválida %s", async (reply, message) => {
  sendMessage.mockResolvedValue(reply);
  await expect(extractCaptionsFromPage("video")).rejects.toThrow(message);
});
it("distingue HTTP, transcrição vazia e cancelamento", async () => {
  vi.mocked(fetch).mockResolvedValueOnce({ ok: false, status: 429 } as Response);
  await expect(extractCaptionsFromPage("video")).rejects.toThrow("HTTP 429");
  vi.mocked(fetch).mockResolvedValueOnce({ ok: true, text: async () => '<transcript/>' } as Response);
  await expect(extractCaptionsFromPage("video")).rejects.toThrow("curta demais");
  const controller = new AbortController(); controller.abort();
  await expect(extractCaptionsFromPage("video", controller.signal)).rejects.toThrow();
});
