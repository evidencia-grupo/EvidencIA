import type {
  AnalyzeRequest,
  AnalyzeResponse,
  LocalCacheEntry,
} from "../../../shared/types/api";

const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 horas (ADR-003)
const BACKEND_URL = "http://127.0.0.1:8000/api/v1/analyze";

/**
 * Service Worker (Manifest V3)
 * Responsável pela intermediação de rede e gerenciamento do cache local com TTL.
 */
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "ANALYZE_VIDEO") {
    handleAnalyzeRequest(message.payload)
      .then((response) => sendResponse({ success: true, data: response }))
      .catch((error) =>
        sendResponse({
          success: false,
          error: error instanceof Error ? error.message : "Erro desconhecido",
        })
      );
    return true; // Mantém o canal de resposta assíncrona aberto
  }

  if (message.type === "GET_CACHE") {
    getCachedResult(message.videoId).then((cached) => {
      sendResponse({ success: true, data: cached });
    });
    return true;
  }
});

async function getCachedResult(videoId: string): Promise<AnalyzeResponse | null> {
  const result = await chrome.storage.local.get(videoId);
  const entry = result[videoId] as LocalCacheEntry | undefined;

  if (!entry) return null;

  const isExpired = Date.now() - entry.timestamp > (entry.ttl || CACHE_TTL_MS);
  if (isExpired) {
    // Invalidação preguiçosa (Lazy eviction)
    await chrome.storage.local.remove(videoId);
    return null;
  }

  return entry;
}

async function handleAnalyzeRequest(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  // 1. Verifica cache local antes de disparar chamada de rede (RNF-01 / ADR-003)
  const cached = await getCachedResult(payload.videoId);
  if (cached) {
    return cached;
  }

  // 2. Chamada ao Backend Proxy seguro com timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 9500); // Limite cliente de 9,5s

  try {
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Client-Version": "1.0.0",
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Falha no servidor intermediário: HTTP ${response.status}`);
    }

    const data = (await response.json()) as AnalyzeResponse;

    // 3. Salva no cache local (chrome.storage.local) com timestamp e TTL
    const cacheEntry: LocalCacheEntry = {
      ...data,
      timestamp: Date.now(),
      ttl: CACHE_TTL_MS,
    };

    await chrome.storage.local.set({ [payload.videoId]: cacheEntry });

    return data;
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("Tempo limite de resposta excedido (SLA 10s).");
    }
    throw error;
  }
}
