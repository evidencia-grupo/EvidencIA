import re
from typing import Dict, List, Optional
from ml.datasets.dataset_downloader import load_local_sample_dataset
from app.schemas import FactCheckingSource


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
            source = FactCheckingSource(
                id=f"src-br-{best_match['id']}",
                title=f"{best_match['publisher']}: {best_match['claim']}",
                url=best_match.get("review_url", "https://lupa.uol.com.br"),
                domain=best_match.get("domain", "agenciachecagem.org"),
                reliabilityScore=0.96,
            )
            return {
                "claim": best_match["claim"],
                "status": best_match["status"],
                "rating_text": best_match["rating_text"],
                "evidence_summary": best_match["evidence_summary"],
                "source": source,
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
