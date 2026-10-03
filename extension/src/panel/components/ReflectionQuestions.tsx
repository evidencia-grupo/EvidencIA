interface ReflectionQuestionsProps {
  questions?: string[];
}

export function ReflectionQuestions({ questions }: ReflectionQuestionsProps) {
  if (!questions || questions.length === 0) {
    return null;
  }

  return (
    <section
      class="reflection-section"
      aria-labelledby="reflection-heading"
      role="region"
    >
      <header class="reflection-header">
        <h3 id="reflection-heading" class="reflection-title">
          Perguntas para Reflexão Crítica
        </h3>
        <p class="reflection-subtitle">
          Questões orientadoras neutras para você avaliar as informações por conta própria.
        </p>
      </header>

      <ul class="reflection-list" role="list">
        {questions.map((question, index) => (
          <li key={index} class="reflection-item">
            <span class="reflection-number" aria-hidden="true">{index + 1}.</span>
            <span class="reflection-text">{question}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
