import type { VerificationClaim } from "../../../../shared/types/api";

interface ReflectionQuestionsProps {
  claims: VerificationClaim[];
  questions?: string[];
}

export function ReflectionQuestions({ claims, questions: generatedQuestions }: ReflectionQuestionsProps) {
  const claim = claims[0]?.text;
  const fallbackQuestions = [
    claim
      ? `Que evidências independentes poderiam ajudar a avaliar esta alegação: “${claim}”?`
      : "Que evidências independentes poderiam ajudar a avaliar as alegações apresentadas?",
    "Quais aspectos das fontes, como autoria, data e método, vale a pena verificar?",
    "Que contexto ou evidência adicional ajudaria você a formar sua própria interpretação?",
  ];
  const questions = generatedQuestions?.length === 3 ? generatedQuestions : fallbackQuestions;

  return (
    <section class="reflection-questions" aria-labelledby="reflection-questions-title">
      <h2 id="reflection-questions-title">Perguntas para sua investigação</h2>
      <ol>
        {questions.map((question) => <li key={question}>{question}</li>)}
      </ol>
    </section>
  );
}