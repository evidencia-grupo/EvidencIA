import type { Claim, UncertaintyState } from "../../../../shared/types/api";
import { ReflectionQuestions } from "./ReflectionQuestions";
import { EvidenceCard } from "./EvidenceCard";

interface ClaimCardProps {
  claim: Claim;
  expanded?: boolean;
  onSelect?: () => void;
}

const UNCERTAINTY_BADGES: Record<
  UncertaintyState,
  { label: string; className: string; bg: string; color: string; border: string; iconPath: string }
> = {
  supported: {
    label: "Apoiada por evidências (Fato verificado)",
    className: "uncertainty-supported",
    bg: "rgba(43, 166, 64, 0.2)",
    color: "#81C784",
    border: "1px solid #2BA640",
    iconPath: "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z M9 12l2 2 4-4",
  },
  contradicted: {
    label: "Contraditada por fatos (Informação falsa)",
    className: "uncertainty-contradicted",
    bg: "rgba(229, 57, 53, 0.2)",
    color: "#FFCDD2",
    border: "1px solid #E53935",
    iconPath: "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm3 13-6-6m0 6 6-6",
  },
  contextualized: {
    label: "Contextualizada (Com ressalvas)",
    className: "uncertainty-contextualized",
    bg: "rgba(33, 150, 243, 0.2)",
    color: "#90CAF9",
    border: "1px solid #2196F3",
    iconPath: "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 14v-4m0-4h.01",
  },
  conflicting: {
    label: "Evidências conflitantes (Divergente)",
    className: "uncertainty-conflicting",
    bg: "rgba(255, 152, 0, 0.2)",
    color: "#FFB74D",
    border: "1px solid #FF9800",
    iconPath: "m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3ZM12 9v4m0 4h.01",
  },
  insufficient_evidence: {
    label: "Sem evidência suficiente (Não checado)",
    className: "uncertainty-insufficient",
    bg: "rgba(158, 158, 158, 0.2)",
    color: "#E0E0E0",
    border: "1px solid #9E9E9E",
    iconPath: "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm-2.91 7a3 3 0 0 1 5.82 1c0 2-3 3-3 3m.09 4h.01",
  },
};

