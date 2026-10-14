import { REFLECTION_QUESTIONS } from "../../../../shared/reflection-catalog";

interface ReflectionQuestionsProps {
  questions?: string[] | null;
  headingId?: string;
}

const fallbackQuestions = REFLECTION_QUESTIONS.slice(0, 3);

export function ReflectionQuestions({ questions, headingId = "reflection-heading" }: ReflectionQuestionsProps) {
  const visibleQuestions =
    questions && questions.length === 3 && new Set(questions).size === 3 && questions.every(q => (REFLECTION_QUESTIONS as readonly string[]).includes(q))
      ? questions
      : fallbackQuestions;

  return (
    <section
      class="reflection-section"
      aria-labelledby={headingId}
      role="region"
    >
      <header class="reflection-header">
        <h3 id={headingId} class="reflection-title" style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <span>Perguntas para Reflexão Crítica</span>
        </h3>
        <p class="reflection-subtitle">
          Questões orientadoras neutras para você avaliar as informações por conta própria.
        </p>
      </header>

      <ul class="reflection-list" role="list">
        {visibleQuestions.map((question, index) => (
          <li key={index} class="reflection-item">
            <span class="reflection-number" aria-hidden="true">{index + 1}.</span>
            <span class="reflection-text">{question}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
