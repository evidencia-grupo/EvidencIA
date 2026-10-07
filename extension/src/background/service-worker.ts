// Até 15s de IA, além de captura de legendas e busca de evidências.
const ANALYSIS_TIMEOUT_MS = 30_000;
import { isAnalysis } from "./response-validation";
import { getCaptionTracks } from "./player-captions";
import { getCachedResult, saveCachedResult, CACHE_TTL_MS } from "./cache-manager";
import type { AnalyzeRequest, AnalyzeResponse, FeedbackRequest, FeedbackResponse } from "../../../shared/types/api";

const API_BASE = (import.meta.env?.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const BACKEND_URL = `${API_BASE}/api/v1/analyze`;
const FEEDBACK_URL = `${API_BASE}/api/v1/feedback`;
const AUTH_URL = `${API_BASE}/api/v1/auth/token`;

export { getCachedResult, saveCachedResult, CACHE_TTL_MS };

let inMemoryToken: string | null = null;

export async function getAuthToken(): Promise<string | null> {
  if (inMemoryToken) return inMemoryToken;
  try {
    const stored = await chrome.storage?.local?.get("evidencia_auth_token");
    if (stored?.evidencia_auth_token) {
      inMemoryToken = stored.evidencia_auth_token;
      return inMemoryToken;
    }
  } catch {
    // Ignora falha de storage em ambiente de teste ou isolado
  }
  return null;
}

export async function refreshAuthToken(): Promise<string | null> {
  try {
    const stored = await chrome.storage?.local?.get("evidencia_inst_id");
    const instId = stored?.evidencia_inst_id || `inst-${crypto.randomUUID()}`;
    await chrome.storage?.local?.set({ evidencia_inst_id: instId });

    const res = await fetch(AUTH_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ installationId: instId, clientVersion: "1.0.0" }),
    });
    if (res.ok) {
      const data = (await res.json()) as { token: string };
      inMemoryToken = data.token;
      await chrome.storage?.local?.set({ evidencia_auth_token: data.token });
      return data.token;
    }
  } catch {
    // Falha silenciosa em dev/offline
  }
  return null;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (sender.id !== chrome.runtime.id || !sender.url?.startsWith("https://www.youtube.com/")) return;
  let operation: Promise<unknown>;
  if (message.type === "GET_CAPTION_TRACKS" && sender.tab?.id !== undefined) operation = getCaptionTracks(sender.tab.id, message.videoId);
  else if (message.type === "GET_CACHE") operation = getCachedResult(message.videoId);
  else if (message.type === "ANALYZE_VIDEO") operation = handleAnalyzeRequest(message.payload, message.deadline);
  else if (message.type === "SUBMIT_FEEDBACK") operation = handleFeedbackRequest(message.payload);
  else if (message.type === "OPEN_TAB" && typeof message.url === "string") operation = chrome.tabs.create({ url: message.url });
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
    const token = await getAuthToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "X-Client-Version": "1.0.0",
    };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers,
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
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Client-Version": "1.0.0",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(FEEDBACK_URL, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Falha ao registrar feedback: HTTP ${response.status}`);
  return (await response.json()) as FeedbackResponse;
}


