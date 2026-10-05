import { useState } from "preact/hooks";
import type { FeedbackRating, FeedbackReason, FeedbackRequest } from "../../../../shared/types/api";

interface FeedbackSectionProps {
  videoId: string;
  onSubmitFeedback?: (payload: FeedbackRequest) => Promise<void> | void;
}

const REASON_OPTIONS: { label: string; value: FeedbackReason }[] = [
  { label: "Fontes desatualizadas", value: "outdated_sources" },
  { label: "Evidências insuficientes", value: "insufficient_evidence" },
  { label: "Análise imprecisa", value: "inaccurate" },
  { label: "Outro motivo", value: "other" },
];

export function FeedbackSection({ videoId, onSubmitFeedback }: FeedbackSectionProps) {
  const [selectedRating, setSelectedRating] = useState<FeedbackRating | null>(null);
  const [selectedReason, setSelectedReason] = useState<FeedbackReason | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [showReasons, setShowReasons] = useState(false);

  const sendFeedback = async (rating: FeedbackRating, reason?: FeedbackReason) => {
    const payload: FeedbackRequest = {
      videoId,
      rating,
      ...(reason ? { reason } : {}),
    };

    try {
      if (onSubmitFeedback) {
        await onSubmitFeedback(payload);
      } else {
        // Envio assíncrono via postMessage para a janela pai (content script)
        window.parent.postMessage({ type: "SUBMIT_FEEDBACK", payload }, "https://www.youtube.com");
      }
    } catch {
      // Cenário de Exceção: Falha ocorre silenciosamente sem interromper a navegação (RNF-05 / HU12)
    } finally {
      setSubmitted(true);
      setShowReasons(false);
    }
  };

  const handlePositiveClick = () => {
    setSelectedRating("positive");
    sendFeedback("positive");
  };

  const handleNegativeClick = () => {
    setSelectedRating("negative");
    setShowReasons(true);
  };

  const handleConfirmNegative = () => {
    sendFeedback("negative", selectedReason || undefined);
  };

  if (submitted) {
    return (
      <section
        class="feedback-section feedback-submitted"
        aria-labelledby="feedback-heading"
        role="region"
      >
        <p id="feedback-heading" class="feedback-success-msg" role="status">
          Obrigado pelo seu feedback anônimo!
        </p>
      </section>
    );
  }

  return (
    <section
      class="feedback-section"
      aria-labelledby="feedback-heading"
      role="region"
    >
      <header class="feedback-header">
        <h4 id="feedback-heading" class="feedback-title">
          Esta análise foi útil para você?
        </h4>
        <p class="feedback-subtitle">
          Sua avaliação anônima ajuda a aprimorar as evidências (LGPD).
        </p>
      </header>

      <div class="feedback-buttons" role="group" aria-label="Avaliação de utilidade">
        <button
          type="button"
          class={`feedback-btn ${selectedRating === "positive" ? "feedback-btn-active" : ""}`}
          onClick={handlePositiveClick}
          aria-label="Avaliar análise como útil"
        >
          <span aria-hidden="true" class="feedback-icon">👍</span>
          <span>Útil</span>
        </button>

        <button
          type="button"
          class={`feedback-btn ${selectedRating === "negative" ? "feedback-btn-active" : ""}`}
          onClick={handleNegativeClick}
          aria-label="Avaliar análise como não útil"
          aria-expanded={showReasons}
        >
          <span aria-hidden="true" class="feedback-icon">👎</span>
          <span>Não útil</span>
        </button>
      </div>

      {showReasons && (
        <div class="feedback-reason-container" role="region" aria-label="Motivo da avaliação">
          <p class="feedback-reason-prompt">Qual foi a principal limitação? (Opcional)</p>
          <div class="feedback-reason-options" role="radiogroup" aria-label="Opções de motivo">
            {REASON_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                class={`feedback-chip ${selectedReason === opt.value ? "feedback-chip-selected" : ""}`}
                onClick={() => setSelectedReason(opt.value)}
                role="radio"
                aria-checked={selectedReason === opt.value}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <button
            type="button"
            class="feedback-submit-btn"
            onClick={handleConfirmNegative}
            aria-label="Confirmar e enviar feedback anônimo"
          >
            Enviar avaliação
          </button>
        </div>
      )}
    </section>
  );
}
