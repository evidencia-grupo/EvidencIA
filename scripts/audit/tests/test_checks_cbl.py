"""Tests for CBL checks (ENG, ADR, EDA, REF)."""

import json
from audit import checks_cbl
from audit.model import Status


def test_eng_01_rejects_11_gqs(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    # Write only 11 GQs
    gq_file = docs_dir / "docs" / "visao" / "guiding-questions.md"
    content = gq_file.read_text(encoding="utf-8")
    content = content.replace("GQ12", "NOT_A_GQ")
    gq_file.write_text(content, encoding="utf-8")

    res = checks_cbl.check_eng_01(repo)
    assert res.status == Status.FAIL
    assert "Faltam GQs" in res.found


def test_eda_02_rejects_unexecuted_notebook(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    nb_path = code_dir / "notebooks" / "eda_datasets.ipynb"
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    # Set execution_count to null
    for c in nb["cells"]:
        if c.get("cell_type") == "code":
            c["execution_count"] = None
    nb_path.write_text(json.dumps(nb), encoding="utf-8")

    res = checks_cbl.check_eda_02(repo)
    assert res.status == Status.FAIL
    assert "células não executadas" in res.found


def test_eda_02_rejects_notebook_with_errors(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    nb_path = code_dir / "notebooks" / "eda_datasets.ipynb"
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    # Add an error output
    for c in nb["cells"]:
        if c.get("cell_type") == "code":
            c["outputs"] = [{"output_type": "error", "ename": "NotImplementedError", "evalue": "TODO", "traceback": []}]
            break
    nb_path.write_text(json.dumps(nb), encoding="utf-8")

    res = checks_cbl.check_eda_02(repo)
    assert res.status == Status.FAIL
    assert "saídas com erro" in res.found


def test_ref_03_detects_metric_without_ev_marker(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    ref_file = docs_dir / "docs" / "cbl" / "reflect-share" / "reflection.md"
    # Write a paragraph with 78% without EV marker
    ref_file.write_text("# Reflexão\n\nNossa taxa de acerto foi de 78% nos testes de campo.\n", encoding="utf-8")

    res = checks_cbl.check_ref_03(repo, fase="SCAFFOLD")
    assert res.status == Status.FAIL
    assert "violações de anti-fabricação" in res.found


def test_ref_03_detects_ev_marker_pointing_to_nonexistent_file(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    ref_file = docs_dir / "docs" / "cbl" / "reflect-share" / "reflection.md"
    # Write paragraph with marker pointing to fake non-existent file
    ref_file.write_text("# Reflexão\n\nNossa taxa foi 78% [EV: docs:docs/cbl/act/nao_existe.md#res@1234567].\n", encoding="utf-8")

    res = checks_cbl.check_ref_03(repo, fase="SCAFFOLD")
    assert res.status == Status.FAIL
    assert "arquivo inexistente" in res.details
