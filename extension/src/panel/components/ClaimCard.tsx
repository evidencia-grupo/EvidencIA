import { h } from "preact";
import type { VerificationClaim } from "../../../../shared/types/api";

interface ClaimCardProps {
  claim: VerificationClaim;
}

export function ClaimCard({ claim }: ClaimCardProps) {
  const getBadgeStyle = () => {
    switch (claim.status) {
      case "apoiada":
        return {
          bg: "rgba(43, 166, 64, 0.2)",
          color: "#81C784",
          border: "1px solid #2BA640",
          label: "Apoiada por evidências",
        };
      case "contraditada":
        return {
          bg: "rgba(229, 57, 53, 0.2)",
          color: "#E57373",
          border: "1px solid #E53935",
          label: "Contraditada por fatos",
        };
      default:
        return {
          bg: "rgba(251, 192, 45, 0.2)",
          color: "#FFF59D",
          border: "1px solid #FBC02D",
          label: "Sem comprovação conclusiva",
        };
    }
  };

  const badge = getBadgeStyle();

  return (
    <div class="card" style={{ marginBottom: "8px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
        <span
          style={{
            background: badge.bg,
            color: badge.color,
            border: badge.border,
            padding: "2px 8px",
            borderRadius: "4px",
            fontSize: "11px",
            fontWeight: "600",
          }}
        >
          {badge.label}
        </span>
        <span style={{ fontSize: "11px", color: "var(--color-text-secondary)" }}>
          Confiança: {Math.round(claim.confidence * 100)}%
        </span>
      </div>
      <p style={{ fontWeight: "500", marginBottom: "6px", color: "var(--color-text-primary)" }}>
        "{claim.text}"
      </p>
      <p style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>
        {claim.evidenceSummary}
      </p>
    </div>
  );
}
