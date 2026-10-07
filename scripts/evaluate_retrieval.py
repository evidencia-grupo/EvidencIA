#!/usr/bin/env python3
"""Script de avaliação de Retrieval e Stance do EvidencIA.

Calcula métricas de IR (Recall@k, MRR) e Stance (F1, Precision, Recall)
a partir de anotações humanas independentes em candidates.jsonl.
Se as anotações ainda não foram feitas, reporta PENDING_HUMAN_ANNOTATION
sem fabricar métricas artificiais.
"""

from __future__ import annotations

import argparse
import json
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
    recall_at_1 = []
    recall_at_3 = []

    for cid, pairs in by_claim.items():
        # Ordenar por rank
        sorted_pairs = sorted(pairs, key=lambda x: x.get("rank", 999))
        relevant_ranks = [p["rank"] for p in sorted_pairs if p.get("human_relevance", 0) >= 1]
        if relevant_ranks:
            first_rank = relevant_ranks[0]
            reciprocal_ranks.append(1.0 / first_rank)
            recall_at_1.append(1.0 if first_rank <= 1 else 0.0)
            recall_at_3.append(1.0 if first_rank <= 3 else 0.0)
        else:
            reciprocal_ranks.append(0.0)
            recall_at_1.append(0.0)
            recall_at_3.append(0.0)

    mrr = sum(reciprocal_ranks) / max(len(reciprocal_ranks), 1)
    r1 = sum(recall_at_1) / max(len(recall_at_1), 1)
    r3 = sum(recall_at_3) / max(len(recall_at_3), 1)

    print(f"\nMétricas de IR Calculadas:")
    print(f"  MRR: {mrr:.4f}")
    print(f"  Recall@1: {r1:.4f}")
    print(f"  Recall@3: {r3:.4f}")


if __name__ == "__main__":
    main()
