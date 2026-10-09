/** Leitura e sanitização de faixas de legenda do YouTube. */

export interface ExtractedCaptions {
  videoId: string;
  transcript: string;
  segments?: CaptionSegment[];
  language: string;
  videoTitle: string;
  channelName: string;
  uploadDate?: string;
  durationSeconds?: number;
}

export interface CaptionSegment {
  text: string;
  start: number;
  duration: number;
}

export interface CaptionTrack {
  baseUrl: string;
  languageCode: string;
}

export interface CaptionAvailability {
  tracks: CaptionTrack[];
  metadata?: Pick<ExtractedCaptions, "videoTitle" | "channelName" | "uploadDate" | "durationSeconds"> & { description?: string };
}

interface YouTubeCaptionJsonSegment {
  utf8?: string;
}

interface YouTubeCaptionJsonEvent {
  tStartMs?: number;
  dDurationMs?: number;
  segs?: YouTubeCaptionJsonSegment[];
}

interface YouTubeCaptionJsonResponse {
  events?: YouTubeCaptionJsonEvent[];
}

interface YouTubePlayerResponse {
  captions?: {
    playerCaptionsTracklistRenderer?: {
      captionTracks?: CaptionTrack[];
    };
  };
}

interface YouTubeMoviePlayer extends Element {
  getPlayerResponse?: () => YouTubePlayerResponse;
}

export function sanitizeTranscriptText(rawText: string | null | undefined): string {
  if (rawText == null) return "";

  return rawText
    .replace(/<[^>]+>/g, " ")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, "&")
    .replace(/\[(?!\d)[^\]]*\]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function parseCaptionJson(jsonText: string): CaptionSegment[] {
  if (!jsonText.trim()) return [];

  try {
    const data = JSON.parse(jsonText) as YouTubeCaptionJsonResponse;
    if (!Array.isArray(data.events)) return [];

    return data.events
      .map((event): CaptionSegment | null => {
        if (!Array.isArray(event.segs) || event.segs.length === 0) return null;

        const raw = event.segs.map((segment) => segment.utf8 ?? "").join("");
        const text = sanitizeTranscriptText(raw.replace(/^\s*>>\s*/, ""));

        if (!text || typeof event.tStartMs !== "number" || typeof event.dDurationMs !== "number"
          || !Number.isFinite(event.tStartMs) || !Number.isFinite(event.dDurationMs)
          || event.tStartMs < 0 || event.dDurationMs < 0) return null;

        return { text, start: event.tStartMs / 1000, duration: event.dDurationMs / 1000 };
      })
      .filter((segment): segment is CaptionSegment => segment !== null);
  } catch {
    return [];
  }
}

export function parseCaptionXml(xmlText: string): CaptionSegment[] {
  if (!xmlText.trim()) return [];

  const parser = new DOMParser();
  const document = parser.parseFromString(xmlText, "text/xml");

  if (document.querySelector("parsererror")) return [];

  return Array.from(document.querySelectorAll("text"))
    .map((node): CaptionSegment | null => {
      const text = sanitizeTranscriptText(node.textContent ?? "");
      const start = Number.parseFloat(node.getAttribute("start") ?? "");
      const duration = Number.parseFloat(node.getAttribute("dur") ?? "");

      if (!text || !Number.isFinite(start) || !Number.isFinite(duration)) return null;

      return { text, start, duration };
    })
    .filter((segment): segment is CaptionSegment => segment !== null);
}

export function parseCaptionBody(body: string): string {
  const trimmed = body.trimStart();

  if (trimmed.startsWith("{")) {
    let data: YouTubeCaptionJsonResponse;
    try {
      data = JSON.parse(body) as YouTubeCaptionJsonResponse;
    } catch {
      throw new Error("Não foi possível interpretar as legendas. Tente novamente.");
    }
    const transcript = (data.events ?? [])
      .flatMap((event) => event.segs ?? [])
      .map((segment) => segment.utf8 ?? "")
      .join(" ");

    return sanitizeTranscriptText(transcript.replace(/(^|\s)\s*>>\s*/g, "$1"));
  }

  const document = new DOMParser().parseFromString(body, "text/xml");

  if (document.querySelector("parsererror")) {
    throw new Error("Não foi possível interpretar as legendas. Tente novamente.");
  }

  return sanitizeTranscriptText(
    Array.from(document.querySelectorAll("text, p"))
      .map((node) => node.textContent ?? "")
      .join(" "),
  );
}

