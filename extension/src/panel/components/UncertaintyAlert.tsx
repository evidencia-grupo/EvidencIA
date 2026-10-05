import type { Claim } from "../../../../shared/types/api";

interface UncertaintyAlertProps {
  claims: Claim[];
}

/**
 * Alerta visual imediato de incerteza analítica (HU09 / RF-07 / RNF-06 / RNF-07).
 * Exibido quando há divergência entre fontes ou quando as evidências são insuficientes,
 * sem impor autoridade algorítmica.
 */
export function UncertaintyAlert({ claims }: UncertaintyAlertProps) {
  const supported = claims.filter((c) => c.uncertainty === "supported").length;
  const contradicted = claims.filter((c) => c.uncertainty === "contradicted").length;
  const conflicting = claims.filter((c) => c.uncertainty === "conflicting").length;
  const insufficient = claims.filter((c) => c.uncertainty === "insufficient_evidence").length;

  const hasControversy = conflicting > 0 || (supported > 0 && contradicted > 0);
  const allInsufficient = claims.length > 0 && insufficient === claims.length;

  if (!hasControversy && !allInsufficient) {
    return null;
  }

  return (
    <section class="uncertainty-alert" role="alert" aria-labelledby="uncertainty-alert-title">
      <div class="uncertainty-alert-header">
        <svg class="uncertainty-alert-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
        </svg>
        <strong id="uncertainty-alert-title">
          {allInsufficient
            ? "Evidências documentais insuficientes"
            : "Evidências com divergências apuradas"}
        </strong>
      </div>

      {allInsufficient ? (
        <p>
          Não foram localizadas checagens consolidadas ou estudos científicos para confirmar ou refutar
          as afirmações deste vídeo. Recomendamos cautela antes de compartilhar.
        </p>
      ) : (
        <p>
          Foram localizadas evidências com conclusões distintas para diferentes afirmações do vídeo.
          Apresentamos os fatos documentados para sua própria análise crítica.
        </p>
      )}

      {hasControversy && (
        <ul class="uncertainty-sides" aria-label="Distribuição de evidências">
          {supported > 0 && (
            <li>
              <span class="uncertainty-side-label">Alegações apoiadas</span>
              <span>
                {supported} {supported === 1 ? "alegação possui" : "alegações possuem"} evidência favorável
              </span>
            </li>
          )}
          {contradicted > 0 && (
            <li>
              <span class="uncertainty-side-label">Alegações contraditas</span>
              <span>
                {contradicted} {contradicted === 1 ? "alegação foi contestada" : "alegações foram contestadas"} por checagens
              </span>
            </li>
          )}
        </ul>
      )}
    </section>
  );
}
