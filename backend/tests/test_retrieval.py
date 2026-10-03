"""Testes de contrato e funcionalidade de retrieval (busca e indexação).

Garantias testadas:
- Contrato da função search e formato de SearchHit.
- Busca textual com fallback de BM25/TF-IDF em memória (offline, sem dependência obrigatória de Chroma).
- Filtro temporal opcional.
- Suporte a Chroma via pytest.importorskip("chromadb").

Refs: ADR-001, IS-06, IS-08.
"""

import pytest
from ml.retrieval.search import search, SearchHit


def test_search_hit_structure():
    """Garante que SearchHit possui os campos e tipos exigidos pela arquitetura."""
    hit = SearchHit(
        evidence_id="factchecksbr:sample:001",
        score=0.95,
        record=None,
        provenance=None,
    )
    assert hit.evidence_id == "factchecksbr:sample:001"
    assert hit.score == 0.95
    assert hasattr(hit, "record")
    assert hasattr(hit, "provenance")


def test_search_bm25_fallback_contract():
    """Testa busca usando o corpus em memória com o algoritmo BM25 (ou fallback equivalente)."""
    # Corpus sintético de teste
    test_corpus = [
        {"id": "doc-01", "text": "A vacina contra dengue é eficaz e segura comprovada pela Anvisa.", "published_at": "2024-05-10"},
        {"id": "doc-02", "text": "O desemprego caiu no último trimestre segundo dados do IBGE.", "published_at": "2024-06-15"},
        {"id": "doc-03", "text": "Consumo de açúcar em excesso está associado a diabetes tipo 2.", "published_at": "2023-01-20"},
    ]

    try:
        results = search(
            query="vacina dengue eficaz",
            k=2,
            corpus=test_corpus,
            use_bm25_fallback=True,
        )
        assert len(results) > 0
        assert isinstance(results[0], SearchHit)
        # O documento mais relevante para a query sobre vacina deve ser o doc-01
        assert results[0].evidence_id == "doc-01"
        assert 0.0 <= results[0].score <= 1.0
    except ImportError:
        # Se rank-bm25 não estiver instalado, a interface ainda deve ser invocável e retornar SearchHit
        pytest.skip("rank-bm25 não disponível no ambiente")


def test_search_temporal_filter():
    """Testa aplicação de filtro temporal."""
    test_corpus = [
        {"id": "doc-antigo", "text": "Relatório econômico sobre inflação", "published_at": "2022-01-01"},
        {"id": "doc-novo", "text": "Relatório econômico sobre inflação recente", "published_at": "2025-01-01"},
    ]

    try:
        results = search(
            query="relatório inflação",
            k=5,
            filters={"after": "2024-01-01"},
            corpus=test_corpus,
            use_bm25_fallback=True,
        )
        # Não deve retornar o documento de 2022
        returned_ids = [r.evidence_id for r in results]
        assert "doc-antigo" not in returned_ids
        if returned_ids:
            assert "doc-novo" in returned_ids
    except ImportError:
        pytest.skip("rank-bm25 não disponível no ambiente")


def test_chroma_retrieval_if_available():
    """Testa integração com Chroma somente quando chromadb e sentence_transformers estiverem instalados."""
    pytest.importorskip("chromadb")
    pytest.importorskip("sentence_transformers")

    # Se ambas as bibliotecas estiverem disponíveis, valida inicialização do encoder
    from ml.embeddings.encoder import default_encoder
    assert default_encoder.model_name is not None
