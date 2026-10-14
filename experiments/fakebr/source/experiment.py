"""Experimento acadêmico independente: não consulta nem inicializa a aplicação."""
from __future__ import annotations

import hashlib
import json
import pickle
import platform
import random
import re
import subprocess
import time
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, brier_score_loss, classification_report,
                            confusion_matrix, f1_score, log_loss, roc_auc_score)
from sklearn.naive_bayes import MultinomialNB
from threadpoolctl import threadpool_limits

SEED = 42
REVISION = "780f5516c4ae070761632d98ac3368f3ded09d35"
ARCHIVE_SHA256 = "be91c188f621424017bd79a0f33528dcc27f8a6151adb2bcb899c17719eb4090"
DATA_URL = f"https://codeload.github.com/roneysco/Fake.br-Corpus/zip/{REVISION}"
BASE = Path(__file__).resolve().parents[1]


def canonical(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return " ".join(re.findall(r"\w+", text))


def download_data(path):
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error", DATA_URL,
                        "--output", str(path)], check=True)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != ARCHIVE_SHA256:
        raise ValueError("Hash do corpus diferente da revisão avaliada; não prossiga.")
    return path


def load_data(archive):
    rows = []
    missing_metadata = 0
    with zipfile.ZipFile(archive) as z:
        root = z.namelist()[0].rstrip("/")
        for label in ("fake", "true"):
            names = sorted(n for n in z.namelist() if f"/size_normalized_texts/{label}/" in n and n.endswith(".txt"))
            for name in names:
                pair_id = Path(name).stem
                text = z.read(name).decode("utf-8-sig").strip()
                meta_name = f"{root}/full_texts/{label}-meta-information/{pair_id}-meta.txt"
                try:
                    meta = z.read(meta_name).decode("utf-8-sig").splitlines()
                except KeyError:
                    missing_metadata += 1
                    meta = ["", "", "não informado", ""]
                rows.append({"id": f"{label}-{pair_id}", "pair_id": pair_id, "label": label,
                             "text": text, "category": meta[2], "date": meta[3], "url": meta[1],
                             "text_sha256": hashlib.sha256(canonical(text).encode()).hexdigest()})
    # União de pares alinhados e duplicatas textuais, inclusive entre pares.
    parents = {r["pair_id"]: r["pair_id"] for r in rows}
    def find(x):
        while parents[x] != x:
            parents[x] = parents[parents[x]]
            x = parents[x]
        return x
    seen = {}
    labels_by_hash = defaultdict(set)
    for row in rows:
        key = row["text_sha256"]
        labels_by_hash[key].add(row["label"])
        if key in seen:
            left, right = find(row["pair_id"]), find(seen[key])
            parents[max(left, right)] = min(left, right)
        seen[key] = row["pair_id"]
    conflicting = {key for key, labels in labels_by_hash.items() if len(labels) > 1}
    conflicting_groups = {find(r["pair_id"]) for r in rows if r["text_sha256"] in conflicting}
    excluded_groups = conflicting_groups | {find(r["pair_id"]) for r in rows if not r["text"]}
    clean = []
    hashes = set()
    for row in rows:
        row["group"] = find(row["pair_id"])
        if row["group"] in excluded_groups or row["text_sha256"] in hashes:
            continue
        hashes.add(row["text_sha256"])
        clean.append(row)
    audit = {"raw_count": len(rows), "missing_metadata": missing_metadata, "clean_count": len(clean), "excluded_count": len(rows) - len(clean),
             "conflicting_texts": len(conflicting), "groups": len({r['group'] for r in clean}),
             "labels": dict(Counter(r["label"] for r in clean)),
             "categories": dict(Counter(r["category"] for r in clean)),
             "origin": DATA_URL, "revision": REVISION, "archive_sha256": ARCHIVE_SHA256}
    return clean, audit


