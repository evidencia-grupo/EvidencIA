// @vitest-environment jsdom
import { expect, it, vi, afterEach } from "vitest";
import { extractCaptionsFromPage } from "./caption-parser";

const text = "A vacina passou por estudos clínicos e protege a população contra a dengue.";
const tracks = { tracks: [{ baseUrl: "https://www.youtube.com/api/timedtext?v=video", languageCode: "pt" }], metadata: { videoTitle: "Vídeo", channelName: "Canal", durationSeconds: 600 } };
afterEach(() => {
  vi.unstubAllGlobals();
});
it.each([
  `<transcript><text start="300" dur="7">${text}</text></transcript>`,
  JSON.stringify({ events: [{ tStartMs: 300000, dDurationMs: 7000, segs: [{ utf8: text }] }] }),
])("preserva o tempo real depois de silêncio prolongado", async body => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, text: async () => body }));
  const result = await extractCaptionsFromPage("video", undefined, tracks);
  expect(result?.segments).toEqual([{ text, start: 300, duration: 7 }]);
});
it.each([
  `<transcript><text start="-2" dur="7">${text}</text></transcript>`,
  `<transcript><text start="300" dur="-7">${text}</text></transcript>`,
  `<transcript><text>${text}</text></transcript>`,
  JSON.stringify({ events: [{ segs: [{ utf8: text }] }] }),
  JSON.stringify({ events: [{ tStartMs: 2000, segs: [{ utf8: text }] }] }),
  JSON.stringify({ events: [{ tStartMs: null, dDurationMs: 7000, segs: [{ utf8: text }] }] }),
  JSON.stringify({ events: [{ tStartMs: 2000, dDurationMs: null, segs: [{ utf8: text }] }] }),
  JSON.stringify({ events: [{ tStartMs: -2000, dDurationMs: 7000, segs: [{ utf8: text }] }] }),
  JSON.stringify({ events: [{ tStartMs: 2000, dDurationMs: -7000, segs: [{ utf8: text }] }] }),
  JSON.stringify({ events: [{ tStartMs: 2000, dDurationMs: 7000, segs: [{ utf8: text }] }, { segs: [{ utf8: " " }] }] }),
])("não envia segmento inválido ou divergente", async body => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, text: async () => body }));
  const result = await extractCaptionsFromPage("video", undefined, tracks);
  expect(result?.transcript).toBe(text);
  if (body.includes('"utf8":" "')) expect(result?.segments).toHaveLength(1);
  else expect(result?.segments).toBeUndefined();
});

it.each(["", "<transcript></transcript>", "<transcript><text>Fala curta.</text></transcript>", "{}", "<transcript>"])("nunca troca legenda vazia, curta ou inválida pela descrição", async body => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, text: async () => body }));
  const payload = { ...tracks, metadata: { ...tracks.metadata, description: "Descrição longa com afirmações sobre saúde que não foram ditas no vídeo." } };
  await expect(extractCaptionsFromPage("video", undefined, payload)).rejects.toThrow();
});
it("junta subsegmentos JSON3 sem separar palavras e preserva os tempos", async () => {
  const body = JSON.stringify({ events: [{ tStartMs: 300000, dDurationMs: 7000, segs: [{ utf8: "A va" }, { utf8: "cina passou por estudos clínicos e protege a população contra a dengue." }] }] });
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, text: async () => body }));
  const result = await extractCaptionsFromPage("video", undefined, tracks);
  expect(result?.transcript).toBe(text);
  expect(result?.segments).toEqual([{ text, start: 300, duration: 7 }]);
});
it("lê legendas SRV3 com tempo em milissegundos", async () => {
  const body = `<timedtext><body><p t="300000" d="7000"><s>${text}</s></p></body></timedtext>`;
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, text: async () => body }));
  const result = await extractCaptionsFromPage("video", undefined, tracks);
  expect(result?.segments).toEqual([{ text, start: 300, duration: 7 }]);
});
