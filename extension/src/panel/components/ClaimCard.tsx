import type { FactCheckingSource, VerificationClaim } from "../../../../shared/types/api";

interface ClaimCardProps {
  claim: VerificationClaim;
  sources: FactCheckingSource[];
}

export function ClaimCard({ claim, sources }: ClaimCardProps) {
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
  const claimSources = sources.filter((source) => claim.sourceIds.includes(source.id));

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
      {claimSources.length > 0 && (
        <div style={{ marginTop: "8px", fontSize: "12px" }}>
          <strong>Referências:</strong>
          <ul style={{ margin: "4px 0 0", paddingLeft: "18px" }}>
            {claimSources.map((source) => (
              <li key={source.id}>
                <a href={source.url} target="_blank" rel="noopener noreferrer">
                  {source.title}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
