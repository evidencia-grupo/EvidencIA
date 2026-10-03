import type { Evidence, EvidenceRelation } from "../../../../shared/types/api";

interface EvidenceCardProps {
  evidence: Evidence;
}

const RELATION_CONFIG: Record<
  EvidenceRelation,
  { label: string; className: string; icon: string }
> = {
  supports: {
    label: "Apoia a alegação",
    className: "relation-supports",
    icon: "✓",
  },
  contradicts: {
    label: "Contradiz a alegação",
    className: "relation-contradicts",
    icon: "✕",
  },
  contextualizes: {
    label: "Contextualiza a alegação",
    className: "relation-contextualizes",
    icon: "ℹ",
  },
};

export function EvidenceCard({ evidence }: EvidenceCardProps) {
  const config = RELATION_CONFIG[evidence.relation] || RELATION_CONFIG.contextualizes;

  const formattedDate = (() => {
    try {
      const d = new Date(evidence.publishedAt);
      return d.toLocaleDateString("pt-BR", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return evidence.publishedAt;
    }
  })();

  return (
    <article
      class="evidence-card"
      aria-label={`Evidência de ${evidence.publisher}: ${evidence.title}`}
    >
      <header class="evidence-card-header">
        <span
          class={`relation-badge ${config.className}`}
          role="status"
          aria-label={config.label}
        >
          <span aria-hidden="true" class="relation-icon">{config.icon}</span>
          <span class="relation-label">{config.label}</span>
        </span>
        <span class="evidence-publisher">{evidence.publisher}</span>
      </header>

      <h4 class="evidence-title">
        <a
          href={evidence.url}
          target="_blank"
          rel="noopener noreferrer"
          class="evidence-link"
          aria-label={`${evidence.title} (abre em nova aba)`}
        >
          {evidence.title}
          <span aria-hidden="true" class="external-icon"> ↗</span>
        </a>
      </h4>

      {evidence.snippet && (
        <blockquote class="evidence-snippet" cite={evidence.url}>
          "{evidence.snippet}"
        </blockquote>
      )}

      <footer class="evidence-footer">
        <time dateTime={evidence.publishedAt} class="evidence-date">
          Publicado em: {formattedDate}
        </time>
        {evidence.provenance?.dataset && (
          <span class="evidence-provenance" title={`Base indexada: ${evidence.provenance.dataset}`}>
            Base: {evidence.provenance.dataset}
          </span>
        )}
      </footer>
    </article>
  );
}
