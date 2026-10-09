import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import type { AnalyzeResponse, LocalCacheEntry } from "../../../shared/types/api";

const storage = { get: vi.fn(), set: vi.fn(), remove: vi.fn() };
vi.stubGlobal("chrome", { storage: { local: storage } });

const { CACHE_TTL_MS, isValidCacheEntry, getCachedResult, saveCachedResult } = await import("./cache-manager");

const mockAnalysis: AnalyzeResponse = {
  analysisMode: "evidence_first",
  videoId: "video-test",
  videoTitle: "Título do Vídeo de Teste",
  channelName: "Canal de Teste",
  publishedAt: "2026-01-15T00:00:00Z",
  processingTimeMs: 250,
  limitations: [],
  claims: [
    {
      id: "claim-1",
      text: "Alegação verificada",
      temporalContext: { videoPublishedAt: "2026-01-15T00:00:00Z" },
      uncertainty: "supported",
      evidence: [
        {
          sourceId: "src-1",
          relation: "supports",
          title: "Fonte Oficial",
          url: "https://fiocruz.br/estudo",
          publisher: "Fiocruz",
          publishedAt: "2026-01-15T00:00:00Z",
          provenance: { dataset: "factchecksbr", indexedAt: "2026-01-15T00:00:00Z" },
        },
      ],
    },
  ],
};

