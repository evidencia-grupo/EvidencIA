"""Módulo de avaliação rigorosa com métricas estatísticas e análise de limiares de aceitação."""

import random
from typing import Any, Dict, List, Tuple
from ml.classifier.dataset import TrainingSample
from ml.classifier.model import ClaimClassifier


def train_test_split(
    samples: List[TrainingSample],
    test_size: float = 0.20,
    seed: int = 42,
) -> Tuple[List[TrainingSample], List[TrainingSample]]:
    """Divide o dataset de forma estratificada preservando proporções de classe."""
    rng = random.Random(seed)
    fakes = [s for s in samples if s.label == "fake"]
    trues = [s for s in samples if s.label == "true"]

    rng.shuffle(fakes)
    rng.shuffle(trues)

    n_test_fakes = int(len(fakes) * test_size)
    n_test_trues = int(len(trues) * test_size)

    test_samples = fakes[:n_test_fakes] + trues[:n_test_trues]
    train_samples = fakes[n_test_fakes:] + trues[n_test_trues:]

    rng.shuffle(train_samples)
    rng.shuffle(test_samples)

    return train_samples, test_samples


def evaluate_model(
    model: ClaimClassifier,
    test_samples: List[TrainingSample],
    thresholds: List[float] = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90],
) -> Dict[str, Any]:
    """Calcula matriz de confusão, métricas por classe e curva de aceitação por limiar."""
    texts = [s.text for s in test_samples]
    true_labels = [s.label for s in test_samples]
    total = len(test_samples)

    # 1. Inferência bruta
    predictions = [model.predict(t, threshold=0.50) for t in texts]

    # 2. Métricas no limiar base (0.50)
    tp = sum(1 for p, y in zip(predictions, true_labels) if p["dominant_label"] == "fake" and y == "fake")
    fp = sum(1 for p, y in zip(predictions, true_labels) if p["dominant_label"] == "fake" and y == "true")
    tn = sum(1 for p, y in zip(predictions, true_labels) if p["dominant_label"] == "true" and y == "true")
    fn = sum(1 for p, y in zip(predictions, true_labels) if p["dominant_label"] == "true" and y == "fake")

    accuracy = (tp + tn) / total if total > 0 else 0.0

    prec_fake = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec_fake = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_fake = (2 * prec_fake * rec_fake) / (prec_fake + rec_fake) if (prec_fake + rec_fake) > 0 else 0.0

    prec_true = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    rec_true = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1_true = (2 * prec_true * rec_true) / (prec_true + rec_true) if (prec_true + rec_true) > 0 else 0.0

    macro_f1 = (f1_fake + f1_true) / 2.0

    # 3. Análise detalhada da Curva de Aceitação por Limiar (Threshold Acceptance)
    acceptance_curve = []
    for tau in thresholds:
        accepted_correct = 0
        accepted_total = 0

        for t, y in zip(texts, true_labels):
            res = model.predict(t, threshold=tau)
            if res["accepted"]:
                accepted_total += 1
                if res["label"] == y:
                    accepted_correct += 1

        acceptance_rate = (accepted_total / total) if total > 0 else 0.0
        precision_at_tau = (accepted_correct / accepted_total) if accepted_total > 0 else 1.0
        abstention_rate = 1.0 - acceptance_rate

        acceptance_curve.append({
            "threshold": round(tau, 2),
            "accepted_count": accepted_total,
            "total_count": total,
            "acceptance_rate_pct": round(acceptance_rate * 100, 1),
            "abstention_rate_pct": round(abstention_rate * 100, 1),
            "precision_on_accepted_pct": round(precision_at_tau * 100, 1),
            "error_rate_on_accepted_pct": round((1.0 - precision_at_tau) * 100, 1),
        })

    return {
        "dataset_size": total,
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "classes": {
            "fake": {
                "precision": round(prec_fake, 4),
                "recall": round(rec_fake, 4),
                "f1": round(f1_fake, 4),
            },
            "true": {
                "precision": round(prec_true, 4),
                "recall": round(rec_true, 4),
                "f1": round(f1_true, 4),
            },
        },
        "acceptance_curve": acceptance_curve,
    }


def generate_markdown_report(metrics: Dict[str, Any], cv_metrics: Optional[Dict[str, Any]] = None) -> str:
    """Gera relatório formatado em Markdown com tabelas para auditoria e documentação."""
    cm = metrics["confusion_matrix"]
    c = metrics["classes"]

    lines = [
        "# Relatório de Treinamento e Avaliação do Modelo Classificador — EvidencIA",
        "",
        "## 1. Resumo Geral de Performance",
        f"- **Amostras no Conjunto de Teste:** {metrics['dataset_size']}",
        f"- **Acurácia Global:** {metrics['accuracy'] * 100:.2f}%",
        f"- **Macro F1-Score:** {metrics['macro_f1'] * 100:.2f}%",
        "",
        "## 2. Matriz de Confusão",
        "| | Predito: FALSO | Predito: VERDADEIRO |",
        "|:---|:---:|:---:|",
        f"| **Real: FALSO** | {cm['tp']} (Verdadeiro Positivo) | {cm['fn']} (Falso Negativo) |",
        f"| **Real: VERDADEIRO** | {cm['fp']} (Falso Positivo) | {cm['tn']} (Verdadeiro Negativo) |",
        "",
        "## 3. Métricas Detalhadas por Classe",
        "| Classe | Precisão | Revocação (Recall) | F1-Score |",
        "|:---|:---:|:---:|:---:|",
        f"| **Falso / Desinformação** | {c['fake']['precision'] * 100:.1f}% | {c['fake']['recall'] * 100:.1f}% | {c['fake']['f1'] * 100:.1f}% |",
        f"| **Verdadeiro / Fato** | {c['true']['precision'] * 100:.1f}% | {c['true']['recall'] * 100:.1f}% | {c['true']['f1'] * 100:.1f}% |",
        "",
        "## 4. Análise de Limiares de Aceitação (Curva de Decisão e Confiança)",
        "> **Conceito de Governança:** O modelo adota calibração com limiar mínimo de confiança $\\tau$. Quando a confiança probabilística é inferior ao limiar estipulado, o modelo **absteve-se de emitir veredito unilateral** e encaminha a alegação para o modo *Evidence-First* (verificação manual por checagens oficiais rastreáveis).",
        "",
        "| Limiar ($\\tau$) | Predições Aceitas | Taxa de Aceitação (%) | Taxa de Abstenção (%) | Precisão nos Aceitos (%) | Taxa de Erro nos Aceitos (%) |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for row in metrics["acceptance_curve"]:
        lines.append(
            f"| **{row['threshold']:.2f}** | {row['accepted_count']} / {row['total_count']} | {row['acceptance_rate_pct']:.1f}% | {row['abstention_rate_pct']:.1f}% | **{row['precision_on_accepted_pct']:.1f}%** | {row['error_rate_on_accepted_pct']:.1f}% |"
        )

    lines.extend([
        "",
        "## 5. Recomendação Operacional para Produção",
        "- **Limiar Recomendado ($\\tau = 0.65$ ou $0.70$):** Oferece o equilíbrio ideal entre alta cobertura e margem mínima de erro.",
        "- **Garantia Evidence-First:** Nenhuma decisão automatizada substitui a apresentação de fontes auditadas; alegações com score abaixo do limiar mantêm o estado de neutralidade investigativa.",
    ])

    return "\n".join(lines)
