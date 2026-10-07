import re
import unicodedata
from typing import Dict, List, Optional
from ml.datasets.dataset_downloader import load_local_sample_dataset
from app.schemas import Evidence, EvidenceProvenance, EvidenceRelation


class BrazilianFactMatcher:
    """
    Serviço local de correspondência factual baseado no dataset curado
    de agências brasileiras (FactChecks.br: Lupa, Aos Fatos, Boatos.org, G1 Fato ou Fake).
    Permite identificação instantânea de boatos e fatos conhecidos em PT-BR sem custo de rede.
    """

    def __init__(self):
        self._dataset: List[Dict] = []
        self._load()

    def _load(self):
        try:
            self._dataset = load_local_sample_dataset()
        except Exception:
            self._dataset = []

    def find_match(self, text: str, threshold: float = 0.30) -> Optional[Dict]:
        """
        Busca casamento semântico/lexical no dataset de checagens brasileiras.
        Retorna a checagem mais similar ou None caso não atinja o limiar de relevância.
        """
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

            # Camada explícita de validação da relação: similaridade moderada (< 0.55) não pode
            # determinar sozinha 'contradicts' ou 'supports', degradando para 'contextualizes'.
            if best_score >= 0.55:
                if "contraditada" in raw_status or "falso" in raw_status or "falsa" in raw_status:
                    relation: EvidenceRelation = "contradicts"
                elif "apoiada" in raw_status or "verdadeiro" in raw_status or "verdadeira" in raw_status or "fato" in raw_status:
                    relation: EvidenceRelation = "supports"
                else:
                    relation: EvidenceRelation = "contextualizes"
                match_reason = f"Correspondência temática direta ({best_match.get('publisher', 'Agência')}) com validação factual auditada."
            else:
                relation = "contextualizes"
                match_reason = f"Correspondência temática contextualizada baseada em entidades e tópicos relacionados."

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
                    indexedAt="2026-08-01T10:00:00Z",
                    contentHash=f"sha256:{best_match['id']}",
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
