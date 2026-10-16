"""Extrator determinístico e estatístico de alegações factuais candidatas em transcrições de vídeo.

Utilizado como motor de contingência de Nível 2 (sem LLM / offline) conforme
o Plano de Contingência do EvidencIA e ADR-006.
"""

import re
from typing import List, Optional, Sequence, Tuple
from ml.classifier.features import normalize_text, SENSATIONAL_MARKERS, CREDIBILITY_MARKERS

# Padrões conversacionais típicos de vídeos do YouTube a serem filtrados
CONVERSATIONAL_PATTERNS = [
    r"\b(?:ta|esta) comecando (?:o |mais um )?(?:(?:seu|nosso) )?programa\b",
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
    r"\bta comecando\b.{0,60}\bprograma\b",
    r"\bcomecando\s+(?:o|seu|o seu)?\s*programa\b",
    r"\bprograma de saude aqui\b",
    r"\b(?:vem|venha) pra ca\b",
    r"\bolha so quem vem aqui\b",
    r"\bdoutor[, ]+tudo bem\b",
    r"\btudo bem[, ]+doutor\b",
    r"\bvamos chamar o\b",
    r"fala pessoal",
    r"muito obrigado por assistir",
    r"link na descricao",
    r"\bcomec\w* agora\b",
    r"\besta no ar\b",
    r"\bfi(?:que|quem|ca) conosco\b",
    r"\bdeix\w* (?:o )?(?:seu )?like\b",
    r"^(?:oi|e ai|fala) (?:pessoal|gente|galera)\b",
    r"^hoje vamos falar\b",
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


# Limites de legibilidade para frases exibidas no painel lateral.
MIN_SEGMENT_WORDS = 8
MAX_SEGMENT_WORDS = 25
MAX_CLAIM_WORDS = 35
# Silêncio entre dois eventos de legenda que marca o fim de uma oração falada.
PAUSE_BREAK_SECONDS = 0.8

# Conectivos e marcadores discursivos (forma normalizada, sem acento) que abrem
# uma nova oração; servem de ponto natural de quebra em fala sem pontuação.
DISCOURSE_MARKERS = frozenset({
    "entao", "portanto", "segundo", "estudos", "existem", "porque", "mas", "alem",
    "porem", "contudo", "entretanto", "todavia", "pois",
})


def _finish_sentence(words: List[str]) -> str:
    """Capitaliza a primeira letra e garante ponto final, sem alterar as palavras originais."""
    sentence = " ".join(words).rstrip(",;:")
    sentence = sentence[:1].upper() + sentence[1:]
    if sentence[-1:] not in ".!?":
        sentence += "."
    return sentence


def _segment_unpunctuated_stream(
    text: str,
    min_words: int = MIN_SEGMENT_WORDS,
    max_words: int = MAX_SEGMENT_WORDS,
) -> List[str]:
    """Divide um fluxo contínuo de fala sem pontuação (legenda ASR) em orações legíveis.

    Quebra antes de conectivos discursivos ou depois de vírgulas quando a oração já
    tem ao menos `min_words` palavras, e força a quebra ao atingir `max_words`.
    As palavras originais são preservadas para que cada frase continue sendo um
    trecho literal da transcrição (necessário para localizar o tempo no vídeo).
    """
    words = text.split()
    if not words:
        return []

    chunks: List[List[str]] = []
    current: List[str] = []
    for word in words:
        marker = normalize_text(word).strip(",;:.!?\"'") in DISCOURSE_MARKERS
        if current and (len(current) >= max_words or (marker and len(current) >= min_words)):
            chunks.append(current)
            current = []
        current.append(word)
        if len(current) >= min_words and word[-1] in ",;:":
            chunks.append(current)
            current = []
    if current:
        # Evita uma sobra curta e solta no fim, sem ultrapassar o limite de alegação.
        if chunks and len(current) < min_words and len(chunks[-1]) + len(current) <= MAX_CLAIM_WORDS:
            chunks[-1].extend(current)
        else:
            chunks.append(current)

    return [_finish_sentence(chunk) for chunk in chunks]


def segment_transcript(transcript: str) -> List[str]:
    """Segmenta a transcrição em frases curtas, mesmo quando a legenda não tem pontuação."""
    if not transcript:
        return []

    sentences: List[str] = []
    # Divide por quebras de linha e pontuação forte, mantendo a pontuação na frase.
    for chunk in re.split(r"(?<=[.!?])\s+|[\n\r]+", transcript):
        cleaned = re.sub(r"\s+", " ", chunk).strip()
        if not cleaned:
            continue
        if len(cleaned.split()) > MAX_CLAIM_WORDS:
            sentences.extend(_segment_unpunctuated_stream(cleaned))
        else:
            sentences.append(cleaned)
    return sentences


def segment_timed_captions(
    segments: Sequence[Tuple[str, float, float]],
    pause_seconds: float = PAUSE_BREAK_SECONDS,
) -> List[str]:
    """Agrupa eventos de legenda (texto, início, duração) em orações usando as pausas da fala.

    Uma pausa de ao menos `pause_seconds` fecha a oração corrente quando ela já tem
    `MIN_SEGMENT_WORDS` palavras; cada grupo passa depois pela segmentação por
    pontuação, conectivos e limite de palavras. O texto dos eventos é preservado,
    então cada frase continua sendo um trecho literal da transcrição.
    """
    groups: List[List[str]] = []
    current: List[str] = []
    previous_end: Optional[float] = None
    for text, start, duration in segments:
        words = text.split()
        if not words:
            continue
        if current and previous_end is not None and start - previous_end >= pause_seconds and len(current) >= MIN_SEGMENT_WORDS:
            groups.append(current)
            current = []
        current.extend(words)
        previous_end = start + duration
    if current:
        groups.append(current)

    sentences: List[str] = []
    for group in groups:
        sentences.extend(_finish_sentence(sentence.split()) for sentence in segment_transcript(" ".join(group)))
    return sentences


def split_transcript_sentences(transcript: str) -> List[str]:
    """Segmenta a transcrição contínua em sentenças candidatas utilizando pontuação e quebras."""
    # Filtra fragmentos muito curtos (menos de 5 palavras)
    return [sentence.rstrip(".!?") for sentence in segment_transcript(transcript) if len(sentence.split()) >= 5]


def shorten_claim(text: str) -> str:
    """Reduz uma alegação longa demais à oração mais saliente, preservando o texto literal."""
    if len(text.split()) <= MAX_CLAIM_WORDS:
        return text
    pieces = _segment_unpunctuated_stream(text)
    return max(pieces, key=score_claim_saliency)


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
    segments: Optional[Sequence[Tuple[str, float, float]]] = None,
) -> List[str]:
    """Extrai as principais sentenças com potencial de alegação factual verificável da transcrição.

    Com legendas temporizadas, as pausas da fala também delimitam as orações.
    """
    raw_sentences = segment_timed_captions(segments) if segments else segment_transcript(transcript)
    # Perguntas não afirmam nada; descarta antes de remover a pontuação final.
    sentences = [s.rstrip(".!?") for s in raw_sentences if not s.rstrip().endswith("?") and len(s.split()) >= 5]
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
