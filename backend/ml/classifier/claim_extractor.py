"""Extrator determinístico e estatístico de alegações factuais candidatas em transcrições de vídeo.

Utilizado como motor de contingência de Nível 2 (sem LLM / offline) conforme
o Plano de Contingência do EvidencIA e ADR-006.
"""

import re
from typing import List, Tuple
from ml.classifier.features import normalize_text, SENSATIONAL_MARKERS, CREDIBILITY_MARKERS

# Padrões conversacionais típicos de vídeos do YouTube a serem filtrados
CONVERSATIONAL_PATTERNS = [
    r"sejam bem[\s-]?vindos",
    r"bem[\s-]?vindo a mais um video",
    r"no video de hoje",
    r"deixe o like",
    r"deixar o like",
    r"deixe seu like",
    r"deixa o like",
    r"se inscreva no canal",
    r"inscreva[\s-]?se",
    r"ative o sininho",
    r"compartilhe com os amigos",
    r"compartilhar com os amigos",
    r"comente aqui embaixo",
    r"deixe seu comentario",
    r"ate o proximo video",
    r"ate a proxima",
    r"ola pessoal",
    r"fala pessoal",
    r"muito obrigado por assistir",
    r"link na descricao",
    r"clique no link",
]

# Verbos de asserção factual e atribuição frequentes em alegações jornalísticas e desinformativas
FACTUAL_VERB_PATTERNS = [
    r"\b(anunciou|anuncia|declarou|afirmou|informou|publicou|divulgou)\b",
    r"\b(comprovou|comprova|provou|revelou|descobriu|demonstrou)\b",
    r"\b(proibiu|proibe|aprovou|aprova|revogou|cassou|cancelou)\b",
    r"\b(cura|curou|elimina|destroi|mata|causa|provoca|gera)\b",
    r"\b(confiscou|confisca|bloqueou|bloqueia|cobra|cobrou)\b",
    r"\b(aumentou|reduziu|caiu|subiu|zerou)\b",
]

# Entidades institucionais, científicas ou temáticas frequentes em alegações
TOPIC_PATTERNS = [
    r"\b(vacina|vacinacao|anvisa|fiocruz|sus|ministerio|governo|saude)\b",
    r"\b(banco central|pix|receita federal|bolsa familia|inss|beneficio)\b",
    r"\b(urna|eleicoes|tse|stf|constituicao|lei|decreto)\b",
    r"\b(diabetes|cancer|dengue|covid|gripe|remedio|tratamento)\b",
    r"\b(nasa|inpe|satelite|desmatamento|clima|aquecimento)\b",
]


def split_transcript_sentences(transcript: str) -> List[str]:
    """Segmenta a transcrição contínua em sentenças candidatas utilizando pontuação e quebras."""
    if not transcript:
        return []

    # Divide por quebras de linha e pontuação forte (. ! ? ; e pausas longas)
    raw_splits = re.split(r"[\n\r.!?]+", transcript)
    sentences = []

    for chunk in raw_splits:
        cleaned = re.sub(r"\s+", " ", chunk).strip()
        words = cleaned.split()
        # Filtra fragmentos muito curtos (menos de 5 palavras)
        if len(words) >= 5:
            sentences.append(cleaned)

    return sentences


def is_conversational_filler(sentence: str) -> bool:
    """Verifica se a frase é ruído conversacional (pedidos de like, saudações, etc.)."""
    norm = normalize_text(sentence)
    for pattern in CONVERSATIONAL_PATTERNS:
        if re.search(pattern, norm):
            return True
    return False


def score_claim_saliency(sentence: str) -> float:
    """Calcula score de saliência factual [0.0 a 1.0] indicando probabilidade de ser alegação verificável."""
    if is_conversational_filler(sentence):
        return 0.0

    words = sentence.split()
    word_count = len(words)

    # Penaliza frases excessivamente curtas ou desmesuradamente longas
    if word_count < 6 or word_count > 45:
        return 0.1

    norm = normalize_text(sentence)
    score = 0.25  # Base para frase bem formada

    # Presença de verbos de asserção factual (+0.30)
    for v_pat in FACTUAL_VERB_PATTERNS:
        if re.search(v_pat, norm):
            score += 0.30
            break

    # Presença de entidades temáticas relevantes (+0.25)
    for t_pat in TOPIC_PATTERNS:
        if re.search(t_pat, norm):
            score += 0.25
            break

    # Presença de dados quantitativos ou estatísticos (+0.15)
    if re.search(r"\b(\d+|por cento|porcento|milhoes|bilhoes|mil|reais|dias|anos)\b", norm):
        score += 0.15

    # Marcadores explícitos de sensacionalismo ou credibilidade (+0.10)
    if any(m in norm for m in SENSATIONAL_MARKERS) or any(m in norm for m in CREDIBILITY_MARKERS):
        score += 0.10

    return min(1.0, score)


def extract_candidate_claims(
    transcript: str,
    max_claims: int = 3,
    min_saliency: float = 0.50,
) -> List[str]:
    """Extrai as principais sentenças com potencial de alegação factual verificável da transcrição."""
    sentences = split_transcript_sentences(transcript)
    if not sentences:
        return []

    scored_candidates: List[Tuple[str, float]] = []
    seen_texts = set()

    for sentence in sentences:
        saliency = score_claim_saliency(sentence)
        norm_key = normalize_text(sentence[:40])
        if saliency >= min_saliency and norm_key not in seen_texts:
            seen_texts.add(norm_key)
            scored_candidates.append((sentence, saliency))

    # Ordena por saliência decrescente
    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    return [s for s, _ in scored_candidates[:max_claims]]
