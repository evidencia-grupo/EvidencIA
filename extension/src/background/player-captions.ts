/** Executada no mundo MAIN. Não captura variáveis externas nem acessa segredos. */
export function readPlayerCaptions(videoId: string) {
  type PlayerResponse = {
    videoDetails?: { videoId?: string };
    captions?: { playerCaptionsTracklistRenderer?: { captionTracks?: Array<{ baseUrl: string; languageCode: string }> } };
  };
  const player = document.querySelector("#movie_player") as (Element & { getPlayerResponse?: () => PlayerResponse }) | null;
  const response = player?.getPlayerResponse?.() ?? (window as Window & { ytInitialPlayerResponse?: PlayerResponse }).ytInitialPlayerResponse;
  if (location.pathname !== "/watch" || new URLSearchParams(location.search).get("v") !== videoId || response?.videoDetails?.videoId !== videoId) {
    throw new Error("O vídeo mudou ou os dados do player ainda não estão disponíveis. Tente novamente.");
  }
  return response.captions?.playerCaptionsTracklistRenderer?.captionTracks?.map(({ baseUrl, languageCode }) => ({ baseUrl, languageCode })) ?? [];
}

export async function getCaptionTracks(tabId: number, videoId: string) {
  const results = await chrome.scripting.executeScript({ target: { tabId }, world: "MAIN", func: readPlayerCaptions, args: [videoId] });
  const result = results[0]?.result;
  if (!Array.isArray(result)) throw new Error("Não foi possível ler as legendas do player. Tente novamente.");
  return result.filter(track => {
    try {
      const url = new URL(track.baseUrl);
      return url.origin === "https://www.youtube.com" && url.pathname === "/api/timedtext" && typeof track.languageCode === "string";
    } catch { return false; }
  });
}
