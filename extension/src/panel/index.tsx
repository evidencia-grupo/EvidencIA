import { render } from "preact";
import { useState, useLayoutEffect } from "preact/hooks";
import { Gauge } from "./components/Gauge";
import { ClaimCard } from "./components/ClaimCard";
import { SourceList } from "./components/SourceList";
import type { AnalyzeResponse } from "../../../shared/types/api";

function formatUploadDate(value?: string | null): string {
  if (!value) return "Data não disponível";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Data não disponível";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "long", timeZone: "UTC" }).format(date);
}

export function App() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [noCaptions, setNoCaptions] = useState(false);

  useLayoutEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.source !== window.parent || event.origin !== "https://www.youtube.com") return;
      const msg = event.data;
      if (!msg || !msg.type) return;

      if (msg.type === "FOCUS_PANEL") {
        document.querySelector<HTMLButtonElement>(".close-btn")?.focus();
      } else if (msg.type === "ANALYSIS_START") {
        setLoading(true);
        setData(null);
        setError(null);
        setNoCaptions(false);
      } else if (msg.type === "NO_CAPTIONS_AVAILABLE") {
        setLoading(false);
        setNoCaptions(true);
        setData(null);
        setError(null);
      } else if (msg.type === "ANALYSIS_SUCCESS") {
        setLoading(false);
        setNoCaptions(false);
        setData(msg.data);
        setError(null);
      } else if (msg.type === "ANALYSIS_ERROR") {
        setLoading(false);
        setNoCaptions(false);
        setData(null);
        setError(msg.error || "Ocorreu uma falha ao checar as alegações.");
      }
    };

    window.addEventListener("message", handleMessage);
    window.parent.postMessage({ type: "PANEL_READY" }, "https://www.youtube.com");

    // Fecha ao pressionar ESC (WCAG AA Acessibilidade por Teclado)
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        window.parent.postMessage({ type: "CLOSE_PANEL" }, "https://www.youtube.com");
      }
    };
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("message", handleMessage);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const handleClose = () => {
    window.parent.postMessage({ type: "CLOSE_PANEL" }, "https://www.youtube.com");
  };

  return (
    <main class="panel-container" aria-label="Painel de verificação de veracidade">
      <header class="panel-header">
        <div>
          <h1 class="panel-title">Veracidade do Vídeo</h1>
          <p class="panel-subtitle">Análise factual e referências</p>
          {data && (
            <div class="video-metadata" aria-label="Metadados de publicação do vídeo">
              <p class="video-metadata-title">{data.videoTitle || "Título não disponível"}</p>
              <p>{data.channelName || "Canal não disponível"} · {formatUploadDate(data.uploadDate)}</p>
              {data.temporalContext?.isOldContent && (
                <p class="temporal-context">Contexto temporal: {data.temporalContext.message}</p>
              )}
            </div>
          )}
        </div>
        <button
          class="close-btn"
          onClick={handleClose}
          aria-label="Fechar painel de verificação (Tecla Escape)"
          title="Fechar (Esc)"
        >
          &times;
        </button>
      </header>

      {/* Alerta de ausência de legendas (HU10 / RNF-06) */}
      {noCaptions && (
        <section class="alert-box" role="alert">
          <strong>Legendas Indisponíveis:</strong> Este vídeo não possui transcrição ou legendas ativadas pelo criador. A checagem factual não pôde ser gerada.
        </section>
      )}

      {/* Erro de rede ou indisponibilidade temporária */}
      {error && (
        <section class="alert-box" role="alert">
          <strong>Aviso de Instabilidade:</strong> {error}
        </section>
      )}

      {/* Estado de Carregamento inicial */}
      {loading && (
        <div role="status" style={{ textAlign: "center", padding: "40px 0", color: "var(--color-text-secondary)" }}>
          <p>Extraindo transcrição e consultando evidências...</p>
        </div>
      )}

      {/* Resultado da Análise */}
      {data && (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {data.analysisMode === "demo" && (
            <div class="warning-badge" role="status">Demonstração: resultado simulado para testar a extensão. Não constitui checagem factual.</div>
          )}
          {/* Alerta de Incerteza Analítica (HU09 / RF-07) */}
          {data.classification === "inconclusivo" && (
            <div class="warning-badge" role="status">
              Aviso de Incerteza Analítica: As evidências encontradas são divergentes ou insuficientes para consolidar um veredito factual.
            </div>
          )}

          {/* Velocímetro de Veracidade */}
          <Gauge score={data.score} classification={data.classification} />

          {/* Card de Síntese Analítica sem jargões (HU02 / RF-03) */}
          <div class="card">
            <h2 class="card-title">Por que essa classificação?</h2>
            <p style={{ fontSize: "13px", lineHeight: "1.6", color: "var(--color-text-primary)" }}>
              {data.summary}
            </p>
          </div>

          {/* Lista de Alegações Estruturadas com Separação Nítida (HU02 / HU04 / RF-03 / RF-06) */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <h3 style={{ fontSize: "14px", fontWeight: "600", color: "var(--color-text-primary)" }}>
              Alegações Analisadas ({data.claims.length})
            </h3>

            {/* Alegações Contraditas pelas Evidências */}
            {data.claims.some((c) => c.status === "contraditada") && (
              <section aria-labelledby="heading-contraditadas">
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--color-veracidade-falsa)" }} />
                  <h4 id="heading-contraditadas" style={{ fontSize: "12px", fontWeight: "600", color: "#E57373", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                    Contraditas por Fatos ({data.claims.filter((c) => c.status === "contraditada").length})
                  </h4>
                </div>
                {data.claims
                  .filter((c) => c.status === "contraditada")
                  .map((claim) => (
                    <ClaimCard key={claim.id} claim={claim} />
                  ))}
              </section>
            )}

            {/* Alegações Apoiadas por Evidências */}
            {data.claims.some((c) => c.status === "apoiada") && (
              <section aria-labelledby="heading-apoiadas">
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--color-veracidade-apoiada)" }} />
                  <h4 id="heading-apoiadas" style={{ fontSize: "12px", fontWeight: "600", color: "#81C784", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                    Com Respaldo Científico ({data.claims.filter((c) => c.status === "apoiada").length})
                  </h4>
                </div>
                {data.claims
                  .filter((c) => c.status === "apoiada")
                  .map((claim) => (
                    <ClaimCard key={claim.id} claim={claim} />
                  ))}
              </section>
            )}

            {/* Alegações Sem Comprovação Conclusiva */}
            {data.claims.some((c) => c.status === "inconclusiva") && (
              <section aria-labelledby="heading-inconclusivas">
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "6px" }}>
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--color-veracidade-inconclusiva)" }} />
                  <h4 id="heading-inconclusivas" style={{ fontSize: "12px", fontWeight: "600", color: "#FFF59D", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                    Sem Comprovação Conclusiva ({data.claims.filter((c) => c.status === "inconclusiva").length})
                  </h4>
                </div>
                {data.claims
                  .filter((c) => c.status === "inconclusiva")
                  .map((claim) => (
                    <ClaimCard key={claim.id} claim={claim} />
                  ))}
              </section>
            )}
          </div>

          {/* Lista de Fontes com Hyperlinks (HU07 / RF-04) */}
          <SourceList sources={data.sources} />
        </div>
      )}

      {!data && !loading && !noCaptions && !error && (
        <div role="status" style={{ textAlign: "center", padding: "40px 0", color: "var(--color-text-secondary)" }}>
          <p>Clique em <strong>Verificar Veracidade</strong> no player do YouTube para iniciar a checagem.</p>
        </div>
      )}
    </main>
  );
}

render(<App />, document.getElementById("app")!);
