// @vitest-environment jsdom
// @vitest-environment-options {"url":"https://www.youtube.com/watch?v=video"}
import { beforeEach, expect, it, vi } from "vitest";
import { getCaptionTracks, readPlayerCaptions } from "./player-captions";
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
