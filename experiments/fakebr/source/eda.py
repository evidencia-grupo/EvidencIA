"""Análise exploratória (EDA) do Fake.br e do corpus local do produto.

Usa o mesmo carregamento e deduplicação do experimento (load_data), então descreve exatamente os
7.199 documentos avaliados. O corpus não é republicado: os textos são lidos do zip oficial
(revisão fixada, SHA-256 conferido) e só estatísticas agregadas são gravadas.

Uso, nesta pasta:  python -m source.eda --archive /caminho/fakebr.zip
Saídas: results/eda_summary.json e figures/eda_*.png
"""
import argparse
import csv
import json
import math
import re
import statistics
import zipfile
from collections import Counter, defaultdict
from urllib.parse import urlparse

from source.experiment import BASE, canonical, download_data, load_data

LOCAL_CORPUS = BASE.parents[1] / "backend/ml/datasets/training_local.csv"
STOPWORDS = set("""a o e é de do da dos das em no na nos nas um uma uns umas que se por para com como
mais mas ao aos à às ou ser foi são está estão ter tem há pelo pela pelos pelas sua seu suas seus
ele ela eles elas isso esse essa este esta não sim já também muito só quando onde sobre entre após
até sem nem lhe nos me te você vocês ainda depois antes porque pois então foram era eram será sido
https www com br""".split())


def quantiles(values):
    ordered = sorted(values)

    def pick(q):
        return ordered[min(len(ordered) - 1, int(q * len(ordered)))]

    return {"mean": round(statistics.fmean(ordered), 1), "median": statistics.median(ordered),
            "p10": pick(.10), "p90": pick(.90), "min": ordered[0], "max": ordered[-1]}


def words(text):
    return re.findall(r"\w+", text, flags=re.UNICODE)


def full_text_lengths(archive, rows):
    """Tamanho das versões integrais, para mostrar o viés removido pela normalização."""
    lengths = defaultdict(list)
    with zipfile.ZipFile(archive) as z:
        root = z.namelist()[0].rstrip("/")
        names = set(z.namelist())
        for row in rows:
            name = f"{root}/full_texts/{row['label']}/{row['pair_id']}.txt"
            if name in names:
                lengths[row["label"]].append(len(words(z.read(name).decode("utf-8-sig"))))
    return lengths


def stylistic_markers(rows):
    per_label = defaultdict(lambda: Counter())
    for row in rows:
        text = row["text"]
        tokens = words(text)
        c = per_label[row["label"]]
        c["words"] += len(tokens)
        c["exclamations"] += text.count("!")
        c["questions"] += text.count("?")
        c["uppercase_words"] += sum(1 for t in tokens if len(t) > 2 and t.isupper())
        c["digits"] += sum(1 for t in tokens if t.isdigit())
        c["quotes"] += text.count('"') + text.count("“") + text.count("”")
    return {label: {k: round(1000 * v / c["words"], 2) for k, v in c.items() if k != "words"}
            for label, c in per_label.items()}


def distinctive_terms(rows, top=15):
    """Log-odds com prior de Dirichlet informativo (Monroe et al., 2008)."""
    counts = {"fake": Counter(), "true": Counter()}
    for row in rows:
        counts[row["label"]].update(t for t in canonical(row["text"]).split()
                                    if t not in STOPWORDS and len(t) > 2 and not t.isdigit())
    prior = counts["fake"] + counts["true"]
    a0 = sum(prior.values())
    n = {k: sum(v.values()) for k, v in counts.items()}
    scores = {}
    for term, alpha in prior.items():
        if alpha < 20:
            continue
        yf, yt = counts["fake"][term], counts["true"][term]
        lf = math.log((yf + alpha) / (n["fake"] + a0 - yf - alpha))
        lt = math.log((yt + alpha) / (n["true"] + a0 - yt - alpha))
        var = 1 / (yf + alpha) + 1 / (yt + alpha)
        scores[term] = (lf - lt) / math.sqrt(var)
    ranked = sorted(scores.items(), key=lambda kv: kv[1])

    def fmt(items):
        return [{"term": t, "z": round(z, 2)} for t, z in items]

    return {"fake": fmt(ranked[::-1][:top]), "true": fmt(ranked[:top])}


def domain(url):
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else (host or "não informado")


def year(date):
    match = re.search(r"(19|20)\d{2}", date or "")
    return match.group(0) if match else "não informado"


def local_corpus_summary():
    rows = list(csv.DictReader(LOCAL_CORPUS.open(encoding="utf-8")))
    return {"rows": len(rows), "labels": dict(Counter(r["label"] for r in rows)),
            "splits": dict(Counter(r["split"] for r in rows)),
            "categories": dict(Counter(r["category"] for r in rows).most_common()),
            "source_declared": dict(Counter(r["source_declared"] for r in rows).most_common()),
            "provenance_status": dict(Counter(r["provenance_status"] for r in rows)),
            "words": quantiles([len(words(r["text"])) for r in rows]),
            "duplicated_texts": len(rows) - len({canonical(r["text"]) for r in rows})}


