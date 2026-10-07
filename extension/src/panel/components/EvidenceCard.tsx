import type { Evidence, EvidenceRelation } from "../../../../shared/types/api";

interface EvidenceCardProps {
  evidence: Evidence;
}

/**
 * Cartão de evidência rastreável (RF-12 / RNF-07 / ADR-006).
 * Mostra de forma explícita a relação da fonte com a alegação, o trecho factual,
 * quem publicou, quando publicou, o endereço da fonte e a base de onde ela veio.
 */
const RELATION_CONFIG: Record<
  EvidenceRelation,
  { label: string; className: string; iconPath: string }
> = {
  supports: {
    label: "Apoia a alegação",
    className: "relation-supports",
    iconPath: "M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z",
  },
  contradicts: {
    label: "Contradiz a alegação",
    className: "relation-contradicts",
    iconPath:
      "M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z",
  },
  contextualizes: {
    label: "Contextualiza a alegação",
    className: "relation-contextualizes",
    iconPath: "M11 7h2v2h-2V7zm0 4h2v6h-2v-6zm1-9C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z",
  },
};

const DATASET_NAMES: Record<string, string> = {
  factchecksbr: "FactChecks.br",
  "factchecks-br": "FactChecks.br",
  google_fact_check: "Google Fact Check",
};

function parseSafeUrl(url: string): URL | null {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? parsed : null;
  } catch {
    return null;
  }
}

function formatDate(value: string): string | null {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  if (isNaN(date.getTime())) {
    return null;
  }
  return date.toLocaleDateString("pt-BR", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

export function EvidenceCard({ evidence }: EvidenceCardProps) {
  const relation = RELATION_CONFIG[evidence.relation] ? evidence.relation : "contextualizes";
  const config = RELATION_CONFIG[relation];
  const safeUrl = parseSafeUrl(evidence.url);
  const displayUrl = safeUrl
    ? safeUrl.hostname.replace(/^www\./, "") + (safeUrl.pathname === "/" ? "" : safeUrl.pathname)
    : null;
  const formattedDate = formatDate(evidence.publishedAt);
  const dataset = evidence.provenance?.dataset;
  const publisher = evidence.publisher || "Fonte não identificada";

  return (
    <article
      class={`evidence-card evidence-card--${relation}`}
      aria-label={`${config.label}. Fonte: ${publisher}`}
    >
      <header class="evidence-card-header">
        <span class={`relation-badge ${config.className}`}>
          <svg class="relation-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
            <path d={config.iconPath} />
          </svg>
          <span class="relation-label">{config.label}</span>
        </span>
      </header>

      <h4 class="evidence-title">
        {safeUrl ? (
          <a href={safeUrl.href} target="_blank" rel="noopener noreferrer" class="evidence-link">
            {evidence.title}
            <span class="visually-hidden"> (abre em nova aba)</span>
            <span aria-hidden="true" class="external-icon"> ↗</span>
          </a>
        ) : (
          evidence.title
        )}
      </h4>

      <div class="evidence-snippet-block">
        <p class="evidence-snippet-label">O que a fonte diz:</p>
        {evidence.snippet ? (
          <blockquote class="evidence-snippet" cite={safeUrl?.href}>
            "{evidence.snippet}"
          </blockquote>
        ) : (
          <p class="evidence-snippet-missing">
            Esta fonte não trouxe um trecho. Abra o link para ler a checagem completa.
          </p>
        )}
      </div>

      <dl class="evidence-meta">
        <div class="evidence-meta-row">
          <dt>Publicado por</dt>
          <dd class="evidence-publisher">{publisher}</dd>
        </div>
        <div class="evidence-meta-row">
          <dt>Publicado em</dt>
          <dd class="evidence-date">
            {formattedDate ? (
              <time dateTime={evidence.publishedAt}>{formattedDate}</time>
            ) : (
              "Data não informada"
            )}
          </dd>
        </div>
        <div class="evidence-meta-row">
          <dt>Endereço</dt>
          <dd class="evidence-url">{displayUrl ?? "Endereço não disponível"}</dd>
        </div>
        {dataset && (
          <div class="evidence-meta-row">
            <dt>Base de checagens</dt>
            <dd class="evidence-provenance">{DATASET_NAMES[dataset] ?? dataset}</dd>
          </div>
        )}
      </dl>
    </article>
  );
}
