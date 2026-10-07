// Até 15s de IA, além de captura de legendas e busca de evidências.
const ANALYSIS_TIMEOUT_MS = 30_000;
import { isAnalysis } from "./response-validation";
import { getCaptionTracks } from "./player-captions";
import { getCachedResult, saveCachedResult, CACHE_TTL_MS } from "./cache-manager";
import type { AnalyzeRequest, AnalyzeResponse, FeedbackRequest, FeedbackResponse } from "../../../shared/types/api";

const BACKEND_URL = "http://127.0.0.1:8000/api/v1/analyze";
const FEEDBACK_URL = "http://127.0.0.1:8000/api/v1/feedback";

export { getCachedResult, saveCachedResult, CACHE_TTL_MS };

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (sender.id !== chrome.runtime.id || !sender.url?.startsWith("https://www.youtube.com/")) return;
  let operation: Promise<unknown>;
  if (message.type === "GET_CAPTION_TRACKS" && sender.tab?.id !== undefined) operation = getCaptionTracks(sender.tab.id, message.videoId);
  else if (message.type === "GET_CACHE") operation = getCachedResult(message.videoId);
  else if (message.type === "ANALYZE_VIDEO") operation = handleAnalyzeRequest(message.payload, message.deadline);
  else if (message.type === "SUBMIT_FEEDBACK") operation = handleFeedbackRequest(message.payload);
  else return;
  operation.then(data => sendResponse({ success: true, data })).catch(error =>
    sendResponse({ success: false, error: error instanceof Error ? error.message : "Falha na checagem." }));
  return true;
});

export async function handleAnalyzeRequest(payload: AnalyzeRequest, deadline = Date.now() + ANALYSIS_TIMEOUT_MS): Promise<AnalyzeResponse> {
  const cached = await getCachedResult(payload.videoId);
  if (cached) return cached;
  const remaining = Math.min(ANALYSIS_TIMEOUT_MS, deadline - Date.now());
  if (!Number.isFinite(remaining) || remaining <= 0) throw new Error("Tempo limite de resposta excedido.");
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
    if (!isAnalysis(data, payload.videoId)) throw new Error("Resposta inválida do servidor.");
    await saveCachedResult(data, payload.videoId);
    return data;
  } catch (error) {
    if (controller.signal.aborted) throw new Error("Tempo limite de resposta excedido.");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

export async function handleFeedbackRequest(payload: FeedbackRequest): Promise<FeedbackResponse> {
  const response = await fetch(FEEDBACK_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Client-Version": "1.0.0" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Falha ao registrar feedback: HTTP ${response.status}`);
  return (await response.json()) as FeedbackResponse;
}


