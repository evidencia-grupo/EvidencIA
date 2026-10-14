// @vitest-environment jsdom
// @vitest-environment-options {"url":"https://www.youtube.com/watch?v=video"}
import { beforeEach, expect, it, vi } from "vitest";
import { capturePlayerCaption, getCaptionTracks, getPlayerCaption, readPlayerCaptions } from "./player-captions";
const tracks = [{ baseUrl: "https://www.youtube.com/api/timedtext?v=video", languageCode: "pt" }];
const metadata = { videoTitle: "Vídeo histórico", channelName: "Canal História", uploadDate: "2021-04-15T00:00:00Z", durationSeconds: 120 };
beforeEach(() => {
  document.body.innerHTML = '<div id="movie_player"></div>';
  (window as any).ytInitialPlayerResponse = {
    videoDetails: { videoId: "video", title: metadata.videoTitle, author: metadata.channelName, lengthSeconds: "120" },
    microformat: { playerMicroformatRenderer: { publishDate: "2021-04-15" } },
    captions: { playerCaptionsTracklistRenderer: { captionTracks: tracks } },
  };
});
it("lê legendas e metadados originais do vídeo", () => expect(readPlayerCaptions("video")).toEqual({ tracks, metadata }));
it("prioriza dados atuais do player e suporta vídeo sem legendas", () => {
  (document.querySelector("#movie_player") as any).getPlayerResponse = () => ({ videoDetails: { videoId: "video" } });
  expect(readPlayerCaptions("video")).toMatchObject({ tracks: [], metadata: { channelName: "Canal YouTube" } });
});
it("rejeita dados antigos e player indisponível", () => {
  expect(() => readPlayerCaptions("other")).toThrow("vídeo mudou");
  delete (window as any).ytInitialPlayerResponse;
  expect(() => readPlayerCaptions("video")).toThrow();
});
it("injeta no MAIN e filtra URLs externas e inválidas", async () => {
  const executeScript = vi.fn().mockResolvedValue([{ result: { tracks: [...tracks, { baseUrl: "https://evil.test", languageCode: "pt" }, { baseUrl: "invalid" }], metadata } }]);
  vi.stubGlobal("chrome", { scripting: { executeScript } });
  expect(await getCaptionTracks(7, "video")).toEqual({ tracks, metadata });
  expect(executeScript).toHaveBeenCalledWith(expect.objectContaining({ world: "MAIN", target: { tabId: 7 }, args: ["video"] }));
  executeScript.mockResolvedValue([]);
  await expect(getCaptionTracks(7, "video")).rejects.toThrow("Não foi possível");
});

it("não coleta descrição como dado de legenda", () => {
  (window as any).ytInitialPlayerResponse.videoDetails.shortDescription = "Uma descrição não corresponde à fala do vídeo.";
  document.body.insertAdjacentHTML("beforeend", '<div id="description">Texto descritivo independente</div>');
  expect(readPlayerCaptions("video").metadata).not.toHaveProperty("description");
});

const CAPTION_URL = "https://www.youtube.com/api/timedtext?v=video&lang=pt&pot=token";
const json3 = JSON.stringify({ events: [{ segs: [{ utf8: "Legenda vinda do player" }] }] });

function fakePlayer(onTrack: (track: { languageCode: string }) => void, previous?: { languageCode: string }) {
  const player = document.querySelector("#movie_player") as any;
  player.getPlayerResponse = () => ({ videoDetails: { videoId: "video" } });
  player.getOption = vi.fn(() => previous ?? {});
  player.loadModule = vi.fn();
  player.unloadModule = vi.fn();
  player.setOption = vi.fn((_m: string, _k: string, track: { languageCode: string }) => onTrack(track));
  return player;
}

class FakeXHR extends EventTarget {
  status = 0; response: unknown = null; url = "";
  open(_method: string, url: string) { this.url = url; }
  send() {
    setTimeout(() => {
      this.status = 200;
      this.response = this.url.includes("lang=pt") ? new TextEncoder().encode(json3).buffer : new ArrayBuffer(0);
      this.dispatchEvent(new Event("load"));
    }, 0);
  }
}

it("lê a legenda que o player baixa por XHR e restaura legendas desligadas", async () => {
  vi.stubGlobal("XMLHttpRequest", FakeXHR);
  const originalOpen = FakeXHR.prototype.open;
  const player = fakePlayer(() => { const x = new XMLHttpRequest(); x.open("GET", "/api/timedtext?v=video&lang=en&pot=t"); x.send(); const y = new XMLHttpRequest(); y.open("GET", CAPTION_URL); y.send(); });
  await expect(capturePlayerCaption("video", "pt", "asr", 1000)).resolves.toBe(json3);
  expect(player.setOption).toHaveBeenCalledWith("captions", "track", { languageCode: "pt", kind: "asr" });
  expect(player.unloadModule).toHaveBeenCalledWith("captions");
  expect(FakeXHR.prototype.open).toBe(originalOpen);
  vi.unstubAllGlobals();
});

it("lê a legenda baixada por fetch e devolve a faixa que o usuário já usava", async () => {
  const originalFetch = vi.fn(async () => new Response(json3, { status: 200 }));
  vi.stubGlobal("fetch", originalFetch);
  const previous = { languageCode: "en" };
  const player = fakePlayer(() => { void window.fetch(CAPTION_URL); }, previous);
  await expect(capturePlayerCaption("video", "pt", null, 1000)).resolves.toBe(json3);
  expect(player.unloadModule).toHaveBeenCalledTimes(1);
  expect(player.setOption).toHaveBeenLastCalledWith("captions", "track", previous);
  expect(window.fetch).toBe(originalFetch);
  vi.unstubAllGlobals();
});

it("repete o pedido ao player que ainda não estava pronto", async () => {
  vi.useFakeTimers();
  const originalFetch = vi.fn(async () => new Response(json3, { status: 200 }));
  vi.stubGlobal("fetch", originalFetch);
  let calls = 0;
  const player = fakePlayer(() => { calls += 1; if (calls === 2) void window.fetch(CAPTION_URL); });
  const result = capturePlayerCaption("video", "pt", null, 8000);
  await vi.advanceTimersByTimeAsync(2100);
  await expect(result).resolves.toBe(json3);
  expect(player.setOption).toHaveBeenCalledTimes(2);
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

it("devolve null quando o player não entrega legenda ou o vídeo mudou", async () => {
  fakePlayer(() => undefined);
  await expect(capturePlayerCaption("video", "pt", null, 20)).resolves.toBeNull();
  await expect(capturePlayerCaption("outro", "pt", null, 20)).resolves.toBeNull();
});

it("executa a captura no MAIN e rejeita resposta vazia", async () => {
  const executeScript = vi.fn().mockResolvedValue([{ result: json3 }]);
  vi.stubGlobal("chrome", { scripting: { executeScript } });
  await expect(getPlayerCaption(7, "video", "pt", "asr")).resolves.toBe(json3);
  expect(executeScript).toHaveBeenCalledWith(expect.objectContaining({ world: "MAIN", target: { tabId: 7 }, args: ["video", "pt", "asr", 8000] }));
  executeScript.mockResolvedValue([{ result: null }]);
  await expect(getPlayerCaption(7, "video", "pt")).rejects.toThrow("não entregou");
});
