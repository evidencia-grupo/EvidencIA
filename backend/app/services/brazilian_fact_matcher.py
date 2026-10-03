import re
from typing import Dict, List, Optional
from ml.datasets.dataset_downloader import load_local_sample_dataset
from app.schemas import Evidence, EvidenceProvenance, EvidenceRelation


class BrazilianFactMatcher:
    """
    Serviço local de correspondência factual baseado no dataset curado
    de agências brasileiras (FactChecks.br: Lupa, Aos Fatos, Boatos.org).
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

    def find_match(self, text: str, threshold: float = 0.35) -> Optional[Dict]:
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

        for entry in self._dataset:
            tokens_claim = self._tokenize(entry.get("claim", ""))
            if not tokens_claim:
                continue

            intersection = tokens_text.intersection(tokens_claim)
            union = tokens_text.union(tokens_claim)
            jaccard = len(intersection) / len(union) if union else 0.0

            if jaccard > best_score and jaccard >= threshold:
                best_score = jaccard
                best_match = entry

        if best_match:
            raw_status = (best_match.get("status") or "").lower()
            if "contraditada" in raw_status or "falso" in raw_status or "falsa" in raw_status:
                relation: EvidenceRelation = "contradicts"
            elif "apoiada" in raw_status or "verdadeiro" in raw_status or "verdadeira" in raw_status:
                relation: EvidenceRelation = "supports"
            else:
                relation: EvidenceRelation = "contextualizes"

            evidence = Evidence(
                sourceId=f"src-br-{best_match['id']}",
                relation=relation,
                title=f"{best_match.get('publisher', 'Agência')}: {best_match.get('claim', '')}",
                url=best_match.get("review_url", "https://lupa.uol.com.br"),
                publishedAt=best_match.get("published_at", "2026-01-01T00:00:00Z"),
                publisher=best_match.get("publisher", "Agência de Fact-Checking"),
                snippet=best_match.get("evidence_summary", ""),
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
                "confidence": min(0.98, 0.85 + (best_score * 0.15)),
            }

        return None

    def _tokenize(self, text: str) -> set:
        stopwords = {
            "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
            "em", "no", "na", "nos", "nas", "por", "para", "com", "que", "e",
            "se", "nao", "não", "como", "mais", "mas", "foi", "tem", "são"
        }
        words = re.findall(r"\b[a-zA-ZáéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ]{3,}\b", text.lower())
        return {w for w in words if w not in stopwords}


brazilian_fact_matcher = BrazilianFactMatcher()
