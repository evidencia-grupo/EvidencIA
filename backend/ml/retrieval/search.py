"""Módulo de busca vetorial para o pipeline EvidencIA.

Expõe ``search(query, k, filters) -> list[SearchHit]``.
Usa BM25 como fallback quando Chroma não está disponível.
Import tardio de chromadb.

Refs: ADR-001, IS-06.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional, Union

from ml.schemas.evidence import EvidenceRecord, NewsRecord, Provenance

logger = logging.getLogger(__name__)

CanonicalRecord = Union[EvidenceRecord, NewsRecord]


@dataclass
class SearchHit:
    """Resultado de uma busca no índice de evidências."""

    evidence_id: str
    score: float  # similaridade 0–1 (maior = mais similar)
    record: Optional[CanonicalRecord]
    provenance: Optional[Provenance]


def search(
    query: str,
    k: int = 5,
    filters: Optional[dict[str, Any]] = None,
    collection_name: str = "evidencia",
    chroma_dir: Optional[str] = None,
    use_bm25_fallback: bool = True,
    corpus: Optional[list[dict]] = None,
) -> list[SearchHit]:
    """Busca os top-k documentos mais similares à query.

    Tenta Chroma primeiro; usa BM25 como fallback se Chroma não disponível.

    Args:
        query: Texto da consulta.
        k: Número máximo de resultados.
        filters: Filtros opcionais. Suportado: ``{"after": "YYYY-MM-DD"}``.
        collection_name: Nome da coleção Chroma.
        chroma_dir: Diretório de persistência do Chroma.
        use_bm25_fallback: Se True, usa BM25 quando Chroma não disponível.
        corpus: Corpus alternativo para BM25 (lista de dicts com 'id' e 'text').

    Returns:
        Lista de ``SearchHit`` ordenada por score descendente.
    """
    try:
        return _search_chroma(query, k=k, filters=filters, collection_name=collection_name, chroma_dir=chroma_dir)
    except ImportError:
        logger.debug("chromadb não disponível — usando BM25 como fallback")
    except Exception as exc:
        logger.warning("Erro no Chroma: %s — usando BM25 como fallback", exc)

    if use_bm25_fallback and corpus:
        return _search_bm25(query, k=k, corpus=corpus, filters=filters)

    return []


def _search_chroma(
    query: str,
    k: int,
    filters: Optional[dict],
    collection_name: str,
    chroma_dir: Optional[str],
) -> list[SearchHit]:
    """Busca usando Chroma (import tardio)."""
    import chromadb  # type: ignore  # noqa: PLC0415
    from ml.embeddings.encoder import default_encoder

    import os
    from ml.retrieval.index import DEFAULT_CHROMA_DIR

    persist_dir = chroma_dir or DEFAULT_CHROMA_DIR
    if not os.path.isdir(persist_dir):
        raise FileNotFoundError(f"Diretório Chroma não encontrado: {persist_dir}")

    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_collection(collection_name)

    # Monta where clause para filtro temporal
    where: Optional[dict] = None
    if filters and "after" in filters:
        where = {"published_at": {"$gte": filters["after"]}}

    query_embedding = default_encoder.encode([query])[0]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where=where,
        include=["documents", "distances", "metadatas"],
    )

    hits: list[SearchHit] = []
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for eid, dist, doc, meta in zip(ids, distances, documents, metadatas):
        # Chroma com cosine retorna distância 0–2; converte para similaridade 0–1
        similarity = max(0.0, 1.0 - dist / 2.0)
        record = None
        if meta.get("record_json"):
            try:
                raw_record = json.loads(meta["record_json"])
                record_class = EvidenceRecord if raw_record.get("record_type") == "fact_check" else NewsRecord
                record = record_class.model_validate(raw_record)
            except (ValueError, TypeError, AttributeError):
                logger.warning("Registro inválido no índice: %s", eid)
        hits.append(SearchHit(
            evidence_id=eid,
            score=round(similarity, 4),
            record=record,
            provenance=record.provenance if record else None,
        ))

    return hits


def _search_bm25(
    query: str,
    k: int,
    corpus: list[dict],
    filters: Optional[dict] = None,
) -> list[SearchHit]:
    """Busca usando BM25 (rank-bm25, import tardio).

    Args:
        query: Texto da consulta.
        k: Número de resultados.
        corpus: Lista de dicts com ``id`` e ``text``.
        filters: Filtros opcionais (suportado: ``{"after": "YYYY-MM-DD"}``).

    Returns:
        Lista de ``SearchHit`` ordenada por score BM25.
    """
    # Filtragem temporal básica
    filtered_corpus = corpus
    if filters and "after" in filters:
        after = filters["after"]
        filtered_corpus = [
            doc for doc in corpus
            if str(doc.get("published_at", ""))[:10] >= after
        ]

    if not filtered_corpus:
        return []

    try:
        from rank_bm25 import BM25Okapi  # type: ignore  # noqa: PLC0415
        tokenized = [doc["text"].lower().split() for doc in filtered_corpus]
        bm25 = BM25Okapi(tokenized)
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)
    except ImportError:
        # Fallback para TF-IDF / overlap lexical em memória (offline)
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
            texts = [doc["text"] for doc in filtered_corpus]
            vec = TfidfVectorizer().fit(texts + [query])
            doc_vecs = vec.transform(texts)
            query_vec = vec.transform([query])
            scores = (doc_vecs * query_vec.T).toarray().ravel()
        except ImportError:
            # Fallback puro padrão Python
            q_set = set(query.lower().split())
            scores = [
                len(q_set.intersection(set(doc["text"].lower().split()))) / max(1, len(q_set))
                for doc in filtered_corpus
            ]

    # Ordena por score e retorna top-k
    indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]

    hits: list[SearchHit] = []
    for idx, score in indexed:
        if score <= 0:
            break
        doc = filtered_corpus[idx]
        # Normaliza score BM25 para 0–1 (heurística simples)
        normalized_score = min(1.0, score / (max(scores) + 1e-9))
        hits.append(SearchHit(
            evidence_id=doc.get("id", f"bm25-{idx}"),
            score=round(normalized_score, 4),
            record=None,
            provenance=None,
        ))

    return hits
