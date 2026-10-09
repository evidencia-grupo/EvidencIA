// @vitest-environment jsdom
import { expect, it, vi, afterEach } from "vitest";
import { extractCaptionsFromPage } from "./caption-parser";

const text = "A vacina passou por estudos clínicos e protege a população contra a dengue.";
const tracks = { tracks: [{ baseUrl: "https://www.youtube.com/api/timedtext?v=video", languageCode: "pt" }], metadata: { videoTitle: "Vídeo", channelName: "Canal", durationSeconds: 600 } };
afterEach(() => vi.unstubAllGlobals());
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
