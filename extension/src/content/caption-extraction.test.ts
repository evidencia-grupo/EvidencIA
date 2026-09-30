// @vitest-environment jsdom

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { extractCaptionsFromPage } from "./caption-parser";

interface MockMoviePlayer extends HTMLElement {
  getPlayerResponse?: () => {
    captions?: {
      playerCaptionsTracklistRenderer?: {
        captionTracks?: Array<{
          baseUrl: string;
          languageCode: string;
        }>;
      };
    };
  };
}

function createMockPlayer(
  tracks: Array<{
    baseUrl: string;
    languageCode: string;
  }>,
): MockMoviePlayer {
  const player = document.createElement("div") as MockMoviePlayer;

  player.id = "movie_player";

  player.getPlayerResponse = () => ({
    captions: {
      playerCaptionsTracklistRenderer: {
        captionTracks: tracks,
      },
    },
  });

  document.body.appendChild(player);

  return player;
}

describe("extractCaptionsFromPage", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    vi.restoreAllMocks();
  });

  afterEach(() => {
    document.body.innerHTML = "";
    vi.restoreAllMocks();
  });

  it("deve extrair e consolidar legendas", async () => {
    createMockPlayer([
      {
        baseUrl: "https://example.com/captions",
        languageCode: "pt",
      },
    ]);

    const xml = `
          <transcript>
            <text start="0" dur="2">
              Olá mundo
            </text>

            <text start="2" dur="3">
              Esta é uma legenda de teste
            </text>
          </transcript>
        `;

    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(xml, {
        status: 200,
      }),
    );

    const result = await extractCaptionsFromPage("video-123");

    expect(fetchMock).toHaveBeenCalledWith("https://example.com/captions");

    expect(result).toEqual({
      videoId: "video-123",
      transcript: "Olá mundo Esta é uma legenda de teste",
      language: "pt",
    });
  });

  it("deve priorizar portugues", async () => {
    createMockPlayer([
      {
        baseUrl: "https://example.com/en",
        languageCode: "en",
      },
      {
        baseUrl: "https://example.com/pt",
        languageCode: "pt",
      },
    ]);

    const xml = `
          <transcript>
            <text start="0" dur="2">
              Legenda em português
            </text>
          </transcript>
        `;

    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(xml, {
        status: 200,
      }),
    );

    const result = await extractCaptionsFromPage("video-pt");

    expect(fetchMock).toHaveBeenCalledWith("https://example.com/pt");

    expect(result?.language).toBe("pt");
  });

  it("deve retornar null sem player", async () => {
    const result = await extractCaptionsFromPage("sem-player");

    expect(result).toBeNull();
  });

  it("deve retornar null quando getPlayerResponse nao existir", async () => {
    const player = document.createElement("div");

    player.id = "movie_player";

    document.body.appendChild(player);

    const result = await extractCaptionsFromPage("sem-api-player");

    expect(result).toBeNull();
  });

  it("deve retornar null sem faixas", async () => {
    createMockPlayer([]);

    const result = await extractCaptionsFromPage("sem-legendas");

    expect(result).toBeNull();
  });

  it("deve retornar null quando fetch falhar", async () => {
    createMockPlayer([
      {
        baseUrl: "https://example.com/falha",
        languageCode: "pt",
      },
    ]);

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("", {
        status: 500,
      }),
    );

    const result = await extractCaptionsFromPage("erro-http");

    expect(result).toBeNull();
  });

  it("deve retornar null para legenda vazia", async () => {
    createMockPlayer([
      {
        baseUrl: "https://example.com/vazia",
        languageCode: "pt",
      },
    ]);

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("<transcript></transcript>", {
        status: 200,
      }),
    );

    const result = await extractCaptionsFromPage("xml-vazio");

    expect(result).toBeNull();
  });
});

it("deve processar resposta JSON do timedtext", async () => {
  createMockPlayer([
    {
      baseUrl: "https://example.com/timedtext",
      languageCode: "pt",
    },
  ]);

  const json = JSON.stringify({
    events: [
      {
        tStartMs: 440,
        dDurationMs: 4640,
        segs: [{ utf8: "Tá" }, { utf8: " começando" }, { utf8: " o programa" }],
      },
      {
        tStartMs: 5080,
        dDurationMs: 4639,
        segs: [{ utf8: "bem-vindo." }],
      },
    ],
  });

  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(json, {
      status: 200,
      headers: {
        "Content-Type": "application/json; charset=UTF-8",
      },
    }),
  );

  const result = await extractCaptionsFromPage("video-json");

  expect(result).toEqual({
    videoId: "video-json",
    transcript: "Tá começando o programa bem-vindo.",
    language: "pt",
  });
});
