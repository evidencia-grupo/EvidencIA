"""Módulo de classificação supervisionada e avaliação de modelos — EvidencIA ML."""

from ml.classifier.model import ClaimClassifier
from ml.classifier.dataset import load_training_dataset

__all__ = ["ClaimClassifier", "load_training_dataset"]
