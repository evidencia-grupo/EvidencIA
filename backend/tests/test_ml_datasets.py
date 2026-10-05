from ml.datasets.dataset_downloader import load_local_sample_dataset
from app.services.brazilian_fact_matcher import brazilian_fact_matcher


def test_brazilian_sample_dataset_integrity():
    """Valida a integridade do dataset de amostra de checagens brasileiras (FactChecks.br)."""
    dataset = load_local_sample_dataset()
    assert len(dataset) >= 10, "O dataset de amostra brasileiro deve conter ao menos 10 checagens reais"

    for item in dataset:
        assert "id" in item
        assert "claim" in item and len(item["claim"]) > 10
        assert item["status"] in ["apoiada", "contraditada", "inconclusiva"]
        assert "publisher" in item and len(item["publisher"]) > 0
        assert "evidence_summary" in item and len(item["evidence_summary"]) > 15
        assert "review_url" in item and item["review_url"].startswith("http")


def test_brazilian_fact_matcher_direct_match():
    """Valida casamento com checagens conhecidas de agências brasileiras (Agência Lupa, Aos Fatos)."""
    # Exemplo emblemático de boato de saúde no Brasil
    query = "O chá de casca de banana cura diabetes e zera glicose"
    match = brazilian_fact_matcher.find_match(query)

    assert match is not None
    assert match["status"] == "contraditada"
    assert "Agência Lupa" in match["evidence"].title
    assert "lupa.uol.com.br" in match["evidence"].url
    assert match["confidence"] >= 0.85


def test_brazilian_fact_matcher_no_false_positive():
    """Garante que frases sem correlação não sofrem falso positivo."""
    query = "Um filme interessante sobre astronautas viajando no espaço sideral"
    match = brazilian_fact_matcher.find_match(query, threshold=0.6)
    assert match is None


def test_brazilian_fact_matcher_evidencia_rastreavel_hu14():
    """HU14: a evidência traz trecho, publisher, endereço e proveniência, sem inventar data de publicação."""
    match = brazilian_fact_matcher.find_match("O chá de casca de banana cura diabetes e zera glicose")

    evidence = match["evidence"]
    assert evidence.relation == "contradicts"
    assert evidence.publisher == "Agência Lupa"
    assert evidence.url.startswith("https://")
    assert evidence.snippet
    assert evidence.provenance.dataset == "factchecksbr"
    assert evidence.publishedAt == ""
