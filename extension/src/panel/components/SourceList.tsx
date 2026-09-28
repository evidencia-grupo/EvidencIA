import { h } from "preact";
import type { FactCheckingSource } from "../../../../shared/types/api";

interface SourceListProps {
  sources: FactCheckingSource[];
}

export function SourceList({ sources }: SourceListProps) {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div class="card" style={{ marginTop: "12px" }}>
      <div class="card-title">
        <svg viewBox="0 0 24 24" style={{ width: "16px", height: "16px", fill: "var(--color-text-secondary)" }}>
          <path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z" />
        </svg>
        <span>Fontes e Referências Auditadas</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {sources.map((src) => (
          <a
            key={src.id}
            href={src.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "block",
              background: "var(--color-bg-surface)",
              border: "1px solid var(--color-border-subtle)",
              borderRadius: "6px",
              padding: "8px 10px",
              textDecoration: "none",
              transition: "border-color 0.2s ease",
            }}
          >
            <div style={{ fontSize: "12px", fontWeight: "600", color: "var(--color-text-primary)", marginBottom: "2px" }}>
              {src.title}
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--color-text-secondary)" }}>
              <span>{src.domain}</span>
              <span>Confiabilidade: {Math.round(src.reliabilityScore * 100)}%</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
