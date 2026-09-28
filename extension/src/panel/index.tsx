import { render } from "preact";
import { useState, useEffect } from "preact/hooks";
import { Gauge } from "./components/Gauge";
import { ClaimCard } from "./components/ClaimCard";
import { SourceList } from "./components/SourceList";
import type { AnalyzeResponse } from "../../../shared/types/api";

function App() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [noCaptions, setNoCaptions] = useState(false);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      const msg = event.data;
      if (!msg || !msg.type) return;

      if (msg.type === "NO_CAPTIONS_AVAILABLE") {
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
        setError(msg.error || "Ocorreu uma falha ao checar as alegações.");
      }
    };

    window.addEventListener("message", handleMessage);

    // Fecha ao pressionar ESC (WCAG AA Acessibilidade por Teclado)
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        window.parent.postMessage({ type: "CLOSE_PANEL" }, "*");
      }
    };
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("message", handleMessage);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const handleClose = () => {
    window.parent.postMessage({ type: "CLOSE_PANEL" }, "*");
  };

  return (
    <main class="panel-container" role="main" aria-label="Painel de verificação de veracidade">
      <header class="panel-header">
        <div>
          <h1 class="panel-title">Veracidade do Vídeo</h1>
          <p class="panel-subtitle">Análise factual e referências</p>
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
        <div style={{ textAlign: "center", padding: "40px 0", color: "var(--color-text-secondary)" }}>
          <p>Extraindo transcrição e consultando evidências...</p>
        </div>
      )}

      {/* Resultado da Análise */}
      {data && (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
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

          {/* Lista de Alegações Estruturadas (HU04 / RF-06) */}
          <div>
            <h3 style={{ fontSize: "13px", fontWeight: "600", marginBottom: "8px", color: "var(--color-text-secondary)" }}>
              Alegações Analisadas ({data.claims.length})
            </h3>
            {data.claims.map((claim) => (
              <ClaimCard key={claim.id} claim={claim} />
            ))}
          </div>

          {/* Lista de Fontes com Hyperlinks (HU07 / RF-04) */}
          <SourceList sources={data.sources} />
        </div>
      )}

      {!data && !loading && !noCaptions && !error && (
        <div style={{ textAlign: "center", padding: "40px 0", color: "var(--color-text-secondary)" }}>
          <p>Clique em <strong>Verificar Veracidade</strong> no player do YouTube para iniciar a checagem.</p>
        </div>
      )}
    </main>
  );
}

render(<App />, document.getElementById("app")!);
