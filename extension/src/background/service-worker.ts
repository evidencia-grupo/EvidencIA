import type { AnalyzeRequest, AnalyzeResponse, LocalCacheEntry } from "../../../shared/types/api";

const CACHE_TTL_MS = 86400000;
const BACKEND_URL = "http://127.0.0.1:8000/api/v1/analyze";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (sender.id !== chrome.runtime.id || !sender.url?.startsWith("https://www.youtube.com/")) return;
  let operation: Promise<AnalyzeResponse | null>;
  if (message.type === "GET_CACHE") operation = getCachedResult(message.videoId);
  else if (message.type === "ANALYZE_VIDEO") operation = handleAnalyzeRequest(message.payload, message.deadline);
  else return;
  operation.then(data => sendResponse({ success: true, data })).catch(error =>
    sendResponse({ success: false, error: error instanceof Error ? error.message : "Falha na checagem." }));
  return true;
});

export async function getCachedResult(videoId: string): Promise<AnalyzeResponse | null> {
  try {
    const result = await chrome.storage.local.get(videoId);
    const entry = result[videoId] as LocalCacheEntry | undefined;
    if (!entry) return null;
    const age = Date.now() - entry.timestamp;
    if (!Number.isFinite(age) || age < 0 || age >= CACHE_TTL_MS || entry.videoId !== videoId || !entry.summary || !Array.isArray(entry.claims) || !Array.isArray(entry.sources)) {
      await chrome.storage.local.remove(videoId).catch(() => undefined);
      return null;
    }
    return entry;
  } catch {
    return null; // Cache indisponível não impede uma nova análise.
  }
}

export async function handleAnalyzeRequest(payload: AnalyzeRequest, deadline = Date.now() + 9500): Promise<AnalyzeResponse> {
  const cached = await getCachedResult(payload.videoId);
  if (cached) return cached;
  const remaining = Math.min(9500, deadline - Date.now());
  if (!Number.isFinite(remaining) || remaining <= 0) throw new Error("Tempo limite de resposta excedido (SLA 10s).");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), remaining);
  try {
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Client-Version": "1.0.0" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`Falha no servidor intermediário: HTTP ${response.status}`);
    const data = await response.json() as AnalyzeResponse;
    if (data.videoId !== payload.videoId || !data.summary || !Array.isArray(data.claims) || !Array.isArray(data.sources)) throw new Error("Resposta inválida do servidor.");
    const entry: LocalCacheEntry = { ...data, timestamp: Date.now(), ttl: CACHE_TTL_MS };
    void chrome.storage.local.set({ [payload.videoId]: entry }).catch(() => undefined);
    return data;
  } catch (error) {
    if (controller.signal.aborted) throw new Error("Tempo limite de resposta excedido (SLA 10s).");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}
