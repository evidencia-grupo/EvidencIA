"""Tests for Scrum and Traceability checks (SCR, TRC, GOV)."""

from audit import checks_scrum_trace
from audit.model import Status


def test_scr_01_core_artifacts(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_scrum_trace.check_scr_01(repo)
    assert res.status == Status.PASS

    (docs_dir / "docs" / "scrum" / "definition-of-done.md").unlink()
    res = checks_scrum_trace.check_scr_01(repo)
    assert res.status == Status.FAIL
    assert "definition-of-done.md" in res.found


def test_scr_02_four_files_per_sprint(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_scrum_trace.check_scr_02(repo)
    assert res.status == Status.PASS

    # Remove sprint-02/retrospective.md
    (docs_dir / "docs" / "scrum" / "sprint-02" / "retrospective.md").unlink()
    res = checks_scrum_trace.check_scr_02(repo)
    assert res.status == Status.FAIL
    assert "sprint-02/retrospective.md" in res.found


def test_scr_03_unfilled_ceremonies(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_scrum_trace.check_scr_03(repo)
    assert res.status == Status.PASS

    # Insert "A preencher" in sprint-02 review
    review_file = docs_dir / "docs" / "scrum" / "sprint-02" / "review.md"
    review_file.write_text("# Review\nStatus: A preencher", encoding="utf-8")
    res = checks_scrum_trace.check_scr_03(repo)
    assert res.status == Status.FAIL
    assert "Cerimônias não encerradas" in res.found


def test_scr_04_mandatory_questions(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_scrum_trace.check_scr_04(repo)
    assert res.status == Status.PASS

    # Remove mandatory question 6 from sprint-01 review
    review_file = docs_dir / "docs" / "scrum" / "sprint-01" / "review.md"
    content = review_file.read_text(encoding="utf-8")
    content = content.replace("Que decisão mudou", "Outro tópico")
    review_file.write_text(content, encoding="utf-8")
    res = checks_scrum_trace.check_scr_04(repo)
    assert res.status == Status.FAIL
    assert "Perguntas obrigatórias não respondidas" in res.found


def test_trc_01_hu11_mvp_and_traceability_chain(make_repos):
    docs_dir, code_dir, repo = make_repos(full_passing=True)
    res = checks_scrum_trace.check_trc_01(repo)
    assert res.status == Status.PASS

    # Mark HU11 as Pós-MVP
    cat_file = docs_dir / "docs" / "requisitos" / "catalogo-requisitos.md"
    cat_file.write_text("# Requisitos\nHU11: Pós-MVP\nHU13\nHU14\nHU15\nHU16", encoding="utf-8")
    res = checks_scrum_trace.check_trc_01(repo)
    assert res.status == Status.FAIL
    assert "HU11 ainda marcada como Pós-MVP" in res.found

    # Reset HU11 and break matrix (remove ADR link)
    cat_file.write_text("# Requisitos\nHU11: Must Have MVP\nHU13\nHU14\nHU15\nHU16", encoding="utf-8")
    matrix_file = docs_dir / "docs" / "requisitos" / "matriz-rastreabilidade.md"
    matrix_file.write_text("# Matriz desconectada sem referencias", encoding="utf-8")
    res = checks_scrum_trace.check_trc_01(repo)
    assert res.status == Status.FAIL
    assert "Matriz de rastreabilidade não conecta" in res.found
