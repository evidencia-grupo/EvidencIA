"""Guardrail AI-001: o runtime (app/ e ml/) só desserializa modelos em JSON.

Os arquivos `.plk`/`.pkl` versionados são exportações acadêmicas solicitadas
(ver experiments/fakebr/README.md); nenhum código servido pela API pode
carregá-los, pois `pickle.load` executa código arbitrário.
"""

import ast
from pathlib import Path

from app.services.classifier_service import DEFAULT_MODEL_PATH

BACKEND = Path(__file__).resolve().parent.parent
RUNTIME_PACKAGES = ("app", "ml")
UNSAFE_MODULES = {"pickle", "cPickle", "_pickle", "dill", "cloudpickle", "joblib", "shelve", "marshal"}
PICKLE_SUFFIXES = (".pkl", ".plk", ".pickle", ".joblib")


def _runtime_sources():
    for package in RUNTIME_PACKAGES:
        yield from sorted((BACKEND / package).rglob("*.py"))


def test_runtime_never_imports_unsafe_deserializers():
    offenders = []
    for source in _runtime_sources():
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            else:
                continue
            offenders += [f"{source.relative_to(BACKEND)}:{node.lineno} -> {name}" for name in names if name in UNSAFE_MODULES]
    assert offenders == []


def test_runtime_never_references_pickle_artifacts():
    offenders = []
    for source in _runtime_sources():
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.lower().endswith(PICKLE_SUFFIXES):
                offenders.append(f"{source.relative_to(BACKEND)}:{node.lineno} -> {node.value}")
    assert offenders == []


def test_production_classifier_loads_json_model():
    model_path = Path(DEFAULT_MODEL_PATH).resolve()
    assert model_path.name == "model.json"
    assert model_path.is_file()
