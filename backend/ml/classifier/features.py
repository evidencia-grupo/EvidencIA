"""Extração de atributos léxicos, estatísticos e estilísticos para classificação de alegações."""

import math
import re
import unicodedata
from collections import Counter
from typing import Dict, List, Set, Tuple

STOPWORDS_PT = {
    "o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "sob", "sobre",
    "que", "e", "ou", "se", "como", "mais", "mas", "porém", "contudo", "todavia",
    "foi", "foram", "é", "era", "eram", "são", "ser", "sendo", "ter", "tem", "têm",
    "tinha", "tinham", "este", "esta", "estes", "estas", "esse", "essa", "esses", "essas",
    "aquele", "aquela", "aqueles", "aquelas", "isto", "isso", "aquilo", "seu", "sua",
    "seus", "suas", "meu", "minha", "nosso", "nossa", "nossos", "nossas", "ele", "ela",
    "eles", "elas", "você", "vocês", "ao", "aos", "à", "às", "pelo", "pela", "pelos", "pelas"
}

SENSATIONAL_MARKERS = {
    "urgente", "bomba", "revelado", "segredo", "ocultado", "milagroso", "cura",
    "proibido", "compartilhe", "apaguem", "vazou", "mentira", "verdade oculta",
    "perigo", "alerta", "absurdo", "inacreditavel", "chocante", "revolucionario",
    "ninguem conta", "estao escondendo", "veneno", "destruir", "conspiracao"
}

CREDIBILITY_MARKERS = {
    "estudo", "pesquisa", "relatorio", "oficial", "segundo", "publicado",
    "ministerio", "anvisa", "fiocruz", "ibge", "nature", "revista", "universidade",
    "dados", "conforme", "comprovado", "ensaios", "diretriz", "organizacao",
    "secretaria", "banco central", "medida provisoria", "resolucao", "portaria"
}


def normalize_text(text: str) -> str:
    """Remove diacríticos e normaliza espaços para manter robustez léxica."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return normalized.lower().strip()


def tokenize(text: str, remove_stopwords: bool = True) -> List[str]:
    """Segmenta o texto em palavras limpas."""
    norm = normalize_text(text)
    words = re.findall(r"\b[a-z0-9_]{2,}\b", norm)
    if remove_stopwords:
        return [w for w in words if w not in STOPWORDS_PT]
    return words


def extract_ngrams(tokens: List[str], n: int = 2) -> List[str]:
    """Gera n-gramas a partir da lista de tokens."""
    if len(tokens) < n:
        return []
    return ["_".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def extract_stylistic_features(raw_text: str) -> Dict[str, float]:
    """Extrai marcadores estilísticos e emocionais frequentes em desinformação."""
    length = max(1, len(raw_text))
    words = raw_text.split()
    word_count = max(1, len(words))

    # Proporção de letras maiúsculas (gritaria textual)
    upper_chars = sum(1 for c in raw_text if c.isupper())
    uppercase_ratio = upper_chars / length

    # Pontuação expressiva
    exclamations = raw_text.count("!")
    questions = raw_text.count("?")
    exclamation_density = exclamations / word_count
    question_density = questions / word_count

    norm_lower = normalize_text(raw_text)
    sensational_hits = sum(1 for marker in SENSATIONAL_MARKERS if marker in norm_lower)
    credibility_hits = sum(1 for marker in CREDIBILITY_MARKERS if marker in norm_lower)

    return {
        "style_uppercase_ratio": min(1.0, uppercase_ratio * 3.0),
        "style_exclamation_density": min(1.0, exclamation_density),
        "style_question_density": min(1.0, question_density),
        "style_sensational_score": min(1.0, sensational_hits * 0.25),
        "style_credibility_score": min(1.0, credibility_hits * 0.25),
    }


class TFIDFVectorizer:
    """Vetorizador TF-IDF puro e determinístico otimizado para português."""

    def __init__(self, max_features: int = 1000, min_df: int = 1, use_bigrams: bool = True):
        self.max_features = max_features
        self.min_df = min_df
        self.use_bigrams = use_bigrams
        self.vocabulary_: Dict[str, int] = {}
        self.idf_: Dict[str, float] = {}

    def fit(self, documents: List[str]) -> "TFIDFVectorizer":
        """Calcula as frequências de documento e índices do vocabulário."""
        doc_count = len(documents)
        df_counter: Counter = Counter()

        for doc in documents:
            tokens = tokenize(doc)
            features = set(tokens)
            if self.use_bigrams:
                features.update(extract_ngrams(tokens, 2))
            df_counter.update(features)

        # Filtra por min_df e limita a max_features
        valid_items = [
            (term, freq) for term, freq in df_counter.items()
            if freq >= self.min_df
        ]
        # Ordena por frequência decrescente
        valid_items.sort(key=lambda x: x[1], reverse=True)
        top_items = valid_items[:self.max_features]

        self.vocabulary_ = {term: idx for idx, (term, _) in enumerate(top_items)}
        self.idf_ = {
            term: math.log((1 + doc_count) / (1 + freq)) + 1.0
            for term, freq in top_items
        }
        return self

    def transform(self, documents: List[str]) -> List[Dict[str, float]]:
        """Transforma documentos em vetores esparsos de TF-IDF com features estilísticas."""
        results = []
        for doc in documents:
            tokens = tokenize(doc)
            all_features = list(tokens)
            if self.use_bigrams:
                all_features.extend(extract_ngrams(tokens, 2))

            counts = Counter(all_features)
            total_terms = max(1, len(all_features))

            vec: Dict[str, float] = {}
            for term, count in counts.items():
                if term in self.vocabulary_:
                    tf = count / total_terms
                    vec[term] = tf * self.idf_[term]

            # Normalização L2
            norm = math.sqrt(sum(v * v for v in vec.values()))
            if norm > 0:
                for k in vec:
                    vec[k] /= norm

            # Adiciona features estilísticas
            stylistic = extract_stylistic_features(doc)
            vec.update(stylistic)
            results.append(vec)

        return results

    def fit_transform(self, documents: List[str]) -> List[Dict[str, float]]:
        return self.fit(documents).transform(documents)

    def to_dict(self) -> dict:
        return {
            "max_features": self.max_features,
            "min_df": self.min_df,
            "use_bigrams": self.use_bigrams,
            "vocabulary": self.vocabulary_,
            "idf": self.idf_,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TFIDFVectorizer":
        vec = cls(
            max_features=data["max_features"],
            min_df=data["min_df"],
            use_bigrams=data["use_bigrams"],
        )
        vec.vocabulary_ = data["vocabulary"]
        vec.idf_ = data["idf"]
        return vec
