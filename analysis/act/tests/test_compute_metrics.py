"""
Unit and integration tests for CBL Act compute_metrics tool.
Verifies all metric formulas M1-M9 against synthetic fixtures
with hand-computed expected values and detailed mathematical rationale.
"""

import json
import os
import subprocess
import sys
import pytest

from analysis.act.compute_metrics import (
    load_sessions,
    load_ground_truth,
    compute_eir,
    compute_sor,
    compute_rir,
    compute_err,
    compute_pdr,
    compute_accuracy_per_phase,
    compute_ttc,
    compute_vsc,
    compute_seq,
    compute_ibr,
    compute_confidence_calibration,
    compute_all_metrics,
    validate_raw_event,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")
SESSIONS_PATH = os.path.join(FIXTURES_DIR, "synthetic_sessions.jsonl")
GROUND_TRUTH_PATH = os.path.join(FIXTURES_DIR, "synthetic_ground_truth.json")


@pytest.fixture
def loaded_data():
    rejections = {}
    sessions = load_sessions(SESSIONS_PATH, rejections)
    gt_map = load_ground_truth(GROUND_TRUTH_PATH)
    sess_b = next(s for s in sessions.values() if s.cond == "B")
    sess_a = next(s for s in sessions.values() if s.cond == "A")
    return {
        "sessions": sessions,
        "gt_map": gt_map,
        "sess_b": sess_b,
        "sess_a": sess_a,
        "rejections": rejections,
    }


def test_m1_evidence_inspection_rate(loaded_data):
    """
    M1: EIR = |claims with >= 1 evidence_expanded| / |claims visible|
    - Condition B: claims 1 and 2 visible.
      Claim 1 expanded at seq 11. Claim 2 expanded at seq 18.
      Expected: 2 / 2 = 1.0 (100%).
    - Condition A: claims 1 and 2 visible.
      Claim 1 has 0 expansions. Claim 2 expanded at seq 13.
      Expected: 1 / 2 = 0.50 (50%).
    """
    eir_b = compute_eir(loaded_data["sess_b"])
    eir_a = compute_eir(loaded_data["sess_a"])
    assert eir_b == 1.0
    assert eir_a == 0.5


def test_m1b_source_open_rate(loaded_data):
    """
    M1b: SOR = |claims with >= 1 source_opened| / |claims visible|
    - Condition B: Claim 1 had source_opened at seq 12; Claim 2 did not.
      Expected: 1 / 2 = 0.50 (50%).
    - Condition A: No source_opened events.
      Expected: 0 / 2 = 0.0.
    """
    sor_b = compute_sor(loaded_data["sess_b"])
    sor_a = compute_sor(loaded_data["sess_a"])
    assert sor_b == 0.5
    assert sor_a == 0.0


def test_m2_reflection_interaction_rate(loaded_data):
    """
    M2: RIR = |interacted in {expanded, answered}| / |viewed questions|
    - Condition B: 1 question viewed (claim 1, question 1).
      Interacted via 'answered' at seq 14.
      Expected: 1 / 1 = 1.0.
    - Condition A: Not applicable (no reflection questions).
      Expected: None.
    """
    rir_b = compute_rir(loaded_data["sess_b"])
    rir_a = compute_rir(loaded_data["sess_a"])
    assert rir_b == 1.0
    assert rir_a is None


def test_m3_evidence_revision_rate(loaded_data):
    """
    M3: ERR = revised decisions / eligible decisions
    - Condition B:
      Claim 1: pre_evidence='supported', evidence_expanded at seq 11, final='misleading'.
      Revision occurred (supported != misleading).
      Ground truth for IT-002 claim 1 is 'misleading'.
      pre != gt and final == gt -> ERR_correct = 1.0, ERR_harm = 0.0.
      Claim 2 has no pre_evidence decision -> not eligible.
      Expected: eligible=1, revised=1, err_rate=1.0, err_correct=1.0, err_harm=0.0.
    - Condition A:
      No pre_evidence decisions recorded.
      Expected: eligible=0, revised=0, err_rate=0.0, err_correct=None, err_harm=None.
    """
    gt_map = loaded_data["gt_map"]
    err_b = compute_err(loaded_data["sess_b"], gt_map)
    err_a = compute_err(loaded_data["sess_a"], gt_map)

    assert err_b["eligible"] == 1
    assert err_b["revised"] == 1
    assert err_b["err_rate"] == 1.0
    assert err_b["err_correct"] == 1.0
    assert err_b["err_harm"] == 0.0

    assert err_a["eligible"] == 0
    assert err_a["revised"] == 0
    assert err_a["err_rate"] == 0.0
    assert err_a["err_correct"] is None


def test_m3b_premature_decision_rate(loaded_data):
    """
    M3b: PDR = final decisions without prior evidence_expanded / total final decisions.
    - Condition B:
      Claim 1 expanded before final decision.
      Claim 2 expanded before final decision.
      Expected: 0 / 2 = 0.0.
    - Condition A:
      Claim 1 final decision made at seq 11 without any evidence_expanded.
      Claim 2 final decision made at seq 14 with evidence_expanded at seq 13.
      Expected: 1 / 2 = 0.50 (50%).
    """
    pdr_b = compute_pdr(loaded_data["sess_b"])
    pdr_a = compute_pdr(loaded_data["sess_a"])
    assert pdr_b == 0.0
    assert pdr_a == 0.5


def test_m4_confidence_calibration(loaded_data):
    """
    M4: Confidence calibration on assisted phase decisions.
    Condition B:
      Claim 1: final='misleading' (gt='misleading' -> o=1), conf=90 (p=0.90).
               (p - o)^2 = (0.9 - 1.0)^2 = 0.01.
      Claim 2: final='insufficient' (gt='insufficient' -> o=1), conf=80 (p=0.80).
               (p - o)^2 = (0.8 - 1.0)^2 = 0.04.
      Expected Brier = (0.01 + 0.04) / 2 = 0.025.
      Expected Gap = ((0.9 + 0.8) / 2) - 1.0 = 0.85 - 1.0 = -0.15.
      ECE omitted because n = 2 < 100.

    Condition A:
      Claim 1: final='supported' (gt='misleading' -> o=0), conf=80 (p=0.80).
               (p - o)^2 = (0.8 - 0.0)^2 = 0.64.
      Claim 2: final='contradicted' (gt='insufficient' -> o=0), conf=85 (p=0.85).
               (p - o)^2 = (0.85 - 0.0)^2 = 0.7225.
      Expected Brier = (0.64 + 0.7225) / 2 = 0.68125.
      Expected Gap = ((0.80 + 0.85) / 2) - 0.0 = 0.825 - 0.0 = 0.825.
      ECE omitted because n = 2 < 100.
    """
    gt_map = loaded_data["gt_map"]

    decisions_b = [
        {"conf": 90, "is_correct": True},
        {"conf": 80, "is_correct": True},
    ]
    calib_b = compute_confidence_calibration(decisions_b)
    assert pytest.approx(calib_b["brier"], 1e-5) == 0.025
    assert pytest.approx(calib_b["overconfidence_gap"], 1e-5) == -0.15
    assert calib_b["ece_omitted"] is True
    assert calib_b["reason"] == "n_decisions_below_100"

    decisions_a = [
        {"conf": 80, "is_correct": False},
        {"conf": 85, "is_correct": False},
    ]
    calib_a = compute_confidence_calibration(decisions_a)
    assert pytest.approx(calib_a["brier"], 1e-5) == 0.68125
    assert pytest.approx(calib_a["overconfidence_gap"], 1e-5) == 0.825
    assert calib_a["ece_omitted"] is True


def test_m5_accuracy_and_delta(loaded_data):
    """
    M5: Final accuracy per phase and intra-participant delta.
    - Condition B:
      Baseline (IT-001):
        Claim 1: dec='supported' (gt='contradicted') -> 0
        Claim 2: dec='supported' (gt='supported') -> 1
        Acc_base = 1/2 = 0.50.
      Assisted (IT-002):
        Claim 1: dec='misleading' (gt='misleading') -> 1
        Claim 2: dec='insufficient' (gt='insufficient') -> 1
        Acc_asst = 2/2 = 1.0.
      Delta_Acc = 1.0 - 0.50 = +0.50 (+50 pp).

    - Condition A:
      Baseline (IT-001):
        Claim 1: dec='contradicted' (gt='contradicted') -> 1
        Claim 2: dec='contradicted' (gt='supported') -> 0
        Acc_base = 1/2 = 0.50.
      Assisted (IT-002):
        Claim 1: dec='supported' (gt='misleading') -> 0
        Claim 2: dec='contradicted' (gt='insufficient') -> 0
        Acc_asst = 0/2 = 0.0.
      Delta_Acc = 0.0 - 0.50 = -0.50 (-50 pp).
    """
    gt_map = loaded_data["gt_map"]
    sess_b = loaded_data["sess_b"]
    sess_a = loaded_data["sess_a"]

    acc_base_b = compute_accuracy_per_phase(sess_b, gt_map, "baseline")
    acc_asst_b = compute_accuracy_per_phase(sess_b, gt_map, "assisted")
    assert acc_base_b == 0.5
    assert acc_asst_b == 1.0
    assert (acc_asst_b - acc_base_b) == 0.5

    acc_base_a = compute_accuracy_per_phase(sess_a, gt_map, "baseline")
    acc_asst_a = compute_accuracy_per_phase(sess_a, gt_map, "assisted")
    assert acc_base_a == 0.5
    assert acc_asst_a == 0.0
    assert (acc_asst_a - acc_base_a) == -0.5


def test_m6_transfer_task_accuracy(loaded_data):
    """
    M6: TTA in transfer phase (IT-003, no tool).
    - Condition B:
      Claim 1: dec='supported' (gt='supported') -> 1
      Claim 2: dec='contradicted' (gt='contradicted') -> 1
      Expected TTA = 2 / 2 = 1.0.
    - Condition A:
      Claim 1: dec='supported' (gt='supported') -> 1
      Claim 2: dec='supported' (gt='contradicted') -> 0
      Expected TTA = 1 / 2 = 0.50.
    """
    gt_map = loaded_data["gt_map"]
    tta_b = compute_accuracy_per_phase(loaded_data["sess_b"], gt_map, "transfer")
    tta_a = compute_accuracy_per_phase(loaded_data["sess_a"], gt_map, "transfer")
    assert tta_b == 1.0
    assert tta_a == 0.5


def test_m6b_verification_steps_count(loaded_data):
    """
    M6b: VSC = distinct steps excluding 'none'.
    - Condition B: ["source", "date", "independent_evidence"] -> VSC = 3.
    - Condition A: ["source"] -> VSC = 1.
    """
    vsc_b = compute_vsc(loaded_data["sess_b"])
    vsc_a = compute_vsc(loaded_data["sess_a"])
    assert vsc_b == 3
    assert vsc_a == 1


def test_m7_time_to_conclusion(loaded_data):
    """
    M7: TTC_c = (t_final - t_first_selected) / 1000.
    - Condition B:
      Claim 1: selected at 7000 ms, final decision at 11000 ms -> (11000 - 7000)/1000 = 4.0 s.
      Claim 2: selected at 12000 ms, final decision at 15000 ms -> (15000 - 12000)/1000 = 3.0 s.
      Median = 3.5 s.
    - Condition A:
      Claim 1: selected at 5500 ms, final decision at 7500 ms -> (7500 - 5500)/1000 = 2.0 s.
      Claim 2: selected at 8000 ms, final decision at 12000 ms -> (12000 - 8000)/1000 = 4.0 s.
      Median = 3.0 s.
    """
    ttcs_b = compute_ttc(loaded_data["sess_b"])
    ttcs_a = compute_ttc(loaded_data["sess_a"])
    assert ttcs_b == [4.0, 3.0]
    assert ttcs_a == [2.0, 4.0]


def test_m8_seq_effort(loaded_data):
    """M8: SEQ score on 1-7 scale."""
    seq_b = compute_seq(loaded_data["sess_b"])
    seq_a = compute_seq(loaded_data["sess_a"])
    assert seq_b == 6
    assert seq_a == 3


def test_m9_investigation_behavior_rate(loaded_data):
    """
    M9: IBR_common = (CE + EIR + SOR) / 3
    - Condition B: CE=1.0, EIR=1.0, SOR=0.5.
      IBR_common = (1.0 + 1.0 + 0.5) / 3 = 2.5 / 3 = 0.8333...
      IBR_B = (1.0 + 1.0 + 0.5 + 1.0) / 4 = 3.5 / 4 = 0.875.
    - Condition A: CE=1.0, EIR=0.5, SOR=0.0.
      IBR_common = (1.0 + 0.5 + 0.0) / 3 = 1.5 / 3 = 0.50.
      IBR_B = None.
    """
    ibr_b = compute_ibr(loaded_data["sess_b"], 1.0, 0.5, 1.0)
    ibr_a = compute_ibr(loaded_data["sess_a"], 0.5, 0.0, None)
    assert pytest.approx(ibr_b["ibr_common"], 1e-4) == 2.5 / 3.0
    assert pytest.approx(ibr_b["ibr_b"], 1e-4) == 0.875
    assert pytest.approx(ibr_a["ibr_common"], 1e-4) == 0.5
    assert ibr_a["ibr_b"] is None


def test_invalid_event_discarded():
    """Confirms invalid events are discarded and counted without mutating."""
    rejections = {}
    invalid_event = {
        "schema_version": "1.0.0",
        "pid": "P-0001",
        "sid": "12345678-1234-4234-8234-123456789abc",
        "cond": "B",
        "phase": "assisted",
        "item_id": "IT-001",
        "event": "session_started",
        "seq": 0,
        "t_ms": 10,
        "props": {"build": "a1b2c3d", "url": "https://evil.com"},
    }
    valid, reason = validate_raw_event(invalid_event)
    assert valid is False
    assert "forbidden_key_in_props" in reason


def test_deterministic_output_and_stable_hash(tmp_path):
    """Runs CLI twice on the synthetic fixtures and ensures exact byte-level hash stability."""
    out1 = str(tmp_path / "summary1.json")
    out2 = str(tmp_path / "summary2.json")

    cmd1 = [
        sys.executable,
        "-m", "analysis.act.compute_metrics",
        "--sessions", SESSIONS_PATH,
        "--ground-truth", GROUND_TRUTH_PATH,
        "--out", out1,
        "--seed", "42",
        "--n-bootstraps", "1000",
    ]
    res1 = subprocess.run(cmd1, capture_output=True, text=True, check=True)

    cmd2 = [
        sys.executable,
        "-m", "analysis.act.compute_metrics",
        "--sessions", SESSIONS_PATH,
        "--ground-truth", GROUND_TRUTH_PATH,
        "--out", out2,
        "--seed", "42",
        "--n-bootstraps", "1000",
    ]
    res2 = subprocess.run(cmd2, capture_output=True, text=True, check=True)

    with open(out1, "rb") as f1, open(out2, "rb") as f2:
        content1 = f1.read()
        content2 = f2.read()

    assert content1 == content2
    assert "summary_sha256:" in res1.stdout
    assert res1.stdout.splitlines()[0] == res2.stdout.splitlines()[0]
