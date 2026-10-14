/** Executada no mundo MAIN. Não captura variáveis externas nem acessa segredos. */
export function readPlayerCaptions(videoId: string) {
  type PlayerResponse = {
    videoDetails?: { videoId?: string; title?: string; author?: string; lengthSeconds?: string };
    microformat?: {
      playerMicroformatRenderer?: { publishDate?: string; uploadDate?: string; ownerChannelName?: string };
    };
    captions?: { playerCaptionsTracklistRenderer?: { captionTracks?: Array<{ baseUrl: string; languageCode: string; kind?: string }> } };
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
      ?.map(({ baseUrl, languageCode, kind }) => ({ baseUrl, languageCode, ...(kind ? { kind } : {}) })) ?? [],
    metadata: {
      videoTitle: details.title ?? document.querySelector("h1.ytd-watch-metadata")?.textContent?.trim() ?? document.title,
      channelName: details.author ?? microformat?.ownerChannelName
        ?? document.querySelector("#channel-name")?.textContent?.trim() ?? "Canal YouTube",
      uploadDate,
      durationSeconds: Number.isFinite(durationSeconds) && durationSeconds >= 0 ? durationSeconds : undefined,
    },
  };
}

/**
 * Executada no mundo MAIN. O YouTube só entrega o conteúdo da legenda a requisições assinadas pelo próprio
 * player (parâmetro pot); a URL pública da faixa responde vazio. Aqui lemos a resposta que o player recebe
 * ao carregar a faixa pedida e, ao terminar, restauramos o estado de legendas que o usuário tinha.
 */
export async function capturePlayerCaption(videoId: string, languageCode: string, kind: string | null, timeoutMs: number): Promise<string | null> {
  type Player = Element & {
    getPlayerResponse?: () => { videoDetails?: { videoId?: string } } | undefined;
    loadModule?: (name: string) => void;
    unloadModule?: (name: string) => void;
    setOption?: (module: string, key: string, value: unknown) => void;
    getOption?: (module: string, key: string) => unknown;
  };
  const player = document.querySelector("#movie_player") as Player | null;
  const setOption = player?.setOption;
  if (!player || !setOption || player.getPlayerResponse?.()?.videoDetails?.videoId !== videoId) return null;

  const matches = (raw: string) => {
    try {
      const url = new URL(raw, location.origin);
      return url.pathname === "/api/timedtext" && url.searchParams.get("v") === videoId && url.searchParams.get("lang") === languageCode;
    } catch {
      return false;
    }
  };
  let finish: (body: string | null) => void = () => undefined;
  const captured = new Promise<string | null>((resolve) => { finish = resolve; });
  const accept = (body: string) => { if (body.trim()) finish(body); };

  const originalOpen = XMLHttpRequest.prototype.open;
  const originalFetch = window.fetch;
  XMLHttpRequest.prototype.open = function (this: XMLHttpRequest, ...args: [string, string | URL, ...unknown[]]) {
    if (matches(String(args[1]))) {
      this.addEventListener("load", () => {
        if (this.status !== 200) return;
        const body: unknown = this.response;
        // instanceof falha entre realms (player e script injetado); a etiqueta do objeto não.
        const isBuffer = Object.prototype.toString.call(body) === "[object ArrayBuffer]" || ArrayBuffer.isView(body);
        accept(typeof body === "string" ? body : isBuffer ? new TextDecoder().decode(body as ArrayBuffer) : "");
      });
    }
    return Reflect.apply(originalOpen, this, args);
  };
  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const response = await originalFetch(input, init);
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    if (response.ok && matches(url)) response.clone().text().then(accept, () => undefined);
    return response;
  };

  const previous = player.getOption?.("captions", "track") as { languageCode?: string } | undefined;
  const wasOn = Boolean(previous?.languageCode);
  const request = () => {
    const current = player.getOption?.("captions", "track") as { languageCode?: string } | undefined;
    if (current?.languageCode) player.unloadModule?.("captions");
    player.loadModule?.("captions");
    setOption.call(player, "captions", "track", kind ? { languageCode, kind } : { languageCode });
  };
  const timer = setTimeout(() => finish(null), timeoutMs);
  // Logo após o carregamento o player pode ignorar o pedido; repete enquanto nada foi capturado.
  const retry = setInterval(request, 2000);
  try {
    request();
    return await captured;
  } finally {
    clearTimeout(timer);
    clearInterval(retry);
    XMLHttpRequest.prototype.open = originalOpen;
    window.fetch = originalFetch;
    if (wasOn) setOption.call(player, "captions", "track", previous);
    else player.unloadModule?.("captions");
  }
}

const PLAYER_CAPTION_TIMEOUT_MS = 8000;
const MAX_CAPTION_BYTES = 5_000_000;

export async function getPlayerCaption(tabId: number, videoId: string, languageCode: string, kind?: string) {
  const results = await chrome.scripting.executeScript({
    target: { tabId }, world: "MAIN", func: capturePlayerCaption, args: [videoId, languageCode, kind ?? null, PLAYER_CAPTION_TIMEOUT_MS],
  });
  const body = results[0]?.result;
  if (typeof body !== "string" || !body.trim()) {
    throw new Error("O YouTube não entregou a legenda deste vídeo. Tente novamente em instantes.");
  }
  if (body.length > MAX_CAPTION_BYTES) throw new Error("A legenda recebida excede o tamanho suportado.");
  return body;
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
