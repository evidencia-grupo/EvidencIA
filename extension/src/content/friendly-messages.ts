/** HU01 / RNF-07: traduz falhas técnicas em avisos simples para quem usa a extensão. */
export const FRIENDLY_MESSAGES = {
  offline: "Parece que sua internet caiu. Confira a conexão e tente de novo.",
  timeout: "A checagem demorou mais do que o esperado. Tente de novo em instantes.",
  generic: "Não conseguimos checar este vídeo agora. Tente de novo em instantes.",
} as const;

const TIMEOUT_PATTERN = /tempo limite|encerrada|abort|timeout/i;
const NETWORK_PATTERN = /failed to fetch|networkerror|network|offline|load failed|internet/i;

export function toFriendlyMessage(error: unknown, online = navigator.onLine): string {
  if (!online) return FRIENDLY_MESSAGES.offline;
  const text = error instanceof Error ? `${error.name} ${error.message}` : String(error ?? "");
  if (TIMEOUT_PATTERN.test(text)) return FRIENDLY_MESSAGES.timeout;
  if (NETWORK_PATTERN.test(text)) return FRIENDLY_MESSAGES.offline;
  return FRIENDLY_MESSAGES.generic;
}
