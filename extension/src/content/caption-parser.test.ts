// @vitest-environment jsdom

import { describe, expect, it } from "vitest";

import {
  extractCaptionsFromPage,
  getCaptionTracksFromPlayer,
  parseCaptionBody,
  parseCaptionJson,
  parseCaptionXml,
  sanitizeTranscriptText,
  selectCaptionTrack,
} from "./caption-parser";


describe("parseCaptionJson", () => {
  it("deve converter eventos JSON3 em segmentos", () => {
    const json = JSON.stringify({
      events: [
        {
          tStartMs: 440,
          dDurationMs: 4640,
          segs: [
            { utf8: "Tá" },
            {
              utf8: " começando",
              tOffsetMs: 240,
            },
            {
              utf8: " o",
              tOffsetMs: 840,
            },
            {
              utf8: " seu",
              tOffsetMs: 920,
            },
            {
              utf8: " programa",
              tOffsetMs: 1159,
            },
            {
              utf8: " de",
              tOffsetMs: 1519,
            },
            {
              utf8: " saúde",
              tOffsetMs: 1880,
            },
          ],
        },
      ],
    });

    expect(
      parseCaptionJson(json)
    ).toEqual([
      {
        text:
          "Tá começando o seu programa de saúde",
        start: 0.44,
        duration: 4.64,
      },
    ]);
  });

  it("deve ignorar eventos sem texto", () => {
    const json = JSON.stringify({
      events: [
        {
          tStartMs: 2869,
          dDurationMs: 2211,
          segs: [
            {
              utf8: "\n",
            },
          ],
        },
      ],
    });

    expect(
      parseCaptionJson(json)
    ).toEqual([]);
  });

  it("deve remover marcadores de musica", () => {
    const json = JSON.stringify({
      events: [
        {
          tStartMs: 7359,
          dDurationMs: 4320,
          segs: [
            { utf8: "tema" },
            { utf8: " muito" },
            { utf8: " legal" },
            { utf8: " [música]" },
            { utf8: " só" },
          ],
        },
      ],
    });

    expect(
      parseCaptionJson(json)
    ).toEqual([
      {
        text:
          "tema muito legal só",
        start: 7.359,
        duration: 4.32,
      },
    ]);
  });

  it("deve tratar mudanca de locutor", () => {
    const json = JSON.stringify({
      events: [
        {
          tStartMs: 11679,
          dDurationMs: 4000,
          segs: [
            {
              utf8: ">> Tudo",
              isSpeakerChange: 1,
            },
            {
              utf8: " bem.",
              tOffsetMs: 201,
            },
          ],
        },
      ],
    });

    expect(
      parseCaptionJson(json)
    ).toEqual([
      {
        text: "Tudo bem.",
        start: 11.679,
        duration: 4,
      },
    ]);
  });

  it("deve retornar vazio para JSON invalido", () => {
    expect(
      parseCaptionJson(
        "{json-invalido"
      )
    ).toEqual([]);
  });
});

/**
 * Testes da higienização textual.
 */
describe("sanitizeTranscriptText", () => {
  it("deve remover tags HTML e entidades codificadas", () => {
    const raw =
      "<font color='#fff'>Texto com &quot;aspas&quot; e &#39;apostrofos&#39;</font>";

    const sanitized =
      sanitizeTranscriptText(raw);

    expect(sanitized).toBe(
      'Texto com "aspas" e \'apostrofos\''
    );
  });

  it("deve remover marcadores de audio como [Musica] e [Aplausos]", () => {
    const raw =
      "[Musica] Ola pessoal [Aplausos] sejam bem-vindos";

    const sanitized =
      sanitizeTranscriptText(raw);

    expect(sanitized).toBe(
      "Ola pessoal sejam bem-vindos"
    );
  });

  it("deve colapsar multiplos espacos e quebras de linha", () => {
    const raw =
      "Texto   com    muitos      espacos\n\ne quebras";

    const sanitized =
      sanitizeTranscriptText(raw);

    expect(sanitized).toBe(
      "Texto com muitos espacos e quebras"
    );
  });

  it("deve retornar string vazia para entrada vazia ou nula", () => {
    expect(
      sanitizeTranscriptText("")
    ).toBe("");

    expect(
      sanitizeTranscriptText(null)
    ).toBe("");

    expect(
      sanitizeTranscriptText(undefined)
    ).toBe("");
  });

  it("deve remover marcadores com caracteres acentuados", () => {
    const raw =
      "[Música] Olá pessoal [Aplausos]";

    expect(
      sanitizeTranscriptText(raw)
    ).toBe("Olá pessoal");
  });

  it("deve preservar colchetes que fazem parte do conteúdo", () => {
    const raw =
      "Use o vetor [1, 2, 3] no exemplo";

    expect(
      sanitizeTranscriptText(raw)
    ).toBe(
      "Use o vetor [1, 2, 3] no exemplo"
    );
  });

  it("deve decodificar entidades HTML básicas", () => {
    const raw =
      "5 &lt; 10 &amp;&amp; 10 &gt; 5";

    expect(
      sanitizeTranscriptText(raw)
    ).toBe(
      "5 < 10 && 10 > 5"
    );
  });

  it("deve preservar caracteres Unicode", () => {
    const raw =
      "Olá, inteligência artificial! Informação, ação e coração.";

    expect(
      sanitizeTranscriptText(raw)
    ).toBe(raw);
  });
});

/**
 * Testes do parser XML.
 */
