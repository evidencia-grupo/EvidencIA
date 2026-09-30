import type { VerificationClaim, VerificationClassification } from "../../../../shared/types/api";

interface UncertaintyAlertProps {
  classification: VerificationClassification;
  claims: VerificationClaim[];
}

/**
 * Alerta visual imediato de incerteza analítica (HU09 / RF-07 / RNF-06 / RNF-07).
 * Aparece no topo do painel quando não há confirmação consolidada ou quando
 * fontes legítimas chegam a conclusões opostas, sem arbitrar um vencedor.
 */
export function UncertaintyAlert({ classification, claims }: UncertaintyAlertProps) {
  const supported = claims.filter((c) => c.status === "apoiada").length;
  const contradicted = claims.filter((c) => c.status === "contraditada").length;
  const inconclusive = classification === "inconclusivo";
  const controversy = supported > 0 && contradicted > 0;

  if (!inconclusive && !controversy) {
    return null;
  }

  return (
    <section class="uncertainty-alert" role="alert" aria-labelledby="uncertainty-alert-title">
      <div class="uncertainty-alert-header">
        <svg class="uncertainty-alert-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
        </svg>
        <strong id="uncertainty-alert-title">
          {inconclusive ? "Ainda não dá para confirmar" : "As fontes discordam entre si"}
        </strong>
      </div>

      {inconclusive ? (
        <p>
          Nenhuma fonte confiável confirma nem desmente o que é dito neste vídeo. Pense antes de
          compartilhar.
        </p>
      ) : (
        <p>
          Encontramos fontes confiáveis dizendo coisas opostas. Mostramos os dois lados para você tirar
          suas conclusões. Pense antes de compartilhar.
        </p>
      )}

      {controversy && (
        <ul class="uncertainty-sides" aria-label="Os dois lados">
          <li>
            <span class="uncertainty-side-label">O que apoia</span>
            <span>
              {supported} {supported === 1 ? "ponto tem" : "pontos têm"} apoio de fontes
            </span>
          </li>
          <li>
            <span class="uncertainty-side-label">O que contradiz</span>
            <span>
              {contradicted} {contradicted === 1 ? "ponto é contrariado" : "pontos são contrariados"} por
              fontes
            </span>
          </li>
        </ul>
      )}

      {controversy && <p class="uncertainty-alert-hint">Veja os detalhes de cada lado logo abaixo.</p>}
    </section>
  );
}
