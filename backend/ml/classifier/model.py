"""Modelo de classificação supervisionada probabilística com abstenção e limiares de aceitação."""

import json
import math
import os
from typing import Any, Dict, List, Optional, Tuple
from ml.classifier.features import TFIDFVectorizer


class ClaimClassifier:
    """Classificador estatístico probabilístico para detecção de desinformação em PT-BR.
    
    Implementa Naive Bayes Multinomial com scores normalizados e análise de limiares.
    100% determinístico, reproduzível e serializável sem dependências externas compiladas.
    """

    def __init__(
        self,
        alpha: float = 0.5,
        acceptance_threshold: float = 0.60,
        vectorizer: Optional[TFIDFVectorizer] = None,
    ):
        self.alpha = alpha
        self.acceptance_threshold = acceptance_threshold
        self.vectorizer = vectorizer or TFIDFVectorizer(max_features=2500, use_bigrams=True)
        self.class_priors: Dict[str, float] = {"fake": 0.5, "true": 0.5}
        self.feature_log_probs: Dict[str, Dict[str, float]] = {"fake": {}, "true": {}}
        self.classes = ["fake", "true"]
        self.is_trained = False

    def train(self, texts: List[str], labels: List[str]) -> "ClaimClassifier":
        """Treina o classificador supervisionado com o conjunto rotulado."""
        if not texts or not labels or len(texts) != len(labels):
            raise ValueError("Textos e rótulos devem ser não-vazios e possuir o mesmo tamanho.")

        # 1. Ajusta o vetorizador e extrai vetores
        vectors = self.vectorizer.fit_transform(texts)

        # 2. Contagem por classe
        total_docs = len(texts)
        fake_indices = [i for i, lbl in enumerate(labels) if lbl == "fake"]
        true_indices = [i for i, lbl in enumerate(labels) if lbl == "true"]

        n_fake = len(fake_indices)
        n_true = len(true_indices)

        if n_fake == 0 or n_true == 0:
            raise ValueError("O conjunto de treino deve conter amostras de ambas as classes ('fake' e 'true').")

        self.class_priors["fake"] = n_fake / total_docs
        self.class_priors["true"] = n_true / total_docs

        # 3. Agrega frequências ponderadas de features por classe
        fake_feature_sums: Dict[str, float] = {}
        true_feature_sums: Dict[str, float] = {}
        total_fake_weight = 0.0
        total_true_weight = 0.0

        for idx in fake_indices:
            for feat, val in vectors[idx].items():
                fake_feature_sums[feat] = fake_feature_sums.get(feat, 0.0) + val
                total_fake_weight += val

        for idx in true_indices:
            for feat, val in vectors[idx].items():
                true_feature_sums[feat] = true_feature_sums.get(feat, 0.0) + val
                total_true_weight += val

        # 4. Vocabulário total de features (incluindo estilísticas)
        all_features = set(fake_feature_sums.keys()).union(true_feature_sums.keys())
        vocab_size = max(1, len(all_features))

        # 5. Cálculo das log-probabilidades condicionais com suavização de Laplace
        denom_fake = total_fake_weight + (self.alpha * vocab_size)
        denom_true = total_true_weight + (self.alpha * vocab_size)

        self.feature_log_probs["fake"] = {
            feat: math.log((fake_feature_sums.get(feat, 0.0) + self.alpha) / denom_fake)
            for feat in all_features
        }
        self.feature_log_probs["true"] = {
            feat: math.log((true_feature_sums.get(feat, 0.0) + self.alpha) / denom_true)
            for feat in all_features
        }

        # Valores de probabilidade para features não vistas (OOD fallback)
        self._default_log_prob_fake = math.log(self.alpha / denom_fake)
        self._default_log_prob_true = math.log(self.alpha / denom_true)

        self.is_trained = True
        return self

    def predict_proba(self, text: str) -> Dict[str, float]:
        """Calcula probabilidades normalizadas P(fake) e P(true) para o texto."""
        if not self.is_trained:
            raise RuntimeError("O modelo precisa ser treinado antes da predição.")

        vector = self.vectorizer.transform([text])[0]

        log_prior_fake = math.log(self.class_priors["fake"])
        log_prior_true = math.log(self.class_priors["true"])

        log_lik_fake = 0.0
        log_lik_true = 0.0

        for feat, val in vector.items():
            lp_f = self.feature_log_probs["fake"].get(feat, self._default_log_prob_fake)
            lp_t = self.feature_log_probs["true"].get(feat, self._default_log_prob_true)
            log_lik_fake += val * lp_f
            log_lik_true += val * lp_t

        score_fake = log_prior_fake + log_lik_fake
        score_true = log_prior_true + log_lik_true

        # Softmax estável
        max_score = max(score_fake, score_true)
        exp_fake = math.exp(score_fake - max_score)
        exp_true = math.exp(score_true - max_score)
        total_exp = exp_fake + exp_true

        prob_fake = exp_fake / total_exp
        prob_true = exp_true / total_exp

        return {"fake": prob_fake, "true": prob_true}

    def predict(self, text: str, threshold: Optional[float] = None) -> Dict[str, Any]:
        """Realiza predição com abstenção por limiar de score.
        
        Retorna:
            - label: "fake", "true" ou "unverified" (se abaixo do limiar)
            - confidence: score de confiança na predição mais provável
            - accepted: booleano indicando se a confiança superou o limiar
            - probabilities: dict com P(fake) e P(true)
            - top_evidence_features: fatores que mais pesaram na decisão
        """
        probs = self.predict_proba(text)
        prob_fake = probs["fake"]
        prob_true = probs["true"]

        dominant_label = "fake" if prob_fake >= prob_true else "true"
        confidence = max(prob_fake, prob_true)

        eff_threshold = threshold if threshold is not None else self.acceptance_threshold
        accepted = confidence >= eff_threshold

        label = dominant_label if accepted else "unverified"

        # Atribuição de importância das features
        top_features = self._explain(text, dominant_label)

        return {
            "label": label,
            "dominant_label": dominant_label,
            "confidence": round(confidence, 4),
            "accepted": accepted,
            "threshold": eff_threshold,
            "probabilities": {
                "fake": round(prob_fake, 4),
                "true": round(prob_true, 4),
            },
            "top_features": top_features,
        }

    def _explain(self, text: str, dominant_label: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Identifica os termos e marcas que mais contribuíram para o veredito."""
        vector = self.vectorizer.transform([text])[0]
        opp_label = "true" if dominant_label == "fake" else "fake"

        contributions: List[Tuple[str, float]] = []
        for feat, val in vector.items():
            lp_dom = self.feature_log_probs[dominant_label].get(feat, self._default_log_prob_fake)
            lp_opp = self.feature_log_probs[opp_label].get(feat, self._default_log_prob_true)
            # Log-odds ratio ponderado pelo valor da feature
            diff = val * (lp_dom - lp_opp)
            if diff > 0:
                contributions.append((feat, round(diff, 4)))

        contributions.sort(key=lambda x: x[1], reverse=True)
        return contributions[:top_k]

    def save(self, filepath: str) -> None:
        """Salva todos os parâmetros e o vocabulário em JSON."""
        data = {
            "alpha": self.alpha,
            "acceptance_threshold": self.acceptance_threshold,
            "class_priors": self.class_priors,
            "feature_log_probs": self.feature_log_probs,
            "default_log_prob_fake": self._default_log_prob_fake,
            "default_log_prob_true": self._default_log_prob_true,
            "vectorizer": self.vectorizer.to_dict(),
        }
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)

    @classmethod
    def load(cls, filepath: str) -> "ClaimClassifier":
        """Reconstrói o classificador a partir do artefato serializado."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        vec = TFIDFVectorizer.from_dict(data["vectorizer"])
        model = cls(
            alpha=data["alpha"],
            acceptance_threshold=data["acceptance_threshold"],
            vectorizer=vec,
        )
        model.class_priors = data["class_priors"]
        model.feature_log_probs = data["feature_log_probs"]
        model._default_log_prob_fake = data["default_log_prob_fake"]
        model._default_log_prob_true = data["default_log_prob_true"]
        model.is_trained = True
        return model
