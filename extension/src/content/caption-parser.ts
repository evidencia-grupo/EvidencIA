/** HU05/HU10: lê faixas no mundo MAIN através do worker e busca somente legendas do YouTube. */
export interface ExtractedCaptions { videoId: string; transcript: string; language: string }

export function sanitizeTranscriptText(rawText: string): string {
  return rawText.replace(/<[^>]+>/g, " ").replace(/\[[\p{L}\s]+\]/gu, "")
    .replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, "&").replace(/\s+/g, " ").trim();
}

export function parseCaptionBody(body: string): string {
  if (body.trimStart().startsWith("{")) {
    const data = JSON.parse(body) as { events?: Array<{ segs?: Array<{ utf8?: string }> }> };
    return sanitizeTranscriptText((data.events ?? []).flatMap(event => (event.segs ?? []).map(seg => seg.utf8 ?? "")).join(" "));
  }
  const xml = new DOMParser().parseFromString(body, "text/xml");
  if (xml.querySelector("parsererror")) throw new Error("Não foi possível interpretar as legendas. Tente novamente.");
  return sanitizeTranscriptText(Array.from(xml.querySelectorAll("text, p")).map(node => node.textContent ?? "").join(" "));
}

export async function extractCaptionsFromPage(videoId: string, signal?: AbortSignal): Promise<ExtractedCaptions | null> {
  signal?.throwIfAborted();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const detectionPromise = chrome.runtime.sendMessage({ type: "GET_CAPTION_TRACKS", videoId });
  const timeoutPromise = new Promise<never>((_, reject) => {
    timer = setTimeout(() => reject(new Error("Tempo limite de 1 segundo para detecção de legendas excedido. Tente novamente.")), 1000);
    signal?.addEventListener("abort", () => reject(signal.reason ?? new DOMException("Aborted", "AbortError")));
  });

  let result: any;
  try {
    result = await Promise.race([detectionPromise, timeoutPromise]);
  } finally {
    clearTimeout(timer);
  }

  signal?.throwIfAborted();
  if (!result?.success) throw new Error(result?.error || "Não foi possível acessar as legendas. Tente novamente.");
  const tracks = result.data as Array<{ baseUrl: string; languageCode: string }>;
  if (!Array.isArray(tracks)) throw new Error("Resposta de legendas inválida.");
  if (!tracks.length) return null;
  const track = tracks.find(item => item.languageCode.startsWith("pt")) ?? tracks[0];
  const url = new URL(track.baseUrl);
  if (url.origin !== "https://www.youtube.com" || url.pathname !== "/api/timedtext") throw new Error("Endereço de legendas inválido.");
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error(`Não foi possível baixar as legendas (HTTP ${response.status}). Tente novamente.`);
  const transcript = parseCaptionBody(await response.text());
  if (transcript.length < 50) throw new Error("A transcrição recebida está vazia ou é curta demais para análise. Tente novamente.");
  return { videoId, transcript, language: track.languageCode };
}
