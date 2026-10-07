"""Testes automatizados para o classificador ML, vetorizador e avaliador de limiares."""

import os
import tempfile
import pytest

from ml.classifier.dataset import TrainingSample, load_training_dataset
from ml.classifier.evaluator import evaluate_model, generate_markdown_report, train_test_split
from ml.classifier.features import (
    TFIDFVectorizer,
    extract_ngrams,
    extract_stylistic_features,
    normalize_text,
    tokenize,
)
from ml.classifier.model import ClaimClassifier


def test_text_normalization_and_tokenization():
    text = "O CHÁ de casca de banana CURA diabetes em 3 dias! Urgente!!"
    norm = normalize_text(text)
    assert "cha" in norm
    assert "cura" in norm

    tokens = tokenize(text)
    assert "cha" in tokens
    assert "banana" in tokens
    assert "diabetes" in tokens
    assert "de" not in tokens  # Stopword removida

    ngrams = extract_ngrams(["cha", "banana", "cura"], n=2)
    assert ngrams == ["cha_banana", "banana_cura"]


def test_stylistic_feature_extraction():
    sensational_text = "URGENTE: BOMBA!! CIENTISTAS REVELAM CURA MILAGROSA SECRETA QUE PROIBIRAM!!!"
    style = extract_stylistic_features(sensational_text)

    assert style["style_uppercase_ratio"] > 0.5
    assert style["style_exclamation_density"] > 0.0
    assert style["style_sensational_score"] > 0.0

    neutral_text = "Segundo relatório oficial da Anvisa publicado nesta terça-feira."
    neutral_style = extract_stylistic_features(neutral_text)
    assert neutral_style["style_credibility_score"] > 0.0


def test_tfidf_vectorizer_fit_transform_and_serialization():
    corpus = [
        "Vacina aprovada pela Anvisa após ensaios clínicos controlados.",
        "Chá milagroso caseiro cura todas as doenças em poucos dias.",
        "Relatório econômico oficial do Banco Central projeta inflação.",
    ]
    vec = TFIDFVectorizer(max_features=20, use_bigrams=True)
    transformed = vec.fit_transform(corpus)

    assert len(transformed) == 3
    assert len(vec.vocabulary_) > 0

    # Valida serialização e desserialização
    state = vec.to_dict()
    reconstructed = TFIDFVectorizer.from_dict(state)
    assert reconstructed.vocabulary_ == vec.vocabulary_
    assert reconstructed.idf_ == vec.idf_


def test_training_dataset_loader():
    dataset = load_training_dataset()
    assert len(dataset) >= 50
    assert any(s.label == "fake" for s in dataset)
    assert any(s.label == "true" for s in dataset)
    assert all(s.binary_label in (0, 1) for s in dataset)


def test_claim_classifier_training_and_inference():
    train_samples = [
        TrainingSample("Chá milagroso de folhas cura câncer sem quimioterapia.", "fake", "saúde", "test"),
        TrainingSample("Chip 5G escondido nas vacinas altera DNA humano secretamente.", "fake", "saúde", "test"),
        TrainingSample("Anvisa aprovou ensaios clínicos da vacina conforme relatório oficial.", "true", "saúde", "test"),
        TrainingSample("Estudo científico publicado comprova eficácia do tratamento médico.", "true", "saúde", "test"),
    ]

    clf = ClaimClassifier(alpha=0.5, acceptance_threshold=0.60)
    clf.train([s.text for s in train_samples], [s.label for s in train_samples])

    assert clf.is_trained

    # Predição probabilística
    probs_fake = clf.predict_proba("Chá milagroso cura câncer")
    assert probs_fake["fake"] > probs_fake["true"]

    probs_true = clf.predict_proba("Anvisa aprovou relatório oficial")
    assert probs_true["true"] > probs_fake["true"]

    # Predição com limiares
    pred = clf.predict("Chá milagroso cura câncer", threshold=0.50)
    assert pred["dominant_label"] == "fake"
    assert pred["accepted"] is True
    assert len(pred["top_features"]) > 0


def test_claim_classifier_serialization():
    train_samples = [
        TrainingSample("Bomba: segredo revelado que ninguém conta sobre remédios.", "fake", "saúde", "test"),
        TrainingSample("Ministério da Saúde publica novas diretrizes de prevenção.", "true", "saúde", "test"),
    ]
    clf = ClaimClassifier(alpha=0.5, acceptance_threshold=0.65)
    clf.train([s.text for s in train_samples], [s.label for s in train_samples])

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        clf.save(tmp_path)
        assert os.path.exists(tmp_path)

        loaded = ClaimClassifier.load(tmp_path)
        assert loaded.is_trained
        assert loaded.acceptance_threshold == 0.65

        pred_orig = clf.predict("Bomba: segredo revelado")
        pred_loaded = loaded.predict("Bomba: segredo revelado")
        assert pred_orig["dominant_label"] == pred_loaded["dominant_label"]
        assert pred_orig["confidence"] == pred_loaded["confidence"]
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_evaluator_metrics_and_markdown_report():
    samples = [
        TrainingSample("Texto falso A", "fake", "geral", "test"),
        TrainingSample("Texto falso B", "fake", "geral", "test"),
        TrainingSample("Texto falso C", "fake", "geral", "test"),
        TrainingSample("Texto verdadeiro A", "true", "geral", "test"),
        TrainingSample("Texto verdadeiro B", "true", "geral", "test"),
        TrainingSample("Texto verdadeiro C", "true", "geral", "test"),
    ]

    train_data, test_data = train_test_split(samples, test_size=0.33, seed=42)
    assert len(train_data) + len(test_data) == len(samples)

    clf = ClaimClassifier(alpha=1.0)
    clf.train([s.text for s in train_data], [s.label for s in train_data])

    metrics = evaluate_model(clf, test_data, thresholds=[0.50, 0.70])
    assert "accuracy" in metrics
    assert "confusion_matrix" in metrics
    assert "acceptance_curve" in metrics
    assert len(metrics["acceptance_curve"]) == 2

    report = generate_markdown_report(metrics)
    assert "# Relatório de Treinamento" in report
    assert "Matriz de Confusão" in report
    assert "Curva de Decisão" in report
