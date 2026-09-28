import { beforeEach, afterEach, expect, it, vi } from "vitest";
const storage = { get: vi.fn(), set: vi.fn(), remove: vi.fn() };
vi.stubGlobal("chrome", { runtime: { onMessage: { addListener: vi.fn() } }, storage: { local: storage } });
const { getCachedResult, handleAnalyzeRequest } = await import("./service-worker");
const data = { videoId: "video", summary: "Síntese", claims: [], sources: [], score: 80 };
const payload = { videoId: "video", videoTitle: "Título", channelName: "Canal", transcript: "transcrição" };
beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-09-28T12:00:00Z"));
  storage.get.mockResolvedValue({});
  storage.set.mockResolvedValue(undefined);
  storage.remove.mockResolvedValue(undefined);
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => data }));
});
afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); });
it("recupera cache recente sem rede", async () => {
  storage.get.mockResolvedValue({ video: { ...data, timestamp: Date.now() - 1 } });
  expect(await handleAnalyzeRequest(payload)).toMatchObject(data);
  expect(fetch).not.toHaveBeenCalled();
});
it.each([86400000, 86400001, -1, NaN])("descarta idade inválida/expirada %s", async age => {
  storage.get.mockResolvedValue({ video: { ...data, timestamp: Date.now() - age } });
  expect(await getCachedResult("video")).toBeNull();
  expect(storage.remove).toHaveBeenCalledWith("video");
});
it("tolera falha de leitura e persistência", async () => {
  storage.get.mockRejectedValue(new Error("storage"));
  storage.set.mockRejectedValue(new Error("quota"));
  expect(await handleAnalyzeRequest(payload)).toEqual(data);
});
it("salva apenas análise bem-sucedida com TTL de 24h", async () => {
  await handleAnalyzeRequest(payload);
  expect(storage.set).toHaveBeenCalledWith({ video: { ...data, timestamp: Date.now(), ttl: 86400000 } });
});
it("não persiste erro HTTP", async () => {
  vi.mocked(fetch).mockResolvedValue({ ok: false, status: 503 } as Response);
  await expect(handleAnalyzeRequest(payload)).rejects.toThrow("HTTP 503");
  expect(storage.set).not.toHaveBeenCalled();
});
it("rejeita resposta de outro vídeo", async () => {
  vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => ({ ...data, videoId: "other" }) } as Response);
  await expect(handleAnalyzeRequest(payload)).rejects.toThrow("Resposta inválida");
  expect(storage.set).not.toHaveBeenCalled();
});
it("não inicia rede após prazo total", async () => {
  await expect(handleAnalyzeRequest(payload, Date.now())).rejects.toThrow("Tempo limite");
  expect(fetch).not.toHaveBeenCalled();
});
it("aborta inclusive leitura do corpo no orçamento restante", async () => {
  vi.mocked(fetch).mockImplementation(async (_url, init) => ({ ok: true, json: () => new Promise((_resolve, reject) => {
    init?.signal?.addEventListener("abort", () => reject(new Error("aborted")));
  }) }) as Response);
  const result = expect(handleAnalyzeRequest(payload, Date.now() + 100)).rejects.toThrow("Tempo limite");
  await vi.advanceTimersByTimeAsync(100);
  await result;
  expect(storage.set).not.toHaveBeenCalled();
});
