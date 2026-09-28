import { describe, it, expect } from "vitest";
import { sanitizeTranscriptText } from "./caption-parser";

describe("sanitizeTranscriptText", () => {
  it("deve remover tags HTML e entidades codificadas", () => {
    const raw = "<font color='#fff'>Texto com &quot;aspas&quot; e &#39;apostrofos&#39;</font>";
    const sanitized = sanitizeTranscriptText(raw);
    expect(sanitized).toBe('Texto com "aspas" e \'apostrofos\'');
  });

  it("deve remover marcadores de audio como [Musica] e [Aplausos]", () => {
    const raw = "[Musica] Ola pessoal [Aplausos] sejam bem-vindos";
    const sanitized = sanitizeTranscriptText(raw);
    expect(sanitized).toBe("Ola pessoal sejam bem-vindos");
  });

  it("deve colapsar multiplos espacos e quebras de linha", () => {
    const raw = "Texto   com    muitos      espacos\n\ne quebras";
    const sanitized = sanitizeTranscriptText(raw);
    expect(sanitized).toBe("Texto com muitos espacos e quebras");
  });

  it("deve retornar string vazia para entrada vazia ou nula", () => {
    expect(sanitizeTranscriptText("")).toBe("");
  });
});
