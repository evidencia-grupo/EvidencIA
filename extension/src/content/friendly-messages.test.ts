import { expect, it } from "vitest";
import { FRIENDLY_MESSAGES, toFriendlyMessage } from "./friendly-messages";

it.each([
  [new Error("Tempo limite de resposta excedido (SLA 10s)."), true, FRIENDLY_MESSAGES.timeout],
  [new Error("Checagem encerrada. Tente novamente."), true, FRIENDLY_MESSAGES.timeout],
  [new TypeError("Failed to fetch"), true, FRIENDLY_MESSAGES.offline],
  [new Error("Falha no servidor intermediário: HTTP 503"), false, FRIENDLY_MESSAGES.offline],
  [new Error("Falha no servidor intermediário: HTTP 503"), true, FRIENDLY_MESSAGES.generic],
  [new Error("Resposta inválida do servidor."), true, FRIENDLY_MESSAGES.generic],
  ["erro", true, FRIENDLY_MESSAGES.generic],
  [undefined, true, FRIENDLY_MESSAGES.generic],
])("traduz %s (online: %s) para aviso simples", (error, online, expected) => {
  expect(toFriendlyMessage(error, online)).toBe(expected);
});

it("nenhum aviso usa termos técnicos", () => {
  for (const text of Object.values(FRIENDLY_MESSAGES)) expect(text).not.toMatch(/HTTP|SLA|servidor|fetch|timeout|transcri/i);
});
