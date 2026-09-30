"""
Módulo de Download e Curadoria de Datasets Brasileiros para Fact-Checking — EvidencIA

Prioridade Absoluta: Datasets em Português Brasileiro (PT-BR)
1. FactChecks.br (fake-news-UFG/FactChecksbr) - Padrão Ouro de checagens da Lupa, Aos Fatos e Boatos.org
2. Fake.br Corpus (NILC - USP São Carlos / fake-news-UFG/fakebr) - Notícias alinhadas e balanceadas
3. ClaimPT - Detecção de alegações checáveis (Check-worthiness)
"""

import argparse
import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Diretório padrão para dados locais processados
DEFAULT_SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "sample_facts.json")


def load_local_sample_dataset(file_path: Optional[str] = None) -> List[Dict]:
    """
    Carrega o dataset local curado em PT-BR (sample_facts.json) que acompanha o repositório.
    Garante que os testes e a API possam funcionar offline sem dependência de download de rede.
    """
    target = file_path or DEFAULT_SAMPLE_PATH
    if not os.path.exists(target):
        logger.warning(f"Arquivo de amostra não encontrado em {target}")
        return []

    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)


def download_dataset_from_hub(dataset_name: str, limit: int = 100) -> List[Dict]:
    """
    Baixa datasets brasileiros diretamente do Hugging Face Hub utilizando a biblioteca `datasets`.
    Requer internet e dependências instaladas (`pip install datasets`).
    """
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        raise ImportError(
            "A biblioteca 'datasets' é necessária para download completo. "
            "Instale via: pip install datasets"
        )

    normalized_data: List[Dict] = []

    if dataset_name == "factchecksbr":
        logger.info("Baixando dataset brasileiro FactChecks.br (UFG / Agências IFCN)...")
        ds = load_dataset("fake-news-UFG/FactChecksbr", split="train")
        for i, row in enumerate(ds):
            if i >= limit:
                break
            normalized_data.append({
                "claim": row.get("claim") or row.get("title") or "",
                "status": row.get("label") or row.get("rating") or "inconclusiva",
                "publisher": row.get("source") or "Agência Brasileira",
                "evidence_summary": row.get("explanation") or row.get("body") or "",
            })

    elif dataset_name == "fakebr":
        logger.info("Baixando dataset Fake.br Corpus (NILC - USP São Carlos)...")
        ds = load_dataset("fake-news-UFG/fakebr", split="train")
        for i, row in enumerate(ds):
            if i >= limit:
                break
            is_fake = row.get("label") in [1, "fake", "1"]
            normalized_data.append({
                "claim": row.get("text", "")[:300],
                "status": "contraditada" if is_fake else "apoiada",
                "publisher": "NILC / USP São Carlos",
                "evidence_summary": f"Corpus Fake.br: Rotulado formalmente como {'falso' if is_fake else 'verdadeiro'}.",
            })

    else:
        raise ValueError(f"Dataset '{dataset_name}' não suportado. Opções: factchecksbr, fakebr")

    return normalized_data


def main():
    parser = argparse.ArgumentParser(description="Downloader e Extrator de Datasets Brasileiros de Fact-Checking")
    parser.add_argument(
        "--dataset",
        choices=["factchecksbr", "fakebr", "sample"],
        default="sample",
        help="Dataset a processar (padrão: sample para uso offline)",
    )
    parser.add_argument("--limit", type=int, default=50, help="Limite de exemplos a baixar do Hub")
    args = parser.parse_args()

    if args.dataset == "sample":
        data = load_local_sample_dataset()
        print(f"✅ Amostra local brasileira carregada com sucesso: {len(data)} checagens registradas.")
        for item in data[:3]:
            print(f" - [{item['status'].upper()}] {item['claim']} ({item['publisher']})")
    else:
        data = download_dataset_from_hub(args.dataset, limit=args.limit)
        print(f"✅ {len(data)} exemplos baixados com sucesso do dataset brasileiro '{args.dataset}'.")


if __name__ == "__main__":
    main()