def split_data(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["group"]].append(row)
    categories = defaultdict(list)
    for group, members in groups.items():
        category = Counter(r["category"] for r in members).most_common(1)[0][0]
        categories[category].append(group)
    assignments = {}
    rng = random.Random(SEED)
    for category in sorted(categories):
        ids = sorted(categories[category])
        rng.shuffle(ids)
        n = len(ids)
        bounds = [int(n * .6), int(n * .75), int(n * .85), n]
        start = 0
        for name, end in zip(("train", "validation", "calibration", "test"), bounds):
            for group in ids[start:end]:
                assignments[group] = name
            start = end
    partitions = {name: [r for r in rows if assignments[r["group"]] == name]
                  for name in ("train", "validation", "calibration", "test")}
    for name, items in partitions.items():
        assert items and {r["label"] for r in items} == {"fake", "true"}, name
    for name, items in partitions.items():
        other = [r for other_name, other_rows in partitions.items() if other_name != name for r in other_rows]
        assert not {r["group"] for r in items} & {r["group"] for r in other}
        assert not {r["text_sha256"] for r in items} & {r["text_sha256"] for r in other}
    return partitions


def lexical_coverage(vectorizer, texts):
    analyzer = vectorizer.build_analyzer()
    vocab = vectorizer.vocabulary_
    values = []
    for text in texts:
        terms = analyzer(text)
        values.append(sum(term in vocab for term in terms) / max(1, len(terms)))
    return np.asarray(values)


def calibrate_scores(estimator, matrix):
    if hasattr(estimator, "decision_function"):
        return np.asarray(estimator.decision_function(matrix)).reshape(-1, 1)
    prob = np.clip(estimator.predict_proba(matrix)[:, 1], 1e-8, 1 - 1e-8)
    return np.log(prob / (1 - prob)).reshape(-1, 1)


def evaluate(y, probabilities, threshold=.6, coverage=None, min_coverage=.15):
    p = np.asarray(probabilities)
    y = np.asarray(y)
    prediction = (p >= .5).astype(int)
    confidence = np.maximum(p, 1 - p)
    accepted = confidence >= threshold
    if coverage is not None:
        accepted &= np.asarray(coverage) >= min_coverage
    correct = prediction == y
    ece = 0.
    for low in np.arange(0, 1, .1):
        members = (confidence >= low) & (confidence < low + .1 + (1e-8 if low > .89 else 0))
        if members.any():
            ece += members.mean() * abs(correct[members].mean() - confidence[members].mean())
    accepted_accuracy = float(correct[accepted].mean()) if accepted.any() else None
    return {"n": len(y), "accuracy": float(accuracy_score(y, prediction)),
            "macro_f1": float(f1_score(y, prediction, average="macro")),
            "roc_auc": float(roc_auc_score(y, p)), "brier": float(brier_score_loss(y, p)),
            "log_loss": float(log_loss(y, np.column_stack([1-p, p]), labels=[0, 1])), "ece_10_bins": float(ece),
            "confusion_matrix": confusion_matrix(y, prediction, labels=[0, 1]).tolist(),
            "classes": classification_report(y, prediction, labels=[0, 1], target_names=["fake", "true"], output_dict=True, zero_division=0),
            "threshold": float(threshold), "accepted_count": int(accepted.sum()),
            "coverage": float(accepted.mean()), "abstention": float(1-accepted.mean()),
            "accepted_accuracy": accepted_accuracy,
            "accepted_error": 1 - accepted_accuracy if accepted_accuracy is not None else None}


def bootstrap_intervals(y, p, groups, threshold, lexical, repeats=1000):
    y, p, groups = np.asarray(y), np.asarray(p), np.asarray(groups)
    unique = np.unique(groups)
    indices = {g: np.flatnonzero(groups == g) for g in unique}
    rng = np.random.default_rng(SEED)
    values = defaultdict(list)
    for _ in range(repeats):
        sample = np.concatenate([indices[g] for g in rng.choice(unique, len(unique), replace=True)])
        result = evaluate(y[sample], p[sample], threshold, lexical[sample])
        for key in ("accuracy", "macro_f1", "coverage", "accepted_accuracy"):
            if result[key] is not None:
                values[key].append(result[key])
    return {key: np.quantile(value, [.025, .975]).tolist() for key, value in values.items()}


def predict_bundle(bundle, texts):
    matrix = bundle["vectorizer"].transform(texts)
    p = bundle["calibrator"].predict_proba(calibrate_scores(bundle["estimator"], matrix))[:, 1]
    coverage = lexical_coverage(bundle["vectorizer"], texts)
    outputs = []
    for text, prob, cov in zip(texts, p, coverage):
        confidence = max(prob, 1-prob)
        reason = "outside_vocabulary" if cov < bundle["min_lexical_coverage"] else "low_confidence" if confidence < bundle["threshold"] else None
        outputs.append({"text": text, "predicted_class": "true" if prob >= .5 else "fake",
                        "label": "abstain" if reason else "true" if prob >= .5 else "fake",
                        "probability_true": float(prob), "confidence": float(confidence),
                        "lexical_coverage": float(cov), "abstention_reason": reason})
    return outputs


