/** Executada no mundo MAIN. Não captura variáveis externas nem acessa segredos. */
export function readPlayerCaptions(videoId: string) {
  type PlayerResponse = {
    videoDetails?: { videoId?: string; title?: string; author?: string; lengthSeconds?: string };
    microformat?: {
      playerMicroformatRenderer?: { publishDate?: string; uploadDate?: string; ownerChannelName?: string };
    };
    captions?: { playerCaptionsTracklistRenderer?: { captionTracks?: Array<{ baseUrl: string; languageCode: string }> } };
  };
  const player = document.querySelector("#movie_player") as (Element & { getPlayerResponse?: () => PlayerResponse }) | null;
  const response = player?.getPlayerResponse?.() ?? (window as Window & { ytInitialPlayerResponse?: PlayerResponse }).ytInitialPlayerResponse;
  if (location.pathname !== "/watch" || new URLSearchParams(location.search).get("v") !== videoId || response?.videoDetails?.videoId !== videoId) {
    throw new Error("O vídeo mudou ou os dados do player ainda não estão disponíveis. Tente novamente.");
  }
  const details = response.videoDetails ?? {};
  const microformat = response.microformat?.playerMicroformatRenderer;
  const rawUploadDate = microformat?.publishDate ?? microformat?.uploadDate
    ?? document.querySelector<HTMLMetaElement>('meta[itemprop="uploadDate"]')?.content;
  const uploadDate = rawUploadDate && /^\d{4}-\d{2}-\d{2}$/.test(rawUploadDate)
    ? `${rawUploadDate}T00:00:00Z`
    : rawUploadDate;
  const durationSeconds = Number(details.lengthSeconds);

  return {
    tracks: response.captions?.playerCaptionsTracklistRenderer?.captionTracks
      ?.map(({ baseUrl, languageCode }) => ({ baseUrl, languageCode })) ?? [],
    metadata: {
      videoTitle: details.title ?? document.querySelector("h1.ytd-watch-metadata")?.textContent?.trim() ?? document.title,
      channelName: details.author ?? microformat?.ownerChannelName
        ?? document.querySelector("#channel-name")?.textContent?.trim() ?? "Canal YouTube",
      uploadDate,
      durationSeconds: Number.isFinite(durationSeconds) && durationSeconds >= 0 ? durationSeconds : undefined,
    },
  };
}

export async function getCaptionTracks(tabId: number, videoId: string) {
  const results = await chrome.scripting.executeScript({ target: { tabId }, world: "MAIN", func: readPlayerCaptions, args: [videoId] });
  const result = results[0]?.result;
  if (!result || !Array.isArray(result.tracks) || !result.metadata) {
    throw new Error("Não foi possível ler as legendas e os metadados do player. Tente novamente.");
  }
  return { ...result, tracks: result.tracks.filter(track => {
    try {
      const url = new URL(track.baseUrl);
      return url.origin === "https://www.youtube.com" && url.pathname === "/api/timedtext" && typeof track.languageCode === "string";
    } catch { return false; }
  }) };
}
