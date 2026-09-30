/**
 * Módulo de extração e higienização de legendas do YouTube.
 *
 * Rastreabilidade:
 * - HU05 — Ingestão e Processamento de Transcrição
 * - HU10 — Notificação Rápida de Ausência de Transcrição
 * - RF-02
 * - RF-08
 * - RNF-06
 *
 * Responsabilidades:
 * 1. Identificar as faixas de legenda disponíveis no player.
 * 2. Selecionar preferencialmente uma faixa em português.
 * 3. Obter o conteúdo da legenda.
 * 4. Converter a resposta em segmentos estruturados.
 * 5. Higienizar o texto sem alterar seu significado.
 * 6. Consolidar os segmentos em uma transcrição textual.
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

interface YouTubeCaptionJsonSegment {
  utf8?: string;
  tOffsetMs?: number;
  acAsrConf?: number;
  isSpeakerChange?: number;
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

/**
 * Representa somente a parte do player do YouTube
 * utilizada pela EvidencIA.
 *
 * Não precisamos modelar toda a API interna do player.
 */
interface YouTubeMoviePlayer extends Element {
  getPlayerResponse?: () => YouTubePlayerResponse;
}

/**
 * Higieniza um trecho textual de legenda.
 */
export function sanitizeTranscriptText(
  rawText: string | null | undefined
): string {
  if (!rawText) {
    return "";
  }

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

/**
 * Converte o XML retornado pelo serviço de legendas
 * em segmentos estruturados.
 */
export function parseCaptionXml(
  xmlText: string
): CaptionSegment[] {
  if (!xmlText.trim()) {
    return [];
  }

  const parser = new DOMParser();

  const xmlDocument = parser.parseFromString(
    xmlText,
    "text/xml"
  );

  if (xmlDocument.querySelector("parsererror")) {
    return [];
  }

  const textElements = Array.from(
    xmlDocument.querySelectorAll("text")
  );

  return textElements
    .map((element): CaptionSegment | null => {
      const text = sanitizeTranscriptText(
        element.textContent ?? ""
      );

      const start = Number.parseFloat(
        element.getAttribute("start") ?? ""
      );

      const duration = Number.parseFloat(
        element.getAttribute("dur") ?? ""
      );

      if (
        !text ||
        !Number.isFinite(start) ||
        !Number.isFinite(duration)
      ) {
        return null;
      }

      return {
        text,
        start,
        duration,
      };
    })
    .filter(
      (segment): segment is CaptionSegment =>
        segment !== null
    );
}

/**
 * Converte o formato JSON3 utilizado pelo endpoint
 * timedtext do YouTube em segmentos internos.
 *
 * O formato observado utiliza:
 *
 * events[].tStartMs
 * events[].dDurationMs
 * events[].segs[].utf8
 */
export function parseCaptionJson(
  jsonText: string
): CaptionSegment[] {
  if (!jsonText.trim()) {
    return [];
  }

  try {
    const data = JSON.parse(
      jsonText
    ) as YouTubeCaptionJsonResponse;

    if (!Array.isArray(data.events)) {
      return [];
    }

    return data.events
      .map(
        (
          event
        ): CaptionSegment | null => {
          if (
            !Array.isArray(event.segs) ||
            event.segs.length === 0
          ) {
            return null;
          }

          if (
            typeof event.tStartMs !==
              "number" ||
            typeof event.dDurationMs !==
              "number"
          ) {
            return null;
          }

          const rawText = event.segs
            .map(
              (segment) =>
                segment.utf8 ?? ""
            )
            .join("");

          /*
           * Remove o marcador textual de
           * mudança de locutor (" >> ").
           *
           * Não removemos a fala propriamente
           * dita.
           */
          const text =
            sanitizeTranscriptText(
              rawText.replace(
                /^\s*>>\s*/,
                ""
              )
            );

          /*
           * Eventos contendo somente quebra
           * de linha ou marcadores removidos
           * pelo sanitizador são descartados.
           */
          if (!text) {
            return null;
          }

          return {
            text,

            /*
             * O modelo interno trabalha
             * em segundos.
             */
            start:
              event.tStartMs / 1000,

            duration:
              event.dDurationMs / 1000,
          };
        }
      )
      .filter(
        (
          segment
        ): segment is CaptionSegment =>
          segment !== null
      );
  } catch {
    return [];
  }
}

/**
 * Seleciona a faixa de legenda.
 *
 * Regra:
 * 1. português;
 * 2. primeira faixa disponível.
 */
export function selectCaptionTrack(
  tracks: CaptionTrack[]
): CaptionTrack | null {
  if (tracks.length === 0) {
    return null;
  }

  const portugueseTrack = tracks.find((track) =>
    track.languageCode
      .toLowerCase()
      .startsWith("pt")
  );

  return portugueseTrack ?? tracks[0];
}

/**
 * Obtém as faixas diretamente do player do YouTube.
 *
 * Esta abordagem substitui a dependência anterior de:
 *
 * window.ytInitialPlayerResponse
 *
 * porque a validação no YouTube real demonstrou que
 * essa propriedade pode estar indisponível enquanto
 * #movie_player.getPlayerResponse() fornece os dados.
 */
export function getCaptionTracksFromPlayer():
  CaptionTrack[] {
  const moviePlayer =
    document.querySelector(
      "#movie_player"
    ) as YouTubeMoviePlayer | null;

  if (!moviePlayer) {
    return [];
  }

  if (
    typeof moviePlayer.getPlayerResponse !==
    "function"
  ) {
    return [];
  }

  try {
    const playerResponse =
      moviePlayer.getPlayerResponse();

    const tracks =
      playerResponse
        ?.captions
        ?.playerCaptionsTracklistRenderer
        ?.captionTracks;

    return tracks ?? [];
  } catch (error) {
    console.warn(
      "[EvidencIA] Não foi possível obter as faixas de legenda do player:",
      error
    );

    return [];
  }
}

/**
 * Fluxo principal da HU05.
 */
export async function extractCaptionsFromPage(
  videoId: string
): Promise<ExtractedCaptions | null> {
  try {
    /*
     * 1. Obtém as faixas diretamente
     *    do player real do YouTube.
     */
    const tracks =
      getCaptionTracksFromPlayer();

    if (tracks.length === 0) {
      return null;
    }

    /*
     * 2. Seleciona preferencialmente
     *    português.
     */
    const selectedTrack =
      selectCaptionTrack(tracks);

    if (!selectedTrack) {
      return null;
    }

    /*
     * 3. Busca o conteúdo da legenda.
     */
    const response = await fetch(
      selectedTrack.baseUrl
    );

    if (!response.ok) {
      return null;
    }

    // /*
    //  * 4. Obtém o conteúdo textual.
    //  */
    // const xmlText = await response.text();

    // /*
    //  * 5. Converte em segmentos.
    //  */
    // const segments =
    //   parseCaptionXml(xmlText);

    // if (segments.length === 0) {
    //   return null;
    // }
    const captionText =
  await response.text();

const contentType =
  response.headers
    .get("content-type")
    ?.toLowerCase() ?? "";

let segments: CaptionSegment[];

if (
  contentType.includes(
    "application/json"
  ) ||
  captionText.trimStart().startsWith("{")
) {
  segments =
    parseCaptionJson(captionText);
} else {
  segments =
    parseCaptionXml(captionText);
}

    /*
     * 6. Consolida os segmentos.
     */
    const transcript = segments
      .map((segment) => segment.text)
      .join(" ")
      .trim();

    if (!transcript) {
      return null;
    }

    /*
     * 7. Mantém o contrato esperado
     *    pelo restante da extensão.
     */
    return {
      videoId,
      transcript,
      language:
        selectedTrack.languageCode,
    };
  } catch (error) {
    console.warn(
      "[EvidencIA] Erro ao extrair legendas do player:",
      error
    );

    return null;
  }
}