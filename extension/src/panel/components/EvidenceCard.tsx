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
    iconPath: "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z M9 12l2 2 4-4",
  },
  contradicts: {
    label: "Contradiz a alegação",
    className: "relation-contradicts",
    iconPath: "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm3 13-6-6m0 6 6-6",
  },
  contextualizes: {
    label: "Contextualiza a alegação",
    className: "relation-contextualizes",
    iconPath: "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 14v-4m0-4h.01",
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
          <svg
            class="relation-icon"
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
            focusable="false"
          >
            <path d={config.iconPath} />
          </svg>
          <span class="relation-label">{config.label}</span>
        </span>
      </header>

      <h4 class="evidence-title">
        {safeUrl ? (
          <a href={safeUrl.href} target="_blank" rel="noopener noreferrer" class="evidence-link">
            <span>{evidence.title}</span>
            <span class="visually-hidden"> (abre em nova aba)</span>
            <svg
              class="external-icon"
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
              style={{ display: "inline-block", verticalAlign: "middle", marginLeft: "4px" }}
            >
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
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

      {safeUrl && (
        <div class="evidence-cta-row" style={{ marginTop: "10px", paddingTop: "8px", borderTop: "1px solid rgba(255, 255, 255, 0.08)" }}>
          <a
            href={safeUrl.href}
            target="_blank"
            rel="noopener noreferrer"
            class="evidence-cta-button"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              backgroundColor: "#2563EB",
              color: "#FFFFFF",
              fontSize: "12px",
              fontWeight: "600",
              padding: "6px 12px",
              borderRadius: "6px",
              textDecoration: "none",
            }}
          >
            <span>Acessar checagem original</span>
            <span class="visually-hidden"> (abre em nova aba)</span>
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </a>
        </div>
      )}
    </article>
  );
}
