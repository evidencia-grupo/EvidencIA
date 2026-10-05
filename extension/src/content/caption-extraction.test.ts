// @vitest-environment jsdom
import { beforeEach, expect, it, vi } from "vitest";
import { extractCaptionsFromPage, parseCaptionBody } from "./caption-parser";
const sendMessage = vi.fn();
const text = "A transcrição de teste contém mais de cinquenta caracteres e informações suficientes para checar.";
const metadata = { videoTitle: "Vídeo histórico", channelName: "Canal História", uploadDate: "2021-04-15T00:00:00Z", durationSeconds: 120 };
beforeEach(() => {
  vi.stubGlobal("chrome", { runtime: { sendMessage } });
  sendMessage.mockResolvedValue({ success: true, data: { tracks: [{ baseUrl: "https://www.youtube.com/api/timedtext", languageCode: "pt-BR" }], metadata } });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, text: async () => `<transcript><text>${text}</text></transcript>` }));
});
it("extrai XML, entidades e segmentos JSON3 sem timestamps", async () => {
  expect(await extractCaptionsFromPage("video")).toEqual({ videoId: "video", transcript: text, language: "pt-BR", ...metadata });
  expect(parseCaptionBody('<transcript><text>A &lt; B &amp; C &#233;</text></transcript>')).toBe("A &lt; B & C é".replace("&lt;", "<"));
  expect(parseCaptionBody(JSON.stringify({ events: [{ segs: [{ utf8: text }, {}] }, {}] }))).toBe(text);
  expect(parseCaptionBody('{}')).toBe("");
  expect(() => parseCaptionBody('<broken>')).toThrow("interpretar");
});
it("usa primeira faixa se português indisponível; ausência é distinta de falha", async () => {
  sendMessage.mockResolvedValueOnce({ success: true, data: { tracks: [{ baseUrl: "https://www.youtube.com/api/timedtext", languageCode: "en" }], metadata } });
  expect((await extractCaptionsFromPage("video"))?.language).toBe("en");
  sendMessage.mockResolvedValueOnce({ success: true, data: { tracks: [], metadata } });
  expect(await extractCaptionsFromPage("video")).toBeNull();
});
it.each([
  [{ success: false, error: "Erro específico" }, "Erro específico"],
  [undefined, "acessar"],
  [{ success: true, data: null }, "inválida"],
  [{ success: true, data: { tracks: [{ baseUrl: "https://evil.test/", languageCode: "pt" }], metadata } }, "Endereço"],
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
it("limita tempo de deteccao de faixas a 1 segundo (HU10 / RNF-01)", async () => {
  vi.useFakeTimers();
  sendMessage.mockReturnValueOnce(new Promise(() => {}));
  const promise = extractCaptionsFromPage("video");
  const expectation = expect(promise).rejects.toThrow("Tempo limite de 1 segundo");
  await vi.advanceTimersByTimeAsync(1001);
  await expectation;
  vi.useRealTimers();
});

it("processa JSON3 real preservando palavras do mesmo evento", () => {
  const body = JSON.stringify({
    events: [
      {
        tStartMs: 440,
        dDurationMs: 4640,
        segs: [
          { utf8: "Tá" },
          { utf8: " começando" },
          { utf8: " o programa" },
        ],
      },
      {
        tStartMs: 5080,
        dDurationMs: 4639,
        segs: [
          { utf8: "bem-vindo." },
        ],
      },
    ],
  });

  expect(parseCaptionBody(body)).toBe(
    "Tá começando o programa bem-vindo.",
  );
});

it("ignora eventos JSON3 contendo somente quebra de linha", () => {
  const body = JSON.stringify({
    events: [
      {
        segs: [{ utf8: "Primeira fala." }],
      },
      {
        aAppend: 1,
        segs: [{ utf8: "\n" }],
      },
      {
        segs: [{ utf8: "Segunda fala." }],
      },
    ],
  });

  expect(parseCaptionBody(body)).toBe(
    "Primeira fala. Segunda fala.",
  );
});

it("remove marcador de musica sem remover a fala", () => {
  const body = JSON.stringify({
    events: [
      {
        segs: [{ utf8: "[música]" }],
      },
      {
        segs: [{ utf8: "A fala continua normalmente." }],
      },
    ],
  });

  expect(parseCaptionBody(body)).toBe(
    "A fala continua normalmente.",
  );
});

it("remove marcador de troca de locutor sem remover a fala", () => {
  const body = JSON.stringify({
    events: [
      {
        segs: [
          { utf8: ">> Tudo" },
          { utf8: " bem?" },
        ],
      },
    ],
  });

  expect(parseCaptionBody(body)).toBe("Tudo bem?");
});


it("cancela detecção pendente e ignora resposta tardia sem baixar legendas", async () => {
  let resolveTracks!: (value: unknown) => void;
  sendMessage.mockReturnValueOnce(new Promise(resolve => { resolveTracks = resolve; }));
  const controller = new AbortController();
  const extraction = extractCaptionsFromPage("video", controller.signal);
  const rejection = expect(extraction).rejects.toThrow("Checagem cancelada");
  await Promise.resolve();
  controller.abort(new Error("Checagem cancelada"));
  await rejection;
  resolveTracks({ success: true, data: { tracks: [{ baseUrl: "https://www.youtube.com/api/timedtext", languageCode: "pt" }], metadata } });
  await Promise.resolve();
  expect(fetch).not.toHaveBeenCalled();
});