export function selectCaptionTrack(tracks: CaptionTrack[] | null | undefined): CaptionTrack | null {
  if (!tracks || tracks.length === 0) return null;

  const preferred = tracks.find((track) => track.languageCode.toLowerCase().startsWith("pt"));
  return preferred ?? tracks[0];
}

export function getCaptionTracksFromPlayer(): CaptionTrack[] {
  const player = document.querySelector("#movie_player") as YouTubeMoviePlayer | null;
  if (!player || typeof player.getPlayerResponse !== "function") return [];

  try {
    const response = player.getPlayerResponse();
    return response?.captions?.playerCaptionsTracklistRenderer?.captionTracks ?? [];
  } catch (error) {
    console.warn("[EvidencIA] getCaptionTracksFromPlayer failed:", error);
    return [];
  }
}

export async function detectCaptionTracks(videoId: string, signal?: AbortSignal): Promise<CaptionAvailability> {
  signal?.throwIfAborted();

  let timer: ReturnType<typeof setTimeout> | undefined;
  const detectionPromise = Promise.resolve().then(() =>
    chrome.runtime.sendMessage({ type: "GET_CAPTION_TRACKS", videoId }),
  );

  let onAbort: (() => void) | undefined;
  const timeoutPromise = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new Error("Tempo limite de 1 segundo para detecção de legendas excedido. Tente novamente.")), 1000);
    onAbort = () => reject(signal?.reason ?? new DOMException("Aborted", "AbortError"));
    signal?.addEventListener("abort", onAbort, { once: true });
  });

  let result: any;
  try {
    result = await Promise.race([detectionPromise, timeoutPromise]);
  } finally {
    clearTimeout(timer);
    if (onAbort) signal?.removeEventListener("abort", onAbort);
  }

  signal?.throwIfAborted();

  if (!result?.success) {
    throw new Error(result?.error || "Não foi possível acessar as legendas. Tente novamente.");
  }

  const payload = result.data;
  if (!payload || !Array.isArray(payload.tracks)) {
    throw new Error("Resposta de legendas inválida.");
  }

  return {
    tracks: payload.tracks,
    metadata: payload.metadata,
  };
}

export async function extractCaptionsFromPage(
  videoId: string,
  signal?: AbortSignal,
  detectedTracks?: CaptionAvailability,
): Promise<ExtractedCaptions | null> {
  const payload = detectedTracks ?? (await detectCaptionTracks(videoId, signal));
  const tracks = payload.tracks;

  signal?.throwIfAborted();
  const track = selectCaptionTrack(tracks);
  if (!track) return null;

  let validUrl = false;
  try {
    const url = new URL(track.baseUrl);
    validUrl = url.origin === "https://www.youtube.com" && url.pathname === "/api/timedtext";
  } catch {
    validUrl = false;
  }
  if (!validUrl) {
    throw new Error("Endereço de legendas inválido.");
  }

  const response = await fetch(track.baseUrl, { signal });

  if (!response.ok) {
    throw new Error(`Não foi possível baixar as legendas (HTTP ${response.status}). Tente novamente.`);
  }

  let transcript = "";
  let segments: CaptionSegment[] = [];
  try {
    const text = await response.text();
    transcript = parseCaptionBody(text);
    const timed = text.trimStart().startsWith("{") ? parseCaptionJson(text) : parseCaptionXml(text);
    if (timed.length && timed.every(s => Number.isFinite(s.start) && s.start >= 0 && Number.isFinite(s.duration) && s.duration >= 0)
      && sanitizeTranscriptText(timed.map(s => s.text).join(" ")) === transcript) segments = timed;
  } catch {
    transcript = "";
  }

  if (transcript.length < 50 && payload.metadata?.description && payload.metadata.description.length >= 50) {
    transcript = sanitizeTranscriptText(payload.metadata.description);
    segments = [];
  }

  if (transcript.length < 50) {
    throw new Error("A transcrição recebida está vazia ou é curta demais para análise. Tente novamente.");
  }

  return {
    videoId,
    transcript,
    ...(segments.length ? { segments } : {}),
    language: track.languageCode,
    videoTitle: payload.metadata?.videoTitle ?? document.title,
    channelName: payload.metadata?.channelName ?? document.querySelector("#channel-name")?.textContent?.trim() ?? "Canal YouTube",
    uploadDate: payload.metadata?.uploadDate,
    durationSeconds: payload.metadata?.durationSeconds,
  };
}