describe("cache-manager", () => {
  const FIXED_NOW = new Date("2026-09-30T12:00:00Z").getTime();

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(FIXED_NOW);
    storage.get.mockReset().mockResolvedValue({});
    storage.set.mockReset().mockResolvedValue(undefined);
    storage.remove.mockReset().mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  describe("isValidCacheEntry", () => {
    it("valida registro correto e íntegro", () => {
      const entry: LocalCacheEntry = {
        ...mockAnalysis,
        cacheVersion: 3, timestamp: FIXED_NOW - 1000,
        ttl: CACHE_TTL_MS,
      };
      expect(isValidCacheEntry(entry, "video-test", FIXED_NOW)).toBe(true);
    });

    it("valida registro íntegro quando ttl não foi explicitado (assume CACHE_TTL_MS)", () => {
      const entry = {
        ...mockAnalysis,
        cacheVersion: 3, timestamp: FIXED_NOW - 1000,
      };
      expect(isValidCacheEntry(entry, "video-test", FIXED_NOW)).toBe(true);
    });

    it("rejeita expiração exatamente no limite de 24 horas (86400000 ms)", () => {
      const expiredAtLimit: LocalCacheEntry = {
        ...mockAnalysis,
        cacheVersion: 3, timestamp: FIXED_NOW - 86400000,
        ttl: CACHE_TTL_MS,
      };
      expect(isValidCacheEntry(expiredAtLimit, "video-test", FIXED_NOW)).toBe(false);
    });

    it("aceita registro com 24 horas menos 1 milissegundo (86399999 ms)", () => {
      const validJustBeforeLimit: LocalCacheEntry = {
        ...mockAnalysis,
        cacheVersion: 3, timestamp: FIXED_NOW - 86399999,
        ttl: CACHE_TTL_MS,
      };
      expect(isValidCacheEntry(validJustBeforeLimit, "video-test", FIXED_NOW)).toBe(true);
    });

    it("rejeita registro com timestamp no futuro", () => {
      const futureEntry: LocalCacheEntry = {
        ...mockAnalysis,
        cacheVersion: 3, timestamp: FIXED_NOW + 1,
        ttl: CACHE_TTL_MS,
      };
      expect(isValidCacheEntry(futureEntry, "video-test", FIXED_NOW)).toBe(false);
    });

    it.each([0, -100, NaN, Infinity, -Infinity, null, undefined, "2026-09-30"])(
      "rejeita timestamp inválido: %s",
      (invalidTimestamp) => {
        const entry = {
          ...mockAnalysis,
          cacheVersion: 3, timestamp: invalidTimestamp,
          ttl: CACHE_TTL_MS,
        };
        expect(isValidCacheEntry(entry, "video-test", FIXED_NOW)).toBe(false);
      }
    );

    it("rejeita quando videoId difere do esperado", () => {
      const divergentEntry: LocalCacheEntry = {
        ...mockAnalysis,
        videoId: "outro-video",
        cacheVersion: 3, timestamp: FIXED_NOW - 500,
        ttl: CACHE_TTL_MS,
      };
      expect(isValidCacheEntry(divergentEntry, "video-test", FIXED_NOW)).toBe(false);
    });

    it("rejeita dados corrompidos ou incompletos", () => {
      expect(isValidCacheEntry(null, "video-test", FIXED_NOW)).toBe(false);
      expect(isValidCacheEntry(undefined, "video-test", FIXED_NOW)).toBe(false);
      expect(isValidCacheEntry("string-entry", "video-test", FIXED_NOW)).toBe(false);
      expect(isValidCacheEntry(42, "video-test", FIXED_NOW)).toBe(false);

      // Sem título do vídeo
      expect(
        isValidCacheEntry(
          { ...mockAnalysis, videoTitle: "", cacheVersion: 3, timestamp: FIXED_NOW - 100, ttl: CACHE_TTL_MS },
          "video-test",
          FIXED_NOW
        )
      ).toBe(false);

      // processingTimeMs inválido
      expect(
        isValidCacheEntry(
          { ...mockAnalysis, processingTimeMs: -1, cacheVersion: 3, timestamp: FIXED_NOW - 100, ttl: CACHE_TTL_MS },
          "video-test",
          FIXED_NOW
        )
      ).toBe(false);

      // analysisMode inválido
      expect(
        isValidCacheEntry(
          { ...mockAnalysis, analysisMode: "invalido", cacheVersion: 3, timestamp: FIXED_NOW - 100, ttl: CACHE_TTL_MS },
          "video-test",
          FIXED_NOW
        )
      ).toBe(false);
    });

    it("aplica TTL customizado válido e rejeita quando expirado pelo TTL específico", () => {
      const customTtl = 5000;
      const entry: LocalCacheEntry = {
        ...mockAnalysis,
        cacheVersion: 3, timestamp: FIXED_NOW - 5000,
        ttl: customTtl,
      };
      expect(isValidCacheEntry(entry, "video-test", FIXED_NOW)).toBe(false);

      const entryStillValid: LocalCacheEntry = {
        ...mockAnalysis,
        cacheVersion: 3, timestamp: FIXED_NOW - 4999,
        ttl: customTtl,
      };
      expect(isValidCacheEntry(entryStillValid, "video-test", FIXED_NOW)).toBe(true);
    });

    it.each([0, -500, NaN, Infinity, null, "86400000", CACHE_TTL_MS + 1])(
      "rejeita TTL corrompido ou superior a 24 horas: %s",
      (ttl) => {
        expect(isValidCacheEntry({ ...mockAnalysis, cacheVersion: 3, timestamp: FIXED_NOW - 1000, ttl }, "video-test", FIXED_NOW)).toBe(false);
      }
    );

  });

  describe("getCachedResult", () => {
    it("recupera resultado válido presente no storage", async () => {
      const validEntry: LocalCacheEntry = {
        ...mockAnalysis,
        cacheVersion: 3, timestamp: FIXED_NOW - 10000,
        ttl: CACHE_TTL_MS,
      };
      storage.get.mockResolvedValue({ "video-test": validEntry });

      const result = await getCachedResult("video-test", FIXED_NOW);
      expect(result).toEqual(validEntry);
      expect(storage.remove).not.toHaveBeenCalled();
    });

    it("retorna null quando chave não existe no storage", async () => {
      storage.get.mockResolvedValue({});
      const result = await getCachedResult("video-inexistente", FIXED_NOW);
      expect(result).toBeNull();
      expect(storage.remove).not.toHaveBeenCalled();
    });

    it("descarta e remove registro expirado (lazy eviction)", async () => {
      const expiredEntry: LocalCacheEntry = {
        ...mockAnalysis,
        cacheVersion: 3, timestamp: FIXED_NOW - 86400000,
        ttl: CACHE_TTL_MS,
      };
      storage.get.mockResolvedValue({ "video-test": expiredEntry });

      const result = await getCachedResult("video-test", FIXED_NOW);
      expect(result).toBeNull();
      expect(storage.remove).toHaveBeenCalledWith("video-test");
    });

    it("remove registro nulo como corrompido", async () => {
      storage.get.mockResolvedValue({ "video-test": null });
      expect(await getCachedResult("video-test", FIXED_NOW)).toBeNull();
      expect(storage.remove).toHaveBeenCalledWith("video-test");
    });

    it("descarta e remove registro corrompido", async () => {
      storage.get.mockResolvedValue({ "video-test": { videoId: "video-test", corrompido: true } });

      const result = await getCachedResult("video-test", FIXED_NOW);
      expect(result).toBeNull();
      expect(storage.remove).toHaveBeenCalledWith("video-test");
    });

    it("descarta e remove registro com videoId divergente", async () => {
      const divergent: LocalCacheEntry = {
        ...mockAnalysis,
        videoId: "outro-id",
        cacheVersion: 3, timestamp: FIXED_NOW - 100,
        ttl: CACHE_TTL_MS,
      };
      storage.get.mockResolvedValue({ "video-test": divergent });

      const result = await getCachedResult("video-test", FIXED_NOW);
      expect(result).toBeNull();
      expect(storage.remove).toHaveBeenCalledWith("video-test");
    });

    it("não falha se remoção do storage rejeitar", async () => {
      const expiredEntry: LocalCacheEntry = {
        ...mockAnalysis,
        cacheVersion: 3, timestamp: FIXED_NOW - 86400000,
        ttl: CACHE_TTL_MS,
      };
      storage.get.mockResolvedValue({ "video-test": expiredEntry });
      storage.remove.mockRejectedValue(new Error("Storage I/O failure"));

      const result = await getCachedResult("video-test", FIXED_NOW);
      expect(result).toBeNull();
    });

    it("retorna null de forma resiliente em falha de leitura do storage", async () => {
      storage.get.mockRejectedValue(new Error("Storage unavailable"));

      const result = await getCachedResult("video-test", FIXED_NOW);
      expect(result).toBeNull();
    });
  });

  describe("saveCachedResult", () => {
    it("persiste dados de checagem com novo timestamp e TTL de 24h", async () => {
      await saveCachedResult(mockAnalysis, "video-test", FIXED_NOW);
      expect(storage.set).toHaveBeenCalledWith({
        "video-test": {
          ...mockAnalysis,
          cacheVersion: 3, timestamp: FIXED_NOW,
          ttl: CACHE_TTL_MS,
        },
      });
    });

    it("não persiste resposta que não atenda ao contrato ou com videoId divergente", async () => {
      const invalidData = { ...mockAnalysis, processingTimeMs: -1 };
      await saveCachedResult(invalidData as any, "video-test", FIXED_NOW);
      expect(storage.set).not.toHaveBeenCalled();

      await saveCachedResult(mockAnalysis, "outro-id", FIXED_NOW);
      expect(storage.set).not.toHaveBeenCalled();
    });

    it("não lança erro se storage.set falhar (ex.: cota excedida)", async () => {
      storage.set.mockRejectedValue(new Error("QUOTA_BYTES_PER_ITEM quota exceeded"));
      await expect(saveCachedResult(mockAnalysis, "video-test", FIXED_NOW)).resolves.toBeUndefined();
    });
  });
});


it("invalida caches da versão anterior à correção factual", () => {
  expect(isValidCacheEntry({ ...mockAnalysis, timestamp: Date.now() - 1, ttl: CACHE_TTL_MS }, "video-test")).toBe(false);
});

it("invalida versão 2 potencialmente preenchida com descrição", () => {
  expect(isValidCacheEntry({ cacheVersion: 2 }, "video", Date.now())).toBe(false);
});
