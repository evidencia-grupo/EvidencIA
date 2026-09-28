/**
 * Módulo de extração e higienização de legendas do YouTube
 * Rastreabilidade: HU05, HU10, RF-02, RF-08, RNF-06
 */

export interface ExtractedCaptions {
  videoId: string;
  transcript: string;
  language: string;
}

/**
 * Higieniza o texto bruto de legendas removendo timestamps, tags HTML e caracteres espúrios.
 */
export function sanitizeTranscriptText(rawText: string): string {
  if (!rawText) return "";

  return rawText
    .replace(/<[^>]+>/g, " ") // Remove tags HTML/XML (<font>, <p>, etc)
    .replace(/\[[a-zA-Z\s]+\]/g, "") // Remove marcadores como [Música], [Aplausos]
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ") // Colapsa múltiplos espaços
    .trim();
}

/**
 * Tenta capturar as legendas expostas no player do YouTube na página ativa.
 */
export async function extractCaptionsFromPage(videoId: string): Promise<ExtractedCaptions | null> {
  try {
    // 1. Tenta acessar os dados do player injetados na janela (ytInitialPlayerResponse)
    const scriptTag = document.querySelector("#movie_player");
    if (!scriptTag) {
      return null;
    }

    // Busca faixas de legendas no objeto global de resposta do player se disponível
    const playerResponse = (window as unknown as { ytInitialPlayerResponse?: { captions?: { playerCaptionsTracklistRenderer?: { captionTracks?: Array<{ baseUrl: string; languageCode: string }> } } } }).ytInitialPlayerResponse;

    const tracks = playerResponse?.captions?.playerCaptionsTracklistRenderer?.captionTracks;

    if (!tracks || tracks.length === 0) {
      return null; // Vídeo sem legendas disponíveis (HU10)
    }

    // Prioriza português (pt ou pt-BR) ou pega a primeira faixa disponível
    const selectedTrack =
      tracks.find((t) => t.languageCode.startsWith("pt")) || tracks[0];

    const response = await fetch(selectedTrack.baseUrl);
    if (!response.ok) return null;

    const xmlText = await response.text();
    const cleanText = sanitizeTranscriptText(xmlText);

    if (cleanText.length < 50) {
      return null;
    }

    return {
      videoId,
      transcript: cleanText,
      language: selectedTrack.languageCode || "pt-BR",
    };
  } catch (error) {
    console.warn("[EvidencIA] Erro ao extrair legendas do player:", error);
    return null;
  }
}
