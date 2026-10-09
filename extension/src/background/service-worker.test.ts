import { beforeEach, afterEach, expect, it, vi } from "vitest";
const storage = { get: vi.fn(), set: vi.fn(), remove: vi.fn() };
vi.stubGlobal("chrome", {
  runtime: { id: "extension", onMessage: { addListener: vi.fn() } },
  storage: { local: storage },
  tabs: { create: vi.fn().mockResolvedValue({ id: 123 }) },
  scripting: { executeScript: vi.fn().mockResolvedValue([{ result: { tracks: [], metadata: { videoTitle: "t", channelName: "c" } } }]) },
});
const { getCachedResult, handleAnalyzeRequest, handleFeedbackRequest, getAuthToken, refreshAuthToken } = await import("./service-worker");
const listener = vi.mocked(chrome.runtime.onMessage.addListener).mock.calls[0][0];
const data = {
  analysisMode: "evidence_first",
  videoId: "video",
  videoTitle: "Título",
  channelName: "Canal",
  publishedAt: "2021-04-15T00:00:00Z",
  processingTimeMs: 100,
  claims: [],
  limitations: [],
};
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
  storage.get.mockResolvedValue({ video: { ...data, cacheVersion: 2, timestamp: Date.now() - 1 } });
  expect(await handleAnalyzeRequest(payload)).toMatchObject(data);
  expect(fetch).not.toHaveBeenCalled();
});
it.each([86400000, 86400001, -1, NaN])("descarta idade inválida/expirada %s", async age => {
  storage.get.mockResolvedValue({ video: { ...data, cacheVersion: 2, timestamp: Date.now() - age } });
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
  expect(storage.set).toHaveBeenCalledWith({ video: { ...data, cacheVersion: 2, timestamp: Date.now(), ttl: 86400000 } });
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

it("mensagens autorizadas recebem sucesso, erros e cache miss", async () => {
  const sender = { id: "extension", url: "https://www.youtube.com/watch?v=video" };
  const response = vi.fn();
  expect(listener({ type: "GET_CACHE", videoId: "video" }, sender, response)).toBe(true);
  await vi.advanceTimersByTimeAsync(0);
  expect(response).toHaveBeenCalledWith({ success: true, data: null });
  listener({ type: "ANALYZE_VIDEO", payload }, sender, response);
  await vi.advanceTimersByTimeAsync(0);
  expect(response).toHaveBeenCalledWith({ success: true, data });
  vi.mocked(fetch).mockRejectedValueOnce(new Error("Offline"));
  listener({ type: "ANALYZE_VIDEO", payload }, sender, response);
  await vi.advanceTimersByTimeAsync(0);
  expect(response).toHaveBeenCalledWith({ success: false, error: "Offline" });
  expect(listener({ type: "UNKNOWN" }, sender, response)).toBeUndefined();
  response.mockClear();
  const reads = storage.get.mock.calls.length;
  expect(listener({ type: "GET_CACHE" }, { ...sender, id: "other" }, response)).toBeUndefined();
  await vi.advanceTimersByTimeAsync(0);
  expect(storage.get).toHaveBeenCalledTimes(reads);
  listener({ type: "GET_CACHE" }, { ...sender, url: "https://evil.test" }, response);
  expect(response).not.toHaveBeenCalled();
});

it("processa envio de feedback assíncrono com sucesso", async () => {
  const sender = { id: "extension", url: "https://www.youtube.com/watch?v=video" };
  const response = vi.fn();
  const feedbackPayload = { videoId: "video", rating: "positive" as const };
  vi.mocked(fetch).mockResolvedValueOnce({
    ok: true,
    json: async () => ({ status: "received", message: "Feedback registrado" }),
  } as Response);

  listener({ type: "SUBMIT_FEEDBACK", payload: feedbackPayload }, sender, response);
  await vi.advanceTimersByTimeAsync(0);

  expect(response).toHaveBeenCalledWith({
    success: true,
    data: { status: "received", message: "Feedback registrado" },
  });
});

it("handleFeedbackRequest envia requisição POST para endpoint de feedback", async () => {
  const feedbackPayload = { videoId: "video", rating: "positive" as const };
  vi.mocked(fetch).mockResolvedValueOnce({
    ok: true,
    json: async () => ({ status: "received", message: "Feedback registrado" }),
  } as Response);

  const res = await handleFeedbackRequest(feedbackPayload);
  expect(res.status).toBe("received");
  expect(fetch).toHaveBeenCalledWith(
    "http://127.0.0.1:8000/api/v1/feedback",
    expect.objectContaining({
      method: "POST",
      body: JSON.stringify(feedbackPayload),
    })
  );
});



it("recebe Evidence-Only após o timeout de IA de 15 segundos", async () => {
  const evidenceOnly = { ...data, analysisMode: "evidence_only", limitations: ["Síntese temporariamente indisponível."] };
  vi.mocked(fetch).mockImplementation(() => new Promise(resolve => {
    setTimeout(() => resolve({ ok: true, json: async () => evidenceOnly } as Response), 15100);
  }));
  const result = handleAnalyzeRequest(payload);
  await vi.advanceTimersByTimeAsync(15100);
  expect(await result).toEqual(evidenceOnly);
});

it("rejeita handleFeedbackRequest quando servidor responde com erro", async () => {
  vi.mocked(fetch).mockResolvedValueOnce({ ok: false, status: 500 } as Response);
  await expect(handleFeedbackRequest({ videoId: "video", rating: "positive" })).rejects.toThrow(
    "Falha ao registrar feedback: HTTP 500"
  );
});

it("atualiza e recupera token de autenticação via refreshAuthToken e getAuthToken", async () => {
  vi.mocked(fetch).mockResolvedValueOnce({
    ok: true,
    json: async () => ({ token: "token-auth-xyz" }),
  } as Response);

  const token = await refreshAuthToken();
  expect(token).toBe("token-auth-xyz");
  expect(storage.set).toHaveBeenCalledWith({ evidencia_auth_token: "token-auth-xyz" });

  const retrieved = await getAuthToken();
  expect(retrieved).toBe("token-auth-xyz");
});

it("retorna null em refreshAuthToken quando requisição falha", async () => {
  vi.mocked(fetch).mockResolvedValueOnce({ ok: false, status: 401 } as Response);
  const token = await refreshAuthToken();
  expect(token).toBeNull();
});

it("processa mensagens GET_CAPTION_TRACKS e OPEN_TAB no listener", async () => {
  const senderWithTab = {
    id: "extension",
    url: "https://www.youtube.com/watch?v=video",
    tab: { id: 1 },
  } as unknown as chrome.runtime.MessageSender;
  const response = vi.fn();

  expect(listener({ type: "GET_CAPTION_TRACKS", videoId: "video" }, senderWithTab, response)).toBe(true);
  await vi.advanceTimersByTimeAsync(0);
  expect(response).toHaveBeenCalledWith(
    expect.objectContaining({ success: true })
  );

  response.mockClear();
  expect(listener({ type: "OPEN_TAB", url: "https://youtube.com" }, senderWithTab, response)).toBe(true);
  await vi.advanceTimersByTimeAsync(0);
  expect(response).toHaveBeenCalledWith({ success: true, data: { id: 123 } });
});


it.each([401, 403])("emite/renova token após HTTP %s e repete uma vez", async status => {
  vi.mocked(fetch)
    .mockResolvedValueOnce({ ok: false, status } as Response)
    .mockResolvedValueOnce({ ok: true, json: async () => ({ token: "fresh-test-token" }) } as Response)
    .mockResolvedValueOnce({ ok: true, json: async () => data } as Response);
  expect(await handleAnalyzeRequest(payload)).toEqual(data);
  expect(fetch).toHaveBeenCalledTimes(3);
  expect(fetch).toHaveBeenNthCalledWith(2, expect.stringContaining("/auth/token"), expect.anything());
  const headers = vi.mocked(fetch).mock.calls[2][1]?.headers as Headers;
  expect(headers.get("Authorization")).toBe("Bearer fresh-test-token");
});
it("não entra em loop quando o token renovado continua rejeitado", async () => {
  vi.mocked(fetch)
    .mockResolvedValueOnce({ ok: false, status: 401 } as Response)
    .mockResolvedValueOnce({ ok: true, json: async () => ({ token: "fresh-test-token" }) } as Response)
    .mockResolvedValueOnce({ ok: false, status: 403 } as Response);
  await expect(handleAnalyzeRequest(payload)).rejects.toThrow("HTTP 403");
  expect(fetch).toHaveBeenCalledTimes(3);
});
it("falha explícita quando a emissão do token não está disponível", async () => {
  vi.mocked(fetch)
    .mockResolvedValueOnce({ ok: false, status: 401 } as Response)
    .mockResolvedValueOnce({ ok: false, status: 503 } as Response);
  await expect(handleAnalyzeRequest(payload)).rejects.toThrow("credencial");
  expect(fetch).toHaveBeenCalledTimes(2);
});
