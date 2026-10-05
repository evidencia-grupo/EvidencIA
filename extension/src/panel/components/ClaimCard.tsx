import type { Claim, UncertaintyState } from "../../../../shared/types/api";
import { EvidenceCard } from "./EvidenceCard";

interface ClaimCardProps {
  claim: Claim;
}

const UNCERTAINTY_BADGES: Record<
  UncertaintyState,
  { label: string; className: string; bg: string; color: string; border: string }
> = {
  supported: {
    label: "Apoiada por evidências",
    className: "uncertainty-supported",
    bg: "rgba(43, 166, 64, 0.2)",
    color: "#81C784",
    border: "1px solid #2BA640",
  },
  contradicted: {
    label: "Contraditada por fatos",
    className: "uncertainty-contradicted",
    bg: "rgba(229, 57, 53, 0.2)",
    color: "#FFCDD2",
    border: "1px solid #E53935",
  },
  contextualized: {
    label: "Contextualizada",
    className: "uncertainty-contextualized",
    bg: "rgba(33, 150, 243, 0.2)",
    color: "#90CAF9",
    border: "1px solid #2196F3",
  },
  conflicting: {
    label: "Evidências conflitantes",
    className: "uncertainty-conflicting",
    bg: "rgba(255, 152, 0, 0.2)",
    color: "#FFB74D",
    border: "1px solid #FF9800",
  },
  insufficient_evidence: {
    label: "Sem evidência suficiente",
    className: "uncertainty-insufficient",
    bg: "rgba(158, 158, 158, 0.2)",
    color: "#E0E0E0",
    border: "1px solid #9E9E9E",
  },
};

export function ClaimCard({ claim }: ClaimCardProps) {
  const badge = UNCERTAINTY_BADGES[claim.uncertainty] || UNCERTAINTY_BADGES.insufficient_evidence;

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
            padding: "2px 8px",
            borderRadius: "4px",
            fontSize: "11px",
            fontWeight: "600",
          }}
          role="status"
        >
          {badge.label}
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
        "{claim.text}"
      </h3>

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
          }}
          aria-label="Contexto temporal da alegação"
        >
          ⏱️ {claim.temporalContext.note}
        </aside>
      )}

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
    </article>
  );
}
