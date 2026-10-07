"""Script CLI para treinamento e avaliação do classificador supervisionado."""

import argparse
import os

from ml.classifier.dataset import load_training_dataset
from ml.classifier.evaluator import evaluate_model, generate_markdown_report, train_test_split
from ml.classifier.model import ClaimClassifier

DEFAULT_MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.json")
DEFAULT_REPORT_PATH = os.path.join(os.path.dirname(__file__), "EVALUATION_REPORT.md")


def run_training(
    model_output: str = DEFAULT_MODEL_PATH,
    report_output: str = DEFAULT_REPORT_PATH,
    test_size: float = 0.20,
    alpha: float = 0.5,
    acceptance_threshold: float = 0.60,
) -> dict:
    print("=" * 70)
    print("  EVIDENCIA ML — TREINAMENTO E CALIBRAÇÃO DO CLASSIFICADOR")
    print("=" * 70)

    # 1. Carrega dados
    dataset = load_training_dataset(include_sample_facts=True)
    fakes = sum(1 for s in dataset if s.label == "fake")
    trues = sum(1 for s in dataset if s.label == "true")
    print(f"\n[1] Dataset carregado: {len(dataset)} amostras totais (Fake: {fakes} | True: {trues})")

    # 2. Divisão estratificada
    train_data, test_data = train_test_split(dataset, test_size=test_size, seed=42)
    print(f"[2] Divisão estratificada: {len(train_data)} treino | {len(test_data)} teste")

    # 3. Treinamento
    classifier = ClaimClassifier(alpha=alpha, acceptance_threshold=acceptance_threshold)
    train_texts = [s.text for s in train_data]
    train_labels = [s.label for s in train_data]

    print("[3] Treinando vetorizador TF-IDF e modelo probabilístico...")
    classifier.train(train_texts, train_labels)

    # 4. Avaliação
    print("[4] Avaliando métricas e curva de aceitação por limiar no conjunto de teste...")
    metrics = evaluate_model(classifier, test_data)

    print("\n" + "-" * 70)
    print(f"  RESULTADOS NO CONJUNTO DE TESTE ({len(test_data)} amostras):")
    print(f"  - Acurácia: {metrics['accuracy'] * 100:.2f}%")
    print(f"  - Macro F1: {metrics['macro_f1'] * 100:.2f}%")
    print(f"  - Falso (Precisão: {metrics['classes']['fake']['precision']*100:.1f}% | Recall: {metrics['classes']['fake']['recall']*100:.1f}%)")
    print(f"  - Verdadeiro (Precisão: {metrics['classes']['true']['precision']*100:.1f}% | Recall: {metrics['classes']['true']['recall']*100:.1f}%)")
    print("-" * 70)

    print("\n  CURVA DE ACEITAÇÃO POR LIMIAR (Threshold Acceptance):")
    print("  | Limiar | Aceitas | Taxa Aceitação | Precisão nos Aceitos | Abstenção |")
    print("  |:------:|:-------:|:--------------:|:---------------------:|:---------:|")
    for r in metrics["acceptance_curve"]:
        print(f"  |  {r['threshold']:.2f}  |  {r['accepted_count']:>2}/{r['total_count']:<2}  |     {r['acceptance_rate_pct']:>5.1f}%    |         {r['precision_on_accepted_pct']:>5.1f}%        |   {r['abstention_rate_pct']:>5.1f}%  |")
    print("-" * 70)

    # 5. Salva artefato do modelo
    classifier.save(model_output)
    print(f"\n[5] Modelo salvo com sucesso em: {model_output}")

    # 6. Salva relatório Markdown
    report_content = generate_markdown_report(metrics)
    with open(report_output, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"[6] Relatório detalhado gerado em: {report_output}")
    print("=" * 70)

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Treinador do Classificador de Alegações EvidencIA")
    parser.add_argument("--output", default=DEFAULT_MODEL_PATH, help="Caminho do arquivo do modelo (.json)")
    parser.add_argument("--report", default=DEFAULT_REPORT_PATH, help="Caminho do relatório (.md)")
    parser.add_argument("--test-size", type=float, default=0.20, help="Proporção de teste (padrão: 0.20)")
    parser.add_argument("--alpha", type=float, default=0.5, help="Parâmetro de suavização Laplace (padrão: 0.5)")
    parser.add_argument("--threshold", type=float, default=0.60, help="Limiar de aceitação (padrão: 0.60)")
    args = parser.parse_args()

    run_training(
        model_output=args.output,
        report_output=args.report,
        test_size=args.test_size,
        alpha=args.alpha,
        acceptance_threshold=args.threshold,
    )


if __name__ == "__main__":
    main()