function formatSeconds(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

export function ClaimCard({ claim, expanded = false, onSelect }: ClaimCardProps) {
  const badge = UNCERTAINTY_BADGES[claim.uncertainty] || UNCERTAINTY_BADGES.insufficient_evidence;
  const evidenceCount = claim.evidence ? claim.evidence.length : 0;

  return (
    <article
      class="claim-card card"
      aria-labelledby={`claim-title-${claim.id}`}
      style={{ marginBottom: "12px" }}
    >
      <header class="claim-card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
        <span
          class={`claim-badge ${badge.className}`}
          style={{
            background: badge.bg,
            color: badge.color,
            border: badge.border,
            padding: "3px 8px",
            borderRadius: "4px",
            fontSize: "11px",
            fontWeight: "600",
            display: "inline-flex",
            alignItems: "center",
            gap: "5px",
          }}
          role="status"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d={badge.iconPath} />
          </svg>
          <span>{badge.label}</span>
        </span>
        <span style={{ fontSize: "11px", color: "var(--color-text-secondary)" }}>
          ID: {claim.id}
        </span>
      </header>

      <h3
        id={`claim-title-${claim.id}`}
        class="claim-text"
        style={{ fontWeight: "600", fontSize: "14px", marginBottom: "8px", color: "var(--color-text-primary)" }}
      >
        <button
          type="button"
          class="claim-toggle"
          aria-expanded={expanded}
          aria-controls={expanded ? `claim-details-${claim.id}` : undefined}
          onClick={onSelect}
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%", textAlign: "left", gap: "8px" }}
        >
          <span>"{claim.text}"</span>
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              flexShrink: 0,
              transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
              transition: "transform 0.2s ease",
            }}
            aria-hidden="true"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
      </h3>

      {claim.transcriptSnippet && (
        <p
          class="claim-transcript-snippet"
          style={{
            fontSize: "12px",
            color: "var(--color-text-secondary, #94A3B8)",
            fontStyle: "italic",
            borderLeft: "2px solid rgba(255, 255, 255, 0.2)",
            paddingLeft: "8px",
            margin: "4px 0 8px 0",
          }}
        >
          "{claim.transcriptSnippet}"
        </p>
      )}

      {typeof claim.timestampStart === "number" && Number.isFinite(claim.timestampStart) && (
        <div class="claim-timestamp-row" style={{ marginBottom: "8px" }}>
          <button
            type="button"
            class="claim-jump-button"
            onClick={() => {
              window.parent?.postMessage({ type: "JUMP_TO_TIMESTAMP", seconds: claim.timestampStart }, "*");
            }}
            style={{
              fontSize: "11px",
              padding: "3px 8px",
              borderRadius: "4px",
              background: "rgba(59, 130, 246, 0.15)",
              color: "#93C5FD",
              border: "1px solid rgba(59, 130, 246, 0.3)",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
            }}
            aria-label={`Ir para o trecho em ${formatSeconds(claim.timestampStart)}`}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <span>Ir para {formatSeconds(claim.timestampStart)}</span>
          </button>
        </div>
      )}

      {claim.temporalContext?.note && (
        <aside
          class="temporal-context-note"
          style={{
            fontSize: "11px",
            color: "var(--color-text-secondary)",
            background: "rgba(255, 255, 255, 0.05)",
            padding: "6px 8px",
            borderRadius: "4px",
            marginBottom: "8px",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}
          aria-label="Contexto temporal da alegação"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span>{claim.temporalContext.note}</span>
        </aside>
      )}

      <div style={{ marginBottom: expanded ? "8px" : "0" }}>
        <button
          type="button"
          onClick={onSelect}
          style={{
            background: "transparent",
            border: "none",
            color: evidenceCount > 0 ? "var(--color-primary, #4ADE80)" : "var(--color-text-secondary)",
            fontSize: "12px",
            cursor: "pointer",
            padding: "4px 0",
            display: "inline-flex",
            alignItems: "center",
            gap: "5px",
            textDecoration: "underline",
          }}
        >
          <span>
            {evidenceCount > 0
              ? (expanded ? "Ocultar fontes" : `Ver ${evidenceCount} ${evidenceCount === 1 ? "fonte e evidência" : "fontes e evidências"}`)
              : (expanded ? "Ocultar detalhes" : "Ver perguntas de reflexão")}
          </span>
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            {expanded ? <polyline points="18 15 12 9 6 15" /> : <polyline points="6 9 12 15 18 9" />}
          </svg>
        </button>
      </div>

      {expanded && <div id={`claim-details-${claim.id}`}>
      {/* Seção de Evidências */}
      <section class="claim-evidences" aria-label={`Evidências para: ${claim.text}`}>
        {claim.evidence && claim.evidence.length > 0 ? (
          <div class="evidence-list" style={{ marginTop: "8px" }}>
            <h4 style={{ fontSize: "12px", color: "var(--color-text-secondary)", marginBottom: "6px" }}>
              Evidências apuradas ({claim.evidence.length}):
            </h4>
            {claim.evidence.map((ev) => (
              <EvidenceCard key={ev.sourceId} evidence={ev} />
            ))}
          </div>
        ) : (
          <p
            class="no-evidence-notice"
            style={{
              fontSize: "12px",
              color: "var(--color-text-secondary)",
              fontStyle: "italic",
              marginTop: "6px",
            }}
          >
            Nenhuma evidência documental ou checagem formal foi localizada para esta alegação específica (RF-12).
          </p>
        )}
      </section>
      <ReflectionQuestions questions={claim.reflectionQuestions} headingId={`reflection-heading-${claim.id}`} />
      </div>}
    </article>
  );
}
