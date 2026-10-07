#!/usr/bin/env python3
"""Script de avaliação de Retrieval e Stance do EvidencIA.

Calcula métricas de IR (Recall@5, Recall@10, MRR, nDCG@5) e taxas de erro
(False Match Rate, Insufficient Evidence Rate) a partir de anotações humanas
independentes em candidates.jsonl.
Se as anotações ainda não foram feitas, reporta PENDING_HUMAN_ANNOTATION
sem fabricar métricas artificiais.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avaliação de Retrieval e Stance")
    parser.add_argument("--claims", type=str, default="evaluation/claims.jsonl", help="Caminho para claims.jsonl")
    parser.add_argument("--candidates", type=str, default="evaluation/candidates.jsonl", help="Caminho para candidates.jsonl")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict]:
    records = []
    if not path.exists():
        print(f"Erro: Arquivo não encontrado: {path}", file=sys.stderr)
        sys.exit(1)
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def main() -> None:
    args = parse_args()
    claims_path = Path(args.claims)
    candidates_path = Path(args.candidates)

    claims = load_jsonl(claims_path)
    candidates = load_jsonl(candidates_path)

    print(f"==================================================")
    print(f"EvidencIA — Avaliação Empírica de Recuperação")
    print(f"==================================================")
    print(f"Total de Alegações carregadas: {len(claims)}")
    print(f"Total de Pares Candidatos avaliados: {len(candidates)}")

    annotated = [c for c in candidates if c.get("human_relevance") is not None]

    if not annotated:
        print("\nStatus: PENDING_HUMAN_ANNOTATION (Bloqueio H3 isolado)")
        print("Nenhuma linha em 'candidates.jsonl' possui anotação humana consolidada.")
        print("Em estrita observância ao princípio de não-circularidade científica,")
        print("métricas automáticas de IR e Stance NÃO são fabricadas.")
        print("Consulte 'evaluation/annotation-guide.md' para o protocolo de rotulação humana.")
        sys.exit(0)

    # Cálculo real para quando anotado por humanos
    print(f"\nAmostras anotadas por humanos: {len(annotated)}")
    by_claim: dict[str, list[dict]] = {}
    for c in annotated:
        cid = c["claim_id"]
        by_claim.setdefault(cid, []).append(c)

    reciprocal_ranks = []
    recall_at_5 = []
    recall_at_10 = []
    ndcg_at_5 = []
    false_matches = 0
    insufficient_evidence_count = 0

    for cid, pairs in by_claim.items():
        sorted_pairs = sorted(pairs, key=lambda x: x.get("rank", 999))
        relevant_ranks = [p["rank"] for p in sorted_pairs if p.get("human_relevance", 0) >= 1]

        if not relevant_ranks:
            insufficient_evidence_count += 1
            reciprocal_ranks.append(0.0)
            recall_at_5.append(0.0)
            recall_at_10.append(0.0)
            ndcg_at_5.append(0.0)
        else:
            first_rank = relevant_ranks[0]
            reciprocal_ranks.append(1.0 / first_rank)
            recall_at_5.append(1.0 if any(r <= 5 for r in relevant_ranks) else 0.0)
            recall_at_10.append(1.0 if any(r <= 10 for r in relevant_ranks) else 0.0)

            # Cálculo de nDCG@5
            dcg = 0.0
            idcg = 0.0
            ideal_rels = sorted([p.get("human_relevance", 0) for p in sorted_pairs], reverse=True)[:5]
            for i, rel in enumerate(ideal_rels):
                idcg += (2**rel - 1) / math.log2(i + 2)
            for i, p in enumerate(sorted_pairs[:5]):
                rel = p.get("human_relevance", 0)
                dcg += (2**rel - 1) / math.log2(i + 2)
            ndcg_at_5.append(dcg / idcg if idcg > 0 else 0.0)

        # False Match Rate: predição 'supports' ou 'contradicts' com relevância 0 ou divergência de postura
        for p in sorted_pairs:
            m_rel = p.get("model_relation")
            h_rel = p.get("human_relevance", 0)
            h_stance = p.get("human_stance")
            if m_rel in ("supports", "contradicts"):
                if h_rel == 0 or (h_stance and h_stance != m_rel):
                    false_matches += 1

    total_queries = max(len(by_claim), 1)
    mrr = sum(reciprocal_ranks) / total_queries
    r5 = sum(recall_at_5) / total_queries
    r10 = sum(recall_at_10) / total_queries
    ndcg5 = sum(ndcg_at_5) / total_queries
    fmr = false_matches / max(len(annotated), 1)
    ier = insufficient_evidence_count / total_queries

    print(f"\nMétricas de IR & Stance Consolidadas:")
    print(f"  Recall@5:                   {r5:.4f}")
    print(f"  Recall@10:                  {r10:.4f}")
    print(f"  MRR:                        {mrr:.4f}")
    print(f"  nDCG@5:                     {ndcg5:.4f}")
    print(f"  False Match Rate:           {fmr:.4f}")
    print(f"  Insufficient Evidence Rate: {ier:.4f}")


if __name__ == "__main__":
    main()