def train_and_evaluate(archive, output_dir=BASE):
    start = time.perf_counter()
    output = Path(output_dir)
    for sub in ("models", "results", "figures"):
        (output / sub).mkdir(parents=True, exist_ok=True)
    rows, audit = load_data(download_data(archive))
    split = split_data(rows)
    texts = {name: [r["text"] for r in items] for name, items in split.items()}
    labels = {name: np.array([int(r["label"] == "true") for r in items]) for name, items in split.items()}
    vectorizer = TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2),
                                 min_df=3, max_df=.98, max_features=30000, sublinear_tf=True)
    matrices = {"train": vectorizer.fit_transform(texts["train"])}
    matrices.update({name: vectorizer.transform(data) for name, data in texts.items() if name != "train"})
    print("Partições:", {name: len(items) for name, items in split.items()}, flush=True)
    candidates = {"multinomial_nb_alpha_0.5": MultinomialNB(alpha=.5),
                  "logistic_C_1": LogisticRegression(C=1., solver="liblinear", max_iter=1000, random_state=SEED),
                  "logistic_C_4": LogisticRegression(C=4., solver="liblinear", max_iter=1000, random_state=SEED)}
    selection = []
    with threadpool_limits(limits=1):
        for name, model in candidates.items():
            model.fit(matrices["train"], labels["train"])
            metrics = evaluate(labels["validation"], model.predict_proba(matrices["validation"])[:, 1])
            selection.append({"model": name, "validation_macro_f1": metrics["macro_f1"],
                              "validation_accuracy": metrics["accuracy"], "validation_brier": metrics["brier"]})
            print(selection[-1], flush=True)
        chosen = max(selection, key=lambda row: (row["validation_macro_f1"], -row["validation_brier"]))["model"]
        estimator = candidates[chosen]
        calibrator = LogisticRegression(C=1e6, solver="lbfgs", random_state=SEED, max_iter=1000)
        calibrator.fit(calibrate_scores(estimator, matrices["calibration"]), labels["calibration"])
    p_val = calibrator.predict_proba(calibrate_scores(estimator, matrices["validation"]))[:, 1]
    lexical_val = lexical_coverage(vectorizer, texts["validation"])
    threshold_grid = [evaluate(labels["validation"], p_val, tau, lexical_val) for tau in np.arange(.5, .96, .05)]
    qualifying = [r for r in threshold_grid if r["accepted_count"] >= 50 and r["accepted_accuracy"] >= .9]
    threshold = max(qualifying, key=lambda r: (r["coverage"], r["accepted_accuracy"]))["threshold"] if qualifying else .95
    raw_p = estimator.predict_proba(matrices["test"])[:, 1]
    p_test = calibrator.predict_proba(calibrate_scores(estimator, matrices["test"]))[:, 1]
    lexical_test = lexical_coverage(vectorizer, texts["test"])
    bundle = {"format_version": 1, "vectorizer": vectorizer, "estimator": estimator, "calibrator": calibrator,
              "threshold": float(threshold), "min_lexical_coverage": .15, "model_name": chosen,
              "scope": "academic_news_style_classifier_not_factual_evidence", "corpus_revision": REVISION,
              "seed": SEED, "sklearn_version": sklearn.__version__}
    model_path = output / "models/modelo_treinado.pkl"
    with model_path.open("wb") as f:
        pickle.dump(bundle, f, protocol=5)
    (output / "models/modelo_treinado.plk").write_bytes(model_path.read_bytes())
    with model_path.open("rb") as f:
        restored = pickle.load(f)
    check = predict_bundle(restored, texts["test"])
    assert np.allclose([r["probability_true"] for r in check], p_test, atol=1e-12)
    short_texts = [" ".join(text.split()[:40]) for text in texts["test"]]
    short_p = calibrator.predict_proba(calibrate_scores(estimator, vectorizer.transform(short_texts)))[:, 1]
    result = {"seed": SEED, "dataset": audit,
              "partitions": {name: {"n": len(items), "groups": len({r['group'] for r in items}),
                                    "labels": dict(Counter(r['label'] for r in items))} for name, items in split.items()},
              "selection": selection, "selected_model": chosen, "threshold_selection": threshold_grid,
              "threshold_target_met": bool(qualifying), "selected_threshold": float(threshold),
              "raw_test": evaluate(labels["test"], raw_p, threshold, lexical_test),
              "calibrated_test": evaluate(labels["test"], p_test, threshold, lexical_test),
              "baseline_nb_test": evaluate(labels["test"], candidates['multinomial_nb_alpha_0.5'].predict_proba(matrices['test'])[:, 1], .6, lexical_test),
              "majority_baseline": evaluate(labels["test"], np.full(len(labels['test']), labels['train'].mean()), .5),
              "short_text_stress_test": evaluate(labels["test"], short_p, threshold, lexical_coverage(vectorizer, short_texts)),
              "confidence_intervals_group_bootstrap_95": bootstrap_intervals(labels["test"], p_test, [r['group'] for r in split['test']], threshold, lexical_test),
              "test_threshold_curve": [evaluate(labels['test'], p_test, float(tau), lexical_test) for tau in np.arange(.5, .96, .05)],
              "calibration_parameters": {"coef": calibrator.coef_.tolist(), "intercept": calibrator.intercept_.tolist()},
              "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__, "numpy": np.__version__, "platform": platform.platform()},
              "per_category_test": {cat: evaluate(labels['test'][mask], p_test[mask], threshold, lexical_test[mask])
                  for cat in sorted({r['category'] for r in split['test']})
                  if (mask := np.array([r['category'] == cat for r in split['test']])).sum() and len(set(labels['test'][mask])) == 2},
              "training_and_evaluation_seconds": time.perf_counter()-start}
    (output / 'results/metrics.json').write_text(json.dumps(result, indent=2, ensure_ascii=False))
    manifest = [{k: v for k, v in row.items() if k != 'text'} | {"split": name}
                for name, items in split.items() for row in items]
    (output / 'results/splits.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in manifest))
    predictions = [{"id": row['id'], "group": row['group'], "label": row['label'], "probability_true": float(p), "raw_probability_true": float(raw),
                    "lexical_coverage": float(cov), "correct": int(p >= .5) == int(row['label'] == 'true')}
                   for row, p, raw, cov in zip(split['test'], p_test, raw_p, lexical_test)]
    (output / 'results/test_predictions.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in predictions))
    print("Resultado teste:", result['calibrated_test'], flush=True)
    return bundle, result, split


def plot_results(result, output_dir=BASE):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, ax = plt.subplots(figsize=(5.6, 4.1), layout="constrained")
    matrix = np.array(result['calibrated_test']['confusion_matrix'])
    ax.imshow(matrix, cmap="Blues")
    for (i, j), value in np.ndenumerate(matrix):
        ax.text(j, i, str(value), ha='center', va='center', color='white' if value > matrix.max()/2 else '#162c43', fontsize=16)
    ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=['fake', 'true'], yticklabels=['fake', 'true'], xlabel='Classe prevista', ylabel='Rótulo do corpus', title=f"Teste independente: n={matrix.sum()}")
    fig.savefig(Path(output_dir)/'figures/confusao.png', dpi=170)
    plt.close(fig)
    curve = result['test_threshold_curve']
    fig, ax = plt.subplots(figsize=(7, 3.8), layout='constrained')
    ax.plot([r['threshold'] for r in curve], [100*r['coverage'] for r in curve], 'o-', label='Cobertura', color='#087f8c')
    ax.plot([r['threshold'] for r in curve], [100*r['accepted_accuracy'] if r['accepted_accuracy'] is not None else np.nan for r in curve], 's-', label='Acurácia entre aceitas', color='#af5900')
    ax.axvline(result['selected_threshold'], color='#455568', ls='--', label='Limiar escolhido na validação')
    ax.set(xlabel='Limiar de abstenção', ylabel='Percentual (%)', ylim=(0, 102), title='Cobertura e erros: teste sem ajuste de limiar')
    ax.grid(alpha=.15); ax.legend(fontsize=8, loc='lower left')
    fig.savefig(Path(output_dir)/'figures/abstencao.png', dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, default=BASE/'cache/fakebr.zip')
    args = parser.parse_args()
    bundle, metrics, _ = train_and_evaluate(args.archive)
    plot_results(metrics)
