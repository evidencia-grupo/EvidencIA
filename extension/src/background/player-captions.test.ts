// @vitest-environment jsdom
// @vitest-environment-options {"url":"https://www.youtube.com/watch?v=video"}
import { beforeEach, expect, it, vi } from "vitest";
import { getCaptionTracks, readPlayerCaptions } from "./player-captions";
const tracks = [{ baseUrl: "https://www.youtube.com/api/timedtext?v=video", languageCode: "pt" }];
beforeEach(() => {
  document.body.innerHTML = '<div id="movie_player"></div>';
  (window as any).ytInitialPlayerResponse = { videoDetails: { videoId: "video" }, captions: { playerCaptionsTracklistRenderer: { captionTracks: tracks } } };
});
it("lê resposta global com identidade do vídeo", () => expect(readPlayerCaptions("video")).toEqual(tracks));
it("prioriza dados atuais do player e suporta vídeo sem legendas", () => {
  (document.querySelector("#movie_player") as any).getPlayerResponse = () => ({ videoDetails: { videoId: "video" } });
  expect(readPlayerCaptions("video")).toEqual([]);
});
it("rejeita dados antigos e player indisponível", () => {
  expect(() => readPlayerCaptions("other")).toThrow("vídeo mudou");
  delete (window as any).ytInitialPlayerResponse;
  expect(() => readPlayerCaptions("video")).toThrow();
});
it("injeta no MAIN e filtra URLs externas e inválidas", async () => {
  const executeScript = vi.fn().mockResolvedValue([{ result: [...tracks, { baseUrl: "https://evil.test", languageCode: "pt" }, { baseUrl: "invalid" }] }]);
  vi.stubGlobal("chrome", { scripting: { executeScript } });
  expect(await getCaptionTracks(7, "video")).toEqual(tracks);
  expect(executeScript).toHaveBeenCalledWith(expect.objectContaining({ world: "MAIN", target: { tabId: 7 }, args: ["video"] }));
  executeScript.mockResolvedValue([]);
  await expect(getCaptionTracks(7, "video")).rejects.toThrow("Não foi possível");
});