describe("parseCaptionXml", () => {
  it("deve converter XML em segmentos estruturados", () => {
    const xml = `
      <transcript>
        <text start="1.5" dur="2.0">
          Olá mundo
        </text>

        <text start="3.5" dur="1.25">
          Segunda legenda
        </text>
      </transcript>
    `;

    const result =
      parseCaptionXml(xml);

    expect(result).toEqual([
      {
        text: "Olá mundo",
        start: 1.5,
        duration: 2.0,
      },
      {
        text: "Segunda legenda",
        start: 3.5,
        duration: 1.25,
      },
    ]);
  });

  it("deve retornar array vazio para XML vazio", () => {
    expect(
      parseCaptionXml("")
    ).toEqual([]);

    expect(
      parseCaptionXml("   ")
    ).toEqual([]);
  });

  it("deve ignorar segmentos sem timestamps validos", () => {
    const xml = `
      <transcript>
        <text start="invalido" dur="2">
          Segmento invalido
        </text>

        <text start="10" dur="3">
          Segmento valido
        </text>
      </transcript>
    `;

    expect(
      parseCaptionXml(xml)
    ).toEqual([
      {
        text: "Segmento valido",
        start: 10,
        duration: 3,
      },
    ]);
  });
});

/**
 * Testes da estratégia de seleção da faixa de legenda.
 */
describe("selectCaptionTrack", () => {
  it("deve priorizar uma faixa em portugues", () => {
    const tracks = [
      {
        baseUrl:
          "https://example.com/captions-en",
        languageCode: "en",
      },
      {
        baseUrl:
          "https://example.com/captions-pt",
        languageCode: "pt-BR",
      },
    ];

    const selected =
      selectCaptionTrack(tracks);

    expect(selected).toEqual(
      tracks[1]
    );
  });

  it("deve reconhecer variantes de portugues", () => {
    const tracks = [
      {
        baseUrl:
          "https://example.com/captions-en",
        languageCode: "en",
      },
      {
        baseUrl:
          "https://example.com/captions-pt-pt",
        languageCode: "pt-PT",
      },
    ];

    const selected =
      selectCaptionTrack(tracks);

    expect(selected).toEqual(
      tracks[1]
    );
  });

  it("deve usar a primeira faixa quando portugues nao estiver disponivel", () => {
    const tracks = [
      {
        baseUrl:
          "https://example.com/captions-en",
        languageCode: "en",
      },
      {
        baseUrl:
          "https://example.com/captions-es",
        languageCode: "es",
      },
    ];

    const selected =
      selectCaptionTrack(tracks);

    expect(selected).toEqual(
      tracks[0]
    );
  });

  it("deve retornar null quando nao houver faixas", () => {
    expect(
      selectCaptionTrack([])
    ).toBeNull();
    expect(selectCaptionTrack(null)).toBeNull();
    expect(selectCaptionTrack(undefined)).toBeNull();
  });
});

describe("getCaptionTracksFromPlayer", () => {
  it("deve retornar lista vazia se elemento do player nao existir", () => {
    document.body.innerHTML = "<div></div>";
    expect(getCaptionTracksFromPlayer()).toEqual([]);
  });

  it("deve retornar lista vazia se player nao tiver funcao getPlayerResponse", () => {
    document.body.innerHTML = '<div id="movie_player"></div>';
    expect(getCaptionTracksFromPlayer()).toEqual([]);
  });

  it("deve extrair faixas de legenda quando getPlayerResponse retornar dados", () => {
    document.body.innerHTML = '<div id="movie_player"></div>';
    const player = document.querySelector("#movie_player") as any;
    player.getPlayerResponse = () => ({
      captions: {
        playerCaptionsTracklistRenderer: {
          captionTracks: [{ baseUrl: "https://example.com/pt", languageCode: "pt" }],
        },
      },
    });

    expect(getCaptionTracksFromPlayer()).toEqual([
      { baseUrl: "https://example.com/pt", languageCode: "pt" },
    ]);
  });

  it("deve retornar lista vazia se captions nao estiver presente", () => {
    document.body.innerHTML = '<div id="movie_player"></div>';
    const player = document.querySelector("#movie_player") as any;
    player.getPlayerResponse = () => ({});

    expect(getCaptionTracksFromPlayer()).toEqual([]);
  });

  it("deve capturar excecao e retornar lista vazia se getPlayerResponse falhar", () => {
    document.body.innerHTML = '<div id="movie_player"></div>';
    const player = document.querySelector("#movie_player") as any;
    player.getPlayerResponse = () => {
      throw new Error("Erro de player simulado");
    };

    expect(getCaptionTracksFromPlayer()).toEqual([]);
  });
});

describe("parseCaptionBody", () => {
  it("deve lancar erro se comecar com { mas for JSON invalido", () => {
    expect(() => parseCaptionBody("{ invalid json")).toThrow(
      "Não foi possível interpretar as legendas. Tente novamente."
    );
  });

  it("deve lancar erro se for XML malformado", () => {
    expect(() => parseCaptionBody("<invalido>")).toThrow(
      "Não foi possível interpretar as legendas. Tente novamente."
    );
  });
});

describe("extractCaptionsFromPage", () => {
  it("deve rejeitar se URL da legenda tiver origem ou rota invalida", async () => {
    const invalidAvailability = {
      tracks: [{ baseUrl: "https://evil.com/api/timedtext", languageCode: "pt" }],
    };
    await expect(
      extractCaptionsFromPage("video-1", undefined, invalidAvailability)
    ).rejects.toThrow("Endereço de legendas inválido.");
  });

  it("deve rejeitar se URL da legenda for malformada", async () => {
    const invalidAvailability = {
      tracks: [{ baseUrl: "not-a-valid-url", languageCode: "pt" }],
    };
    await expect(
      extractCaptionsFromPage("video-1", undefined, invalidAvailability)
    ).rejects.toThrow("Endereço de legendas inválido.");
  });
});