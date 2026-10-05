/**
 * caption-parser.ts
 * Implementação limpa e testada localmente para extração e sanitização
 * de legendas do player do YouTube.
 */

export interface ExtractedCaptions {
  videoId: string;
  transcript: string;
  language: string;
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

interface YouTubeCaptionJsonSegment { utf8?: string }
interface YouTubeCaptionJsonEvent { tStartMs?: number; dDurationMs?: number; segs?: YouTubeCaptionJsonSegment[] }
interface YouTubeCaptionJsonResponse { events?: YouTubeCaptionJsonEvent[] }

interface YouTubePlayerResponse { captions?: { playerCaptionsTracklistRenderer?: { captionTracks?: CaptionTrack[] } } }
interface YouTubeMoviePlayer extends Element { getPlayerResponse?: () => YouTubePlayerResponse }

export function sanitizeTranscriptText(rawText: string | null | undefined): string {
  if (!rawText) return "";
  return rawText
    .replace(/<[^>]+>/g, " ")
    .replace(/\[[\p{L}\s]+\]/gu, " ")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
}

export function parseCaptionXml(xmlText: string): CaptionSegment[] {
  if (!xmlText.trim()) return [];
  const parser = new DOMParser();
  const doc = parser.parseFromString(xmlText, "text/xml");
  if (doc.querySelector("parsererror")) return [];
  const nodes = Array.from(doc.querySelectorAll("text"));
  return nodes
    .map((n): CaptionSegment | null => {
      const text = sanitizeTranscriptText(n.textContent ?? "");
      const start = Number.parseFloat(n.getAttribute("start") ?? "");
      const dur = Number.parseFloat(n.getAttribute("dur") ?? "");
      if (!text || !Number.isFinite(start) || !Number.isFinite(dur)) return null;
      return { text, start, duration: dur };
    })
    .filter((s): s is CaptionSegment => s !== null);
}

export function parseCaptionJson(jsonText: string): CaptionSegment[] {
  if (!jsonText.trim()) return [];
  try {
    const data = JSON.parse(jsonText) as YouTubeCaptionJsonResponse;
    if (!Array.isArray(data.events)) return [];
    return data.events
      .map((ev): CaptionSegment | null => {
        if (!Array.isArray(ev.segs) || ev.segs.length === 0) return null;
        if (typeof ev.tStartMs !== "number" || typeof ev.dDurationMs !== "number") return null;
        const raw = ev.segs.map((s) => s.utf8 ?? "").join("");
        const text = sanitizeTranscriptText(raw.replace(/^\s*>>\s*/, ""));
        if (!text) return null;
        return { text, start: ev.tStartMs / 1000, duration: ev.dDurationMs / 1000 };
      })
      .filter((s): s is CaptionSegment => s !== null);
  } catch {
    return [];
  }
}

export function parseCaptionBody(body: string): string {
  const trimmed = body.trimStart();
  if (trimmed.startsWith("{")) {
    try {
      const data = JSON.parse(body) as YouTubeCaptionJsonResponse;
      const transcript = (data.events ?? []).flatMap((e) => e.segs ?? []).map((s) => s.utf8 ?? "").join("");
      return sanitizeTranscriptText(transcript.replace(/(^|\n)\s*>>\s*/g, "$1"));
    } catch {
      // fallback to XML
    }
  }
  const parser = new DOMParser();
  const doc = parser.parseFromString(body, "text/xml");
  if (doc.querySelector("parsererror")) throw new Error("Não foi possível interpretar as legendas.");
  const text = Array.from(doc.querySelectorAll("text, p")).map((n) => n.textContent ?? "").join(" ");
  return sanitizeTranscriptText(text);
}

export function selectCaptionTrack(tracks: CaptionTrack[]): CaptionTrack | null {
  if (!tracks || tracks.length === 0) return null;
  const pt = tracks.find((t) => t.languageCode.toLowerCase().startsWith("pt"));
  return pt ?? tracks[0];
}

export function getCaptionTracksFromPlayer(): CaptionTrack[] {
  const player = document.querySelector("#movie_player") as YouTubeMoviePlayer | null;
  if (!player || typeof player.getPlayerResponse !== "function") return [];
  try {
    const resp = player.getPlayerResponse();
    return resp?.captions?.playerCaptionsTracklistRenderer?.captionTracks ?? [];
  } catch (e) {
    console.warn("[EvidencIA] getCaptionTracksFromPlayer failed:", e);
    return [];
  }
}

export async function extractCaptionsFromPage(videoId: string): Promise<ExtractedCaptions | null> {
  try {
    const tracks = getCaptionTracksFromPlayer();
    if (!tracks.length) return null;
    const track = selectCaptionTrack(tracks);
    if (!track) return null;
    const res = await fetch(track.baseUrl);
    if (!res.ok) return null;
    const body = await res.text();
    const ct = res.headers.get("content-type") ?? "";
    const segments = (ct.includes("application/json") || body.trimStart().startsWith("{")) ? parseCaptionJson(body) : parseCaptionXml(body);
    const transcript = segments.map((s) => s.text).join(" ").trim();
    if (!transcript) return null;
    return { videoId, transcript, language: track.languageCode };
  } catch (e) {
    console.warn("[EvidencIA] extractCaptionsFromPage error:", e);
    return null;
  }
}
