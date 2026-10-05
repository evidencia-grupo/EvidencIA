/** HU05/HU08/HU10: lê faixas e metadados no mundo MAIN através do worker. */
export interface ExtractedCaptions {
  videoId: string;
  transcript: string;
  language: string;
  videoTitle: string;
  channelName: string;
  uploadDate?: string;
  durationSeconds?: number;
}

export function sanitizeTranscriptText(rawText: string): string {
  return rawText
    .replace(/<[^>]+>/g, " ")
    .replace(/\[\p{L}[\p{L}\s]*\]/gu, " ")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
}

export function parseCaptionBody(body: string): string {
  if (body.trimStart().startsWith("{")) {
    const data = JSON.parse(body) as {
      events?: Array<{
        segs?: Array<{
          utf8?: string;
          isSpeakerChange?: number;
        }>;
      }>;
    };

    const transcript = (data.events ?? [])
      .map((event) => {
        const eventText = (event.segs ?? [])
          .map((segment) => segment.utf8 ?? "")
          .join("");

        return eventText.replace(/^\s*>>\s*/, "");
      })
      .map(sanitizeTranscriptText)
      .filter(Boolean)
      .join(" ");

    return sanitizeTranscriptText(transcript);
  }

  const xml = new DOMParser().parseFromString(body, "text/xml");

  if (xml.querySelector("parsererror")) {
    throw new Error(
      "Não foi possível interpretar as legendas. Tente novamente.",
    );
  }

  return sanitizeTranscriptText(
    Array.from(xml.querySelectorAll("text, p"))
      .map((node) => node.textContent ?? "")
      .join(" "),
  );
}

export interface CaptionTrack { baseUrl: string; languageCode: string }

export interface CaptionAvailability {
  tracks: CaptionTrack[];
  metadata?: Pick<ExtractedCaptions, "videoTitle" | "channelName" | "uploadDate" | "durationSeconds">;
}

export async function detectCaptionTracks(videoId: string, signal?: AbortSignal): Promise<CaptionAvailability> {
  signal?.throwIfAborted();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const detectionPromise = Promise.resolve().then(() => chrome.runtime.sendMessage({ type: "GET_CAPTION_TRACKS", videoId }));
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
  if (!result?.success) throw new Error(result?.error || "Não foi possível acessar as legendas. Tente novamente.");
  const payload = result.data as {
    tracks?: Array<{ baseUrl: string; languageCode: string }>;
    metadata?: Pick<ExtractedCaptions, "videoTitle" | "channelName" | "uploadDate" | "durationSeconds">;
  };
  const tracks = payload?.tracks;
  if (!Array.isArray(tracks)) throw new Error("Resposta de legendas inválida.");
  return { tracks, metadata: payload.metadata };
}

export async function extractCaptionsFromPage(videoId: string, signal?: AbortSignal, detectedTracks?: CaptionAvailability): Promise<ExtractedCaptions | null> {
  const payload = detectedTracks ?? await detectCaptionTracks(videoId, signal);
  const tracks = payload.tracks;
  signal?.throwIfAborted();
  if (!tracks.length) return null;
  const track = tracks.find(item => item.languageCode.startsWith("pt")) ?? tracks[0];
  const url = new URL(track.baseUrl);
  if (url.origin !== "https://www.youtube.com" || url.pathname !== "/api/timedtext") throw new Error("Endereço de legendas inválido.");
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error(`Não foi possível baixar as legendas (HTTP ${response.status}). Tente novamente.`);
  const transcript = parseCaptionBody(await response.text());
  if (transcript.length < 50) throw new Error("A transcrição recebida está vazia ou é curta demais para análise. Tente novamente.");
  return {
    videoId,
    transcript,
    language: track.languageCode,
    videoTitle: payload.metadata?.videoTitle || document.title,
    channelName: payload.metadata?.channelName || "Canal YouTube",
    uploadDate: payload.metadata?.uploadDate,
    durationSeconds: payload.metadata?.durationSeconds,
  };
}
