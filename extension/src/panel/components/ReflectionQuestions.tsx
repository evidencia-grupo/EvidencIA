interface ReflectionQuestionsProps {
  questions?: string[];
}

const fallbackQuestions = [
  "Que evidências independentes poderiam ajudar a avaliar as alegações apresentadas?",
  "Quais aspectos das fontes, como autoria, data e método, vale a pena verificar?",
  "Que contexto ou evidência adicional ajudaria você a formar sua própria interpretação?",
];

export function ReflectionQuestions({ questions }: ReflectionQuestionsProps) {
  const visibleQuestions = questions?.length === 3 ? questions : fallbackQuestions;

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