def plot(summary, out):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = ("fake", "true")
    colors = {"fake": "#C62828", "true": "#2E7D32"}

    cats = sorted(summary["category_by_label"], key=lambda c: -sum(summary["category_by_label"][c].values()))
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for i, label in enumerate(labels):
        ax.bar([x + i * .4 for x in range(len(cats))], [summary["category_by_label"][c].get(label, 0) for c in cats],
               width=.4, label=label, color=colors[label])
    ax.set_xticks([x + .2 for x in range(len(cats))], cats, rotation=20, ha="right")
    ax.set_ylabel("documentos")
    ax.set_title("Fake.br: documentos por categoria e rótulo")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "eda_categorias.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), sharey=True)
    for ax, key, title in ((axes[0], "full_text_words", "Textos integrais"),
                           (axes[1], "normalized_words", "Textos normalizados (usados no modelo)")):
        data = [summary["_lengths"][key][label] for label in labels]
        ax.boxplot(data, tick_labels=labels, showfliers=False)
        ax.set_title(title)
        ax.set_ylabel("palavras")
    fig.suptitle("Tamanho dos textos por rótulo")
    fig.tight_layout()
    fig.savefig(out / "eda_tamanho.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, label in zip(axes, labels):
        items = summary["top_domains"][label][:8]
        ax.barh([d["domain"] for d in items][::-1], [d["count"] for d in items][::-1], color=colors[label])
        ax.set_title(f"Domínios de origem — {label}")
        ax.set_xlabel("documentos")
    fig.tight_layout()
    fig.savefig(out / "eda_dominios.png", dpi=150)
    plt.close(fig)

    markers = list(summary["stylistic_markers_per_1000_words"]["fake"])
    fig, ax = plt.subplots(figsize=(8, 3.2))
    for i, label in enumerate(labels):
        ax.bar([x + i * .4 for x in range(len(markers))],
               [summary["stylistic_markers_per_1000_words"][label][m] for m in markers], width=.4, label=label, color=colors[label])
    ax.set_xticks([x + .2 for x in range(len(markers))], markers)
    ax.set_ylabel("por 1.000 palavras")
    ax.set_title("Marcadores estilísticos por rótulo")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "eda_estilo.png", dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", default=str(BASE / "data/fakebr.zip"))
    args = parser.parse_args()
    archive = download_data(args.archive)
    rows, audit = load_data(archive)
    splits = {json.loads(line)["id"]: json.loads(line)["split"] for line in (BASE / "results/splits.jsonl").read_text().splitlines()}

    normalized = defaultdict(list)
    for row in rows:
        normalized[row["label"]].append(len(words(row["text"])))
    full = full_text_lengths(archive, rows)
    cat_label = defaultdict(Counter)
    split_label = defaultdict(Counter)
    domains = defaultdict(Counter)
    years = defaultdict(Counter)
    for row in rows:
        cat_label[row["category"]][row["label"]] += 1
        split_label[splits[row["id"]]][row["label"]] += 1
        domains[row["label"]][domain(row["url"])] += 1
        years[row["label"]][year(row["date"])] += 1
    shared_domains = set(domains["fake"]) & set(domains["true"]) - {"não informado"}

    summary = {
        "source": {k: audit[k] for k in ("origin", "revision", "archive_sha256")},
        "audit": {k: audit[k] for k in ("raw_count", "clean_count", "excluded_count", "conflicting_texts", "missing_metadata", "groups")},
        "labels": audit["labels"],
        "category_by_label": {c: dict(v) for c, v in sorted(cat_label.items(), key=lambda kv: -sum(kv[1].values()))},
        "split_by_label": {s: dict(split_label[s]) for s in ("train", "validation", "calibration", "test")},
        "length_words": {"normalized": {label: quantiles(v) for label, v in normalized.items()},
                         "full_text": {label: quantiles(v) for label, v in full.items()}},
        "vocabulary": {label: len({t for r in rows if r["label"] == label for t in canonical(r["text"]).split()}) for label in ("fake", "true")},
        "top_domains": {label: [{"domain": d, "count": n} for d, n in domains[label].most_common(10)] for label in ("fake", "true")},
        "distinct_domains": {label: len(domains[label]) for label in ("fake", "true")},
        "domains_shared_between_labels": sorted(shared_domains),
        "years": {label: dict(sorted(years[label].items())) for label in ("fake", "true")},
        "stylistic_markers_per_1000_words": stylistic_markers(rows),
        "distinctive_terms": distinctive_terms(rows),
        "local_corpus": local_corpus_summary(),
        "_lengths": {"normalized_words": normalized, "full_text_words": full},
    }
    (BASE / "figures").mkdir(exist_ok=True)
    plot(summary, BASE / "figures")
    del summary["_lengths"]
    (BASE / "results/eda_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: summary[k] for k in ("audit", "labels", "length_words", "distinct_domains")}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
