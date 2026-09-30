import { isAnalysis } from "./response-validation";
import type { AnalyzeResponse, LocalCacheEntry } from "../../../shared/types/api";

/**
 * Tempo de vida padrão do cache local: 24 horas em milissegundos.
 * Rastreabilidade: ADR-003, RNF-01 e RNF-05.
 */
export const CACHE_TTL_MS = 86400000;

/**
 * Valida minuciosamente um registro recuperado do chrome.storage.local:
 * 1. Deve ser um objeto válido e não nulo.
 * 2. O identificador do vídeo no registro deve corresponder exatamente ao esperado.
 * 3. O timestamp deve ser um número finito, positivo e não posterior ao momento atual.
 * 4. O TTL deve ser um número finito e positivo (padrão CACHE_TTL_MS).
 * 5. A idade (now - timestamp) deve ser estritamente inferior ao TTL (idade >= TTL indica expiração).
 * 6. A estrutura interna dos dados deve satisfazer integralmente o contrato AnalyzeResponse.
 */
export function isValidCacheEntry(entry: unknown, expectedVideoId: string, now = Date.now()): entry is LocalCacheEntry {
  if (!entry || typeof entry !== "object") {
    return false;
  }
  const candidate = entry as Partial<LocalCacheEntry>;

  // Validação estrita do timestamp: número finito, positivo e nunca no futuro
  if (
    typeof candidate.timestamp !== "number" ||
    !Number.isFinite(candidate.timestamp) ||
    candidate.timestamp <= 0 ||
    candidate.timestamp > now
  ) {
    return false;
  }

  // Validação do TTL: número finito e positivo
  const ttl =
    typeof candidate.ttl === "number" && Number.isFinite(candidate.ttl) && candidate.ttl > 0
      ? candidate.ttl
      : CACHE_TTL_MS;

  // Critério de expiração: idade igual ou superior ao TTL é descartada
  const age = now - candidate.timestamp;
  if (!Number.isFinite(age) || age < 0 || age >= ttl) {
    return false;
  }

  // Validação da integridade do contrato AnalyzeResponse e do videoId
  return isAnalysis(candidate, expectedVideoId);
}

/**
 * Recupera o resultado de checagem do chrome.storage.local antes de qualquer acesso externo.
 * - Registros válidos são retornados imediatamente para renderização instantânea (<1s).
 * - Registros expirados, corrompidos ou divergentes são removidos de forma resiliente (lazy eviction).
 * - Falhas de leitura do storage não lançam exceção, retornando null para permitir a análise externa.
 */
export async function getCachedResult(videoId: string, now = Date.now()): Promise<AnalyzeResponse | null> {
  try {
    const result = await chrome.storage.local.get(videoId);
    const entry = result?.[videoId];
    if (entry === undefined || entry === null) {
      return null;
    }

    if (!isValidCacheEntry(entry, videoId, now)) {
      // Lazy eviction de registro expirado, corrompido ou com videoId divergente
      await chrome.storage.local.remove(videoId).catch(() => undefined);
      return null;
    }

    return entry;
  } catch {
    // Falha de leitura do armazenamento não impede o fluxo de análise
    return null;
  }
}

/**
 * Persiste um resultado de análise concluído com sucesso no chrome.storage.local.
 * - Grava apenas os dados necessários da checagem (AnalyzeResponse), sem histórico geral de navegação.
 * - Atualiza o timestamp para o momento atual com TTL de 24 horas.
 * - Falha de gravação (ex.: cota de disco excedida) não lança erro nem impede a exibição ao usuário.
 */
export async function saveCachedResult(data: AnalyzeResponse, videoId: string, now = Date.now()): Promise<void> {
  if (!isAnalysis(data, videoId)) {
    return;
  }
  const entry: LocalCacheEntry = {
    ...data,
    timestamp: now,
    ttl: CACHE_TTL_MS,
  };
  try {
    await chrome.storage.local.set({ [videoId]: entry });
  } catch {
    // Falha ao gravar não interrompe a entrega da checagem
  }
}
