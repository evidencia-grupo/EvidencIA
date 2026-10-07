"""Serviço de inferência do modelo classificador supervisionado de alegações."""

import logging
import os
from typing import Any, Dict, Optional

from ml.classifier.model import ClaimClassifier
from ml.classifier.dataset import load_training_dataset
from ml.classifier.features import explain_linguistic_triggers

logger = logging.getLogger(__name__)

DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "ml", "classifier", "model.json"
)


class ClassifierService:
    """Encapsula a carga e execução do modelo ML de classificação de desinformação."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.model: Optional[ClaimClassifier] = None
        self._load_or_train()

    def _load_or_train(self) -> None:
        try:
            if os.path.exists(self.model_path):
                self.model = ClaimClassifier.load(self.model_path)
                logger.info("Modelo ML carregado com sucesso a partir de %s", self.model_path)
            else:
                logger.info("Modelo não encontrado em %s. Treinando modelo inicial...", self.model_path)
                dataset = load_training_dataset()
                self.model = ClaimClassifier(alpha=0.5, acceptance_threshold=0.60)
                self.model.train([s.text for s in dataset], [s.label for s in dataset])
                self.model.save(self.model_path)
                logger.info("Modelo inicial treinado e salvo com sucesso em %s", self.model_path)
        except Exception as exc:
            logger.error("Falha ao inicializar o classificador ML: %s", exc)
            self.model = None

    def classify(self, text: str, threshold: Optional[float] = None) -> Dict[str, Any]:
        """Classifica uma alegação utilizando o modelo supervisionado."""
        if not self.model or not self.model.is_trained:
            self._load_or_train()

        if not self.model:
            return {
                "label": "unverified",
                "verdict_pt": "Não verificado (modelo indisponível)",
                "confidence": 0.50,
                "accepted": False,
                "probabilities": {"fake": 0.50, "true": 0.50},
                "top_features": [],
            }

        res = self.model.predict(text, threshold=threshold)

        triggers = explain_linguistic_triggers(text)
        tone = "neutral"
        if any("sensacionalismo" in t.lower() or "dogmático" in t.lower() for t in triggers):
            tone = "sensational_dogmatic"
        elif any("institucionais" in t.lower() or "modulação" in t.lower() for t in triggers):
            tone = "scientific_cautious"

        verdict_map = {
            "fake": "Falso / Desinformação",
            "true": "Verdadeiro / Fato",
            "unverified": "Sem evidência conclusiva (Abstenção)",
        }

        return {
            "label": res["label"],
            "dominant_label": res["dominant_label"],
            "verdict_pt": verdict_map.get(res["label"], "Não verificado"),
            "confidence": res["confidence"],
            "accepted": res["accepted"],
            "threshold": res["threshold"],
            "probabilities": res["probabilities"],
            "top_features": res["top_features"],
            "heuristic_reasons": triggers,
            "epistemic_tone": tone,
        }


classifier_service = ClassifierService()
