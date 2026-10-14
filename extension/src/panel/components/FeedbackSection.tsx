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
      // Cenário de Exceção: Falha ocorre silenciosamente sem interromper a navegação (RNF-05)
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
          <svg class="feedback-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M7 10v12" />
            <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z" />
          </svg>
          <span>Útil</span>
        </button>

        <button
          type="button"
          class={`feedback-btn ${selectedRating === "negative" ? "feedback-btn-active" : ""}`}
          onClick={handleNegativeClick}
          aria-label="Avaliar análise como não útil"
          aria-expanded={showReasons}
        >
          <svg class="feedback-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M17 14V2" />
            <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z" />
          </svg>
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
