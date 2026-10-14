import re
import json
import hashlib
from datetime import datetime, timezone
import unicodedata
from typing import Dict, List, Optional
from ml.datasets.dataset_downloader import load_local_sample_dataset
from app.config import settings
from app.schemas import Evidence, EvidenceProvenance, EvidenceRelation


class BrazilianFactMatcher:
    """
    Serviço local de correspondência factual baseado no dataset curado
    de agências brasileiras (FactChecks.br: Lupa, Aos Fatos, Boatos.org, G1 Fato ou Fake).
    Permite identificação instantânea de boatos e fatos conhecidos em PT-BR sem custo de rede.
    """

    def __init__(self):
        self._dataset: List[Dict] = []
        self._loaded_at = ""
        self._load()

    def _load(self):
        try:
            self._dataset = load_local_sample_dataset()
            self._loaded_at = datetime.now(timezone.utc).isoformat()
        except Exception:
            self._dataset = []

    def find_match(self, text: str, threshold: float = 0.30) -> Optional[Dict]:
        """
        Busca casamento semântico/lexical no dataset de checagens brasileiras.
        Retorna a checagem mais similar ou None caso não atinja o limiar de relevância.
        """
        # The bundled demo corpus is never served as factual evidence in production.
        if settings.is_production():
            return None
        if not self._dataset:
            self._load()

        tokens_text = self._tokenize(text)
        if not tokens_text:
            return None

        best_match: Optional[Dict] = None
        best_score = 0.0

        domain_keywords = {
            "sus", "saude", "dengue", "vacina", "vacinas", "vacinacao", "diabetes",
            "anvisa", "cloroquina", "ivermectina", "polio", "sarampo", "pix", "inss",
            "banana", "limao", "bolsa", "familia", "remedio", "remedios", "cancer",
            "estacao", "primaria", "prevencao", "urna", "urnas", "fraude", "biometria",
            "aposentadoria", "qdenga", "ozonioterapia", "aspartame"
        }

        for entry in self._dataset:
            tokens_claim = self._tokenize(entry.get("claim", ""))
            if not tokens_claim:
                continue

            intersection = tokens_text.intersection(tokens_claim)
            union = tokens_text.union(tokens_claim)
            if not intersection:
                continue

            jaccard = len(intersection) / len(union) if union else 0.0
            if len(intersection) < 2 and jaccard < 0.5:
                continue

            overlap = len(intersection) / min(len(tokens_text), len(tokens_claim)) if tokens_text and tokens_claim else 0.0

            # Score balanceado: prioriza overlap semântico ponderado
            score = (0.45 * jaccard) + (0.55 * overlap)

            # Bônus para termos de domínio altamente específicos
            matched_keywords = intersection.intersection(domain_keywords)
            if matched_keywords:
                score += min(0.18, len(matched_keywords) * 0.06)

            if score > best_score and score >= threshold:
                best_score = score
                best_match = entry

        if best_match:
            raw_status = (best_match.get("status") or "").lower()

            tokens_claim = self._tokenize(best_match.get("claim", ""))
            intersection = tokens_text.intersection(tokens_claim)
            union = tokens_text.union(tokens_claim)
            jaccard = len(intersection) / len(union) if union else 0.0
            overlap = len(intersection) / min(len(tokens_text), len(tokens_claim)) if tokens_text and tokens_claim else 0.0

            # Detecção de negação e inversão de polaridade (ex: vídeo desmentindo o boato)
            text_lower = text.lower()
            negation_terms = {"nao", "não", "nunca", "jamais", "falso", "mentira", "desmentido", "fake", "boato"}
            has_negation = any(re.search(rf"\b{term}\b", text_lower) for term in negation_terms)
            claim_lower = best_match.get("claim", "").lower()
            claim_has_negation = any(re.search(rf"\b{term}\b", claim_lower) for term in negation_terms)
            polarity_mismatch = has_negation != claim_has_negation

            # Regra estrita contra falso positivo factual:
            # Similaridade lexical indica apenas relevância de recuperação (candidato de fact-check).
            # Emit factual stance only for the same textual proposition.
            # Paraphrases, changed numbers/predicates and negation stay contextual.
            def normalize_proposition(value):
                return " ".join(value.casefold().strip(" .!?").split())
            is_high_propositional_match = (
                normalize_proposition(text) == normalize_proposition(best_match.get("claim", ""))
                and not polarity_mismatch
            )

            if is_high_propositional_match:
                if "contraditada" in raw_status or "falso" in raw_status or "falsa" in raw_status:
                    relation: EvidenceRelation = "contradicts"
                    match_reason = f"Checagem da {best_match.get('publisher', 'Agência')} apurou esta alegação específica e atestou falsidade ou distorção factual."
                elif "apoiada" in raw_status or "verdadeiro" in raw_status or "verdadeira" in raw_status or "fato" in raw_status:
                    relation: EvidenceRelation = "supports"
                    match_reason = f"Checagem da {best_match.get('publisher', 'Agência')} confirmou a veracidade e conformidade oficial desta alegação."
                else:
                    relation = "contextualizes"
                    match_reason = f"Correspondência direta com checagem da {best_match.get('publisher', 'Agência')} que esclarece o contexto factual."
            else:
                relation = "contextualizes"
                if polarity_mismatch:
                    match_reason = f"Fonte relacionada ({best_match.get('publisher', 'Agência')}): o vídeo aborda ou questiona o tema, fornecendo contexto jornalístico apurado."
                else:
                    match_reason = f"Fonte jornalística relacionada ({best_match.get('publisher', 'Agência')}) com apuração temática sobre entidades ou tópicos afins."

            evidence = Evidence(
                sourceId=f"src-br-{best_match['id']}",
                relation=relation,
                title=f"{best_match.get('publisher', 'Agência')}: {best_match.get('claim', '')}",
                url=best_match.get("review_url", "https://lupa.uol.com.br"),
                publishedAt=best_match.get("published_at") or "",
                publisher=best_match.get("publisher", "Agência de Fact-Checking"),
                snippet=best_match.get("evidence_summary", ""),
                matchReason=match_reason,
                provenance=EvidenceProvenance(
                    dataset="factchecksbr",
                    indexedAt=self._loaded_at,
                    contentHash="sha256:" + hashlib.sha256(
                        json.dumps(best_match, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                    ).hexdigest(),
                ),
            )
            return {
                "claim": best_match["claim"],
                "status": best_match["status"],
                "rating_text": best_match.get("rating_text", ""),
                "evidence_summary": best_match.get("evidence_summary", ""),
                "evidence": evidence,
                "relation": relation,
                "confidence": min(0.98, max(0.85, 0.75 + (best_score * 0.25))),
            }

        return None

    def _tokenize(self, text: str) -> set:
        stopwords = {
            "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
            "em", "no", "na", "nos", "nas", "por", "para", "com", "que", "e",
            "se", "nao", "não", "como", "mais", "mas", "foi", "tem", "são",
            "este", "esta", "esse", "essa", "aquele", "aquela", "seu", "sua",
            "pelo", "pela", "pelos", "pelas", "ser", "sendo", "sobre", "qual",
            "ter", "tem", "têm", "isso", "isto", "aquilo", "está", "estao"
        }
        normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
        words = re.findall(r"\b[a-z]{3,}\b", normalized)
        return {w for w in words if w not in stopwords}


brazilian_fact_matcher = BrazilianFactMatcher()
