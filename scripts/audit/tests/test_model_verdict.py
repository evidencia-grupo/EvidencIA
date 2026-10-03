"""Tests for model verdict calculation and exit codes."""

from audit.model import Check, CheckResult, Priority, Status, Verdict, calculate_verdict


def test_verdict_all_pass():
    checks = {
        "C-01": Check("C-01", "DOM", Priority.P0, "exp", "desc", "docs"),
        "C-02": Check("C-02", "DOM", Priority.P1, "exp", "desc", "docs"),
    }
    results = [
        CheckResult("C-01", Status.PASS, "ok"),
        CheckResult("C-02", Status.PASS, "ok"),
    ]
    summary = calculate_verdict(results, checks)
    assert summary.verdict == Verdict.GO
    assert summary.exit_code == 0
    assert not summary.blockers
    assert not summary.debts


def test_verdict_p0_fail_produces_nogo():
    checks = {
        "C-01": Check("C-01", "DOM", Priority.P0, "exp", "desc", "docs"),
        "C-02": Check("C-02", "DOM", Priority.P1, "exp", "desc", "docs"),
    }
    results = [
        CheckResult("C-01", Status.FAIL, "broken", "details"),
        CheckResult("C-02", Status.PASS, "ok"),
    ]
    summary = calculate_verdict(results, checks)
    assert summary.verdict == Verdict.NO_GO
    assert summary.exit_code == 20
    assert len(summary.blockers) == 1
    assert summary.blockers[0].check_id == "C-01"


def test_verdict_p0_skip_is_fail_closed():
    checks = {
        "C-01": Check("C-01", "DOM", Priority.P0, "exp", "desc", "docs"),
    }
    results = [
        CheckResult("C-01", Status.SKIP, "skipped", "details"),
    ]
    summary = calculate_verdict(results, checks)
    # Fail-closed rule: P0 SKIP must produce NO-GO
    assert summary.verdict == Verdict.NO_GO
    assert summary.exit_code == 20
    assert len(summary.blockers) == 1


def test_verdict_only_p1_p2_fail_produces_go_with_debt():
    checks = {
        "C-01": Check("C-01", "DOM", Priority.P0, "exp", "desc", "docs"),
        "C-02": Check("C-02", "DOM", Priority.P1, "exp", "desc", "docs"),
        "C-03": Check("C-03", "DOM", Priority.P2, "exp", "desc", "docs"),
    }
    results = [
        CheckResult("C-01", Status.PASS, "ok"),
        CheckResult("C-02", Status.FAIL, "minor issue", "details"),
        CheckResult("C-03", Status.WARN, "warning", "details"),
    ]
    summary = calculate_verdict(results, checks)
    assert summary.verdict == Verdict.GO_WITH_DEBT
    assert summary.exit_code == 10
    assert not summary.blockers
    assert len(summary.debts) == 2


def test_immediate_nogo_trigger():
    checks = {
        "ENG-01": Check("ENG-01", "CBL", Priority.P0, "exp", "desc", "docs"),
    }
    results = [
        CheckResult("ENG-01", Status.FAIL, "missing GQs", "details"),
    ]
    summary = calculate_verdict(results, checks)
    assert summary.verdict == Verdict.NO_GO
    assert summary.immediate_nogo_triggered is True
    assert len(summary.immediate_nogo_reasons) == 1
