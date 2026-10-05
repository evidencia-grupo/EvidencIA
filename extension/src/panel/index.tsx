import { render } from "preact";
import { useState, useLayoutEffect } from "preact/hooks";
import { ClaimCard } from "./components/ClaimCard";
import { UncertaintyAlert } from "./components/UncertaintyAlert";
import { FeedbackSection } from "./components/FeedbackSection";
import type { AnalyzeResponse, FeedbackRequest } from "../../../shared/types/api";

function formatUploadDate(value?: string | null): string {
  if (!value) return "Data não disponível";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Data não disponível";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "long", timeZone: "UTC" }).format(date);
}

export interface AppProps {
  onSubmitFeedback?: (payload: FeedbackRequest) => Promise<void> | void;
}

export function App({ onSubmitFeedback }: AppProps = {}) {
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [noCaptions, setNoCaptions] = useState(false);

  useLayoutEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.source !== window.parent || event.origin !== "https://www.youtube.com") return;
      const msg = event.data;
      if (!msg || !msg.type) return;
      if (["ANALYSIS_START", "ANALYSIS_SUCCESS", "ANALYSIS_ERROR", "NO_CAPTIONS", "NO_CAPTIONS_AVAILABLE"].includes(msg.type)) setSelectedClaimId(null);

      if (msg.type === "FOCUS_PANEL") {
        document.querySelector<HTMLButtonElement>(".close-btn")?.focus();
      } else if (msg.type === "ANALYSIS_START") {
        setLoading(true);
        setData(null);
        setError(null);
        setNoCaptions(false);
      } else if (msg.type === "NO_CAPTIONS_AVAILABLE" || msg.type === "NO_CAPTIONS") {
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
        setError(msg.error || "Não conseguimos checar este vídeo agora. Tente de novo em instantes.");
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

  const handleRetry = () => {
    window.parent.postMessage({ type: "RETRY_ANALYSIS" }, "https://www.youtube.com");
  };

  return (
    <main class="panel-container" aria-label="Painel de checagem factual">
      <header class="panel-header">
        <div>
          <h1 class="panel-title">Checagem Factual</h1>
          <p class="panel-subtitle">Investigação orientada por evidências e fontes curadas</p>
          {data && (
            <div class="video-metadata" aria-label="Metadados de publicação do vídeo">
              <p class="video-metadata-title">{data.videoTitle || "Título não disponível"}</p>
              <p>{data.channelName || "Canal não disponível"} · {formatUploadDate(data.publishedAt)}</p>
            </div>
          )}
        </div>
        <button
          class="close-btn"
          onClick={handleClose}
          aria-label="Fechar painel de checagem factual (Tecla Escape)"
          title="Fechar (Esc)"
        >
          &times;
        </button>
      </header>

      {/* Alerta de ausência de legendas (HU10 / RNF-06) */}
      {noCaptions && (
        <section class="alert-box" role="alert">
          <div>
            <strong>Este vídeo não tem legendas.</strong> Sem as legendas não conseguimos analisar o que é dito, então a checagem não pôde ser feita. Você pode tentar com outro vídeo.
          </div>
          <button
            class="retry-btn"
            onClick={handleRetry}
            aria-label="Tentar novamente a verificação"
          >
            Tentar novamente
          </button>
        </section>
      )}

      {/* Erro de rede ou indisponibilidade temporária */}
      {error && (
        <section class="alert-box" role="alert">
          <div>
            <strong>Algo deu errado.</strong> {error}
          </div>
          <button
            class="retry-btn"
            onClick={handleRetry}
            aria-label="Tentar novamente a verificação"
          >
            Tentar novamente
          </button>
        </section>
      )}

      {/* Estado de Carregamento inicial */}
      {loading && (
        <div role="status" style={{ textAlign: "center", padding: "40px 0", color: "var(--color-text-secondary)" }}>
          <p>Estamos analisando as alegações do vídeo e buscando evidências documentadas...</p>
        </div>
      )}

      {/* Resultado da Análise Evidence-First */}
      {data && (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {/* Banner de Modo Evidence-Only (HU16 / Issue #37) */}
          {data.analysisMode === "evidence_only" && (
            <div class="warning-badge" role="status" style={{ padding: "8px 12px", borderRadius: "6px", background: "rgba(255, 152, 0, 0.15)", border: "1px solid #FF9800", color: "#FFB74D", fontSize: "12px" }}>
              <strong>Modo Exclusivo de Evidências:</strong> A síntese de IA está temporariamente indisponível. Exibindo evidências recuperadas diretamente das bases de checagem.
            </div>
          )}

          {/* Alerta de Incerteza Analítica no topo (HU09 / RF-07) */}
          <UncertaintyAlert claims={data.claims} />

          {/* Limitações e Ressalvas Metodológicas */}
          {data.limitations && data.limitations.length > 0 && (
            <aside class="limitations-container" aria-label="Ressalvas metodológicas" style={{ fontSize: "11px", color: "var(--color-text-secondary)", background: "rgba(255, 255, 255, 0.03)", padding: "6px 10px", borderRadius: "4px" }}>
              {data.limitations.map((lim, idx) => (
                <p key={idx} style={{ margin: "2px 0" }}>* {lim}</p>
              ))}
            </aside>
          )}

          {/* Lista de Alegações com Evidence Cards (HU13 / HU14 / RF-06 / ADR-006) */}
          <div class="claims-list-section" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <h2 style={{ fontSize: "14px", fontWeight: "600", color: "var(--color-text-primary)", margin: "4px 0" }}>
              Alegações Analisadas ({data.claims.length})
            </h2>

            {data.claims.map((claim) => (
              <ClaimCard key={claim.id} claim={claim} expanded={selectedClaimId === claim.id} onSelect={() => setSelectedClaimId(selectedClaimId === claim.id ? null : claim.id)} />
            ))}
          </div>
          {data.claims.length === 0 && (
            <p role="status">{data.analysisMode === "evidence_only"
              ? "Não foi possível identificar alegações checáveis nesta tentativa. Tente novamente mais tarde."
              : "Não foram identificadas alegações checáveis neste vídeo. Opiniões e preferências pessoais não recebem nota ou veredito."}</p>
          )}

          <FeedbackSection videoId={data.videoId} onSubmitFeedback={onSubmitFeedback} />
        </div>
      )}

      {!data && !loading && !noCaptions && !error && (
        <div role="status" style={{ textAlign: "center", padding: "40px 0", color: "var(--color-text-secondary)" }}>
          <p>Clique em <strong>Checar Alegações</strong> no player do YouTube para iniciar a checagem.</p>
        </div>
      )}
    </main>
  );
}

render(<App />, document.getElementById("app")!);
