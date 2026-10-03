#!/usr/bin/env python3
"""
CBL Act Metrics Computation Tool — EvidencIA.
Strict Python stdlib implementation of behavioral metrics M1 to M9.
Computes non-parametric bootstrap confidence intervals (10,000 resamples),
generates deterministic summary.json, and outputs SHA-256 hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

PID_REGEX = re.compile(r"^P-[0-9]{4}$")
SID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.IGNORECASE)
ITEM_ID_REGEX = re.compile(r"^IT-[0-9]{3}$")
BUILD_REGEX = re.compile(r"^[a-f0-9]{7,12}$")

URL_PATTERN = re.compile(r"(?:https?://|www\.)[^\s/$.?#].[^\s]*", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")

FORBIDDEN_KEYS = {
    "text", "transcript", "url", "video_id", "videoId",
    "name", "email", "cpf", "comment", "query", "title", "message"
}

EVENT_ALLOWLIST = {
    "session_started": ["build"],
    "item_presented": ["n_claims"],
    "claims_viewed": ["n_claims_visible"],
    "claim_selected": ["claim_ordinal"],
    "evidence_expanded": ["claim_ordinal", "evidence_ordinal", "relation"],
    "source_opened": ["claim_ordinal", "evidence_ordinal"],
    "uncertainty_viewed": ["claim_ordinal", "kind"],
    "reflection_viewed": ["claim_ordinal", "question_ordinal"],
    "reflection_interacted": ["claim_ordinal", "question_ordinal", "interaction"],
    "global_verdict_viewed": [],
    "decision_submitted": ["claim_ordinal", "stage", "decision", "confidence"],
    "post_task_questionnaire": ["effort_seq", "verification_steps"],
    "session_ended": ["reason"],
}

ENVELOPE_KEYS = {
    "schema_version", "pid", "sid", "cond", "phase", "item_id",
    "event", "seq", "t_ms", "props", "synthetic"
}


def validate_raw_event(raw: Any) -> Tuple[bool, Optional[str]]:
    """Validates an event line against the strict CBL Act schema."""
    if not isinstance(raw, dict):
        return False, "not_an_object"

    for k in raw:
        if k not in ENVELOPE_KEYS:
            return False, f"unknown_envelope_key:{k}"

    required_keys = {"schema_version", "pid", "sid", "cond", "phase", "item_id", "event", "seq", "t_ms", "props"}
    for req in required_keys:
        if req not in raw:
            return False, f"missing_envelope_key:{req}"

    if raw["schema_version"] != SCHEMA_VERSION:
        return False, "invalid_schema_version"

    if not isinstance(raw["pid"], str) or not PID_REGEX.match(raw["pid"]):
        return False, "invalid_pid"

    if not isinstance(raw["sid"], str) or not SID_REGEX.match(raw["sid"]):
        return False, "invalid_sid"

    if raw["cond"] not in ("A", "B"):
        return False, "invalid_condition"

    if raw["phase"] not in ("baseline", "assisted", "transfer"):
        return False, "invalid_phase"

    if not isinstance(raw["item_id"], str) or not ITEM_ID_REGEX.match(raw["item_id"]):
        return False, "invalid_item_id"

    event = raw["event"]
    if event not in EVENT_ALLOWLIST:
        return False, f"unknown_event:{event}"

    if not isinstance(raw["seq"], int) or raw["seq"] < 0:
        return False, "invalid_seq"

    if not isinstance(raw["t_ms"], (int, float)) or raw["t_ms"] < 0:
        return False, "invalid_t_ms"

    props = raw["props"]
    if not isinstance(props, dict):
        return False, "props_not_an_object"

    for pk in props:
        if pk in FORBIDDEN_KEYS:
            return False, f"forbidden_key_in_props:{pk}"

    allowed_keys = EVENT_ALLOWLIST[event]
    if len(props) != len(allowed_keys):
        return False, f"prop_keys_count_mismatch:{event}"

    for ak in allowed_keys:
        if ak not in props:
            return False, f"missing_prop_key:{ak}"

    for pk in props:
        if pk not in allowed_keys:
            return False, f"unknown_prop_key:{pk}"

    # Specific property constraints
    if event == "session_started":
        build = props.get("build")
        if not isinstance(build, str) or not BUILD_REGEX.match(build):
            return False, "invalid_build_hash"
    elif event == "item_presented":
        nc = props.get("n_claims")
        if not isinstance(nc, int) or not (1 <= nc <= 10):
            return False, "invalid_n_claims"
    elif event == "claims_viewed":
        ncv = props.get("n_claims_visible")
        if not isinstance(ncv, int) or not (1 <= ncv <= 10):
            return False, "invalid_n_claims_visible"
    elif event == "claim_selected":
        co = props.get("claim_ordinal")
        if not isinstance(co, int) or not (1 <= co <= 10):
            return False, "invalid_claim_ordinal"
    elif event == "evidence_expanded":
        co = props.get("claim_ordinal")
        eo = props.get("evidence_ordinal")
        rel = props.get("relation")
        if not isinstance(co, int) or not (1 <= co <= 10):
            return False, "invalid_claim_ordinal"
        if not isinstance(eo, int) or not (1 <= eo <= 20):
            return False, "invalid_evidence_ordinal"
        if rel not in ("supports", "contradicts", "contextualizes", "unspecified"):
            return False, "invalid_evidence_relation"
    elif event == "source_opened":
        co = props.get("claim_ordinal")
        eo = props.get("evidence_ordinal")
        if not isinstance(co, int) or not (1 <= co <= 10):
            return False, "invalid_claim_ordinal"
        if not isinstance(eo, int) or not (1 <= eo <= 20):
            return False, "invalid_evidence_ordinal"
    elif event == "uncertainty_viewed":
        co = props.get("claim_ordinal")
        kind = props.get("kind")
        if not isinstance(co, int) or not (1 <= co <= 10):
            return False, "invalid_claim_ordinal"
        if kind not in ("insufficient_evidence", "conflicting", "dated"):
            return False, "invalid_uncertainty_kind"
    elif event == "reflection_viewed":
        co = props.get("claim_ordinal")
        qo = props.get("question_ordinal")
        if not isinstance(co, int) or not (1 <= co <= 10):
            return False, "invalid_claim_ordinal"
        if not isinstance(qo, int) or not (1 <= qo <= 5):
            return False, "invalid_question_ordinal"
    elif event == "reflection_interacted":
        co = props.get("claim_ordinal")
        qo = props.get("question_ordinal")
        inter = props.get("interaction")
        if not isinstance(co, int) or not (1 <= co <= 10):
            return False, "invalid_claim_ordinal"
        if not isinstance(qo, int) or not (1 <= qo <= 5):
            return False, "invalid_question_ordinal"
        if inter not in ("expanded", "answered", "dismissed"):
            return False, "invalid_reflection_interaction"
    elif event == "decision_submitted":
        co = props.get("claim_ordinal")
        stage = props.get("stage")
        dec = props.get("decision")
        conf = props.get("confidence")
        if not isinstance(co, int) or not (1 <= co <= 10):
            return False, "invalid_claim_ordinal"
        if stage not in ("pre_evidence", "final"):
            return False, "invalid_decision_stage"
        if dec not in ("supported", "contradicted", "misleading", "insufficient", "cannot_determine"):
            return False, "invalid_decision_verdict"
        if not isinstance(conf, int) or not (0 <= conf <= 100):
            return False, "invalid_confidence"
    elif event == "post_task_questionnaire":
        seq = props.get("effort_seq")
        steps = props.get("verification_steps")
        if not isinstance(seq, int) or not (1 <= seq <= 7):
            return False, "invalid_effort_seq"
        if not isinstance(steps, list) or len(steps) == 0:
            return False, "invalid_verification_steps"
        allowed_steps = {"source", "date", "independent_evidence", "context", "none"}
        seen_steps = set()
        for s in steps:
            if s not in allowed_steps:
                return False, f"invalid_step:{s}"
            if s in seen_steps:
                return False, f"duplicate_step:{s}"
            seen_steps.add(s)
    elif event == "session_ended":
        reason = props.get("reason")
        if reason not in ("completed", "abandoned", "timeout"):
            return False, "invalid_session_end_reason"

    return True, None


class SessionData:
    def __init__(self, pid: str, sid: str, cond: str):
        self.pid = pid
        self.sid = sid
        self.cond = cond
        self.events: List[Dict[str, Any]] = []

    def add_event(self, ev: Dict[str, Any]):
        self.events.append(ev)


def load_sessions(source_path: str, rejections: Dict[str, int]) -> Dict[str, SessionData]:
    """Reads JSONL files from path or directory and parses valid events into sessions."""
    files: List[str] = []
    if os.path.isdir(source_path):
        for root, _, filenames in os.walk(source_path):
            for fn in filenames:
                if fn.endswith(".jsonl"):
                    files.append(os.path.join(root, fn))
    elif os.path.isfile(source_path):
        files.append(source_path)
    else:
        raise FileNotFoundError(f"Source path {source_path} does not exist.")

    sessions: Dict[str, SessionData] = {}

    for file_path in sorted(files):
        with open(file_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    raw_event = json.loads(clean_line)
                except Exception:
                    rejections["json_parse_error"] = rejections.get("json_parse_error", 0) + 1
                    continue

                valid, reason = validate_raw_event(raw_event)
                if not valid:
                    key = reason or "unknown_rejection"
                    rejections[key] = rejections.get(key, 0) + 1
                    continue

                sid = raw_event["sid"]
                if sid not in sessions:
                    sessions[sid] = SessionData(
                        pid=raw_event["pid"],
                        sid=sid,
                        cond=raw_event["cond"],
                    )
                sessions[sid].add_event(raw_event)

    # Sort events by seq
    for s in sessions.values():
        s.events.sort(key=lambda x: x["seq"])

    return sessions


def load_ground_truth(gt_path: str) -> Dict[str, Dict[str, str]]:
    """Loads ground truth item mapping."""
    with open(gt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data.get("items", {})
    gt_map: Dict[str, Dict[str, str]] = {}
    for item_id, item_val in items.items():
        gt_map[item_id] = {}
        for claim_ord, verdict in item_val.get("claims", {}).items():
            gt_map[item_id][str(claim_ord)] = verdict
    return gt_map


# =============================================================================
# METRIC FUNCTIONS M1 TO M9
# =============================================================================

def compute_eir(session: SessionData) -> Optional[float]:
    """
    M1: Evidence Inspection Rate (EIR)
    EIR_s = |claims with >= 1 evidence_expanded| / |claims viewed| (assisted phase).
    Denominator 0 -> returns None (excluded).
    """
    assisted_events = [e for e in session.events if e["phase"] == "assisted"]
    claims_viewed_counts = [e["props"]["n_claims_visible"] for e in assisted_events if e["event"] == "claims_viewed"]
    if not claims_viewed_counts or max(claims_viewed_counts) == 0:
        return None

    denom = max(claims_viewed_counts)
    expanded_claims = {
        e["props"]["claim_ordinal"]
        for e in assisted_events
        if e["event"] == "evidence_expanded"
    }
    return min(1.0, len(expanded_claims) / float(denom))


def compute_sor(session: SessionData) -> Optional[float]:
    """
    M1b: Source Open Rate (SOR)
    SOR_s = |claims with >= 1 source_opened| / |claims viewed| (assisted phase).
    Denominator 0 -> returns None.
    """
    assisted_events = [e for e in session.events if e["phase"] == "assisted"]
    claims_viewed_counts = [e["props"]["n_claims_visible"] for e in assisted_events if e["event"] == "claims_viewed"]
    if not claims_viewed_counts or max(claims_viewed_counts) == 0:
        return None

    denom = max(claims_viewed_counts)
    opened_claims = {
        e["props"]["claim_ordinal"]
        for e in assisted_events
        if e["event"] == "source_opened"
    }
    return min(1.0, len(opened_claims) / float(denom))


def compute_rir(session: SessionData) -> Optional[float]:
    """
    M2: Reflection Interaction Rate (RIR, Cond B only)
    RIR_s = |questions with reflection_interacted in {expanded, answered}| / |questions reflection_viewed|.
    """
    if session.cond != "B":
        return None

    assisted_events = [e for e in session.events if e["phase"] == "assisted"]
    viewed_questions = {
        (e["props"]["claim_ordinal"], e["props"]["question_ordinal"])
        for e in assisted_events
        if e["event"] == "reflection_viewed"
    }
    if not viewed_questions:
        return None

    interacted_questions = {
        (e["props"]["claim_ordinal"], e["props"]["question_ordinal"])
        for e in assisted_events
        if e["event"] == "reflection_interacted" and e["props"]["interaction"] in ("expanded", "answered")
    }
    return min(1.0, len(interacted_questions) / float(len(viewed_questions)))


def compute_err(session: SessionData, gt_map: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    """
    M3: Evidence Revision Rate (ERR)
    For decisions with pre_evidence and final on same claim, with >= 1 evidence_expanded between:
    ERR = sum(final != pre) / sum(eligible decisions).
    Sub-rates: ERR_correct (revised to correct) and ERR_harm (revised from correct to incorrect).
    """
    assisted_events = [e for e in session.events if e["phase"] == "assisted"]
    item_id = assisted_events[0]["item_id"] if assisted_events else ""

    decisions: Dict[int, Dict[str, Any]] = {}
    for ev in assisted_events:
        co = ev["props"].get("claim_ordinal")
        if not co:
            continue
        if co not in decisions:
            decisions[co] = {"pre": None, "final": None, "pre_seq": None, "final_seq": None, "exp_seqs": []}

        if ev["event"] == "decision_submitted":
            stage = ev["props"]["stage"]
            if stage == "pre_evidence" and decisions[co]["pre"] is None:
                decisions[co]["pre"] = ev["props"]["decision"]
                decisions[co]["pre_seq"] = ev["seq"]
            elif stage == "final":
                decisions[co]["final"] = ev["props"]["decision"]
                decisions[co]["final_seq"] = ev["seq"]
        elif ev["event"] == "evidence_expanded":
            decisions[co]["exp_seqs"].append(ev["seq"])

    eligible = 0
    revised = 0
    correct_revised = 0
    harm_revised = 0

    for co, data in decisions.items():
        if data["pre"] is not None and data["final"] is not None:
            pre_s = data["pre_seq"]
            fin_s = data["final_seq"]
            has_evidence_between = any(pre_s < exp_s < fin_s for exp_s in data["exp_seqs"])
            if has_evidence_between:
                eligible += 1
                if data["pre"] != data["final"]:
                    revised += 1
                    gt = gt_map.get(item_id, {}).get(str(co))
                    if gt:
                        if data["pre"] != gt and data["final"] == gt:
                            correct_revised += 1
                        elif data["pre"] == gt and data["final"] != gt:
                            harm_revised += 1

    err_rate = (revised / float(eligible)) if eligible > 0 else 0.0
    err_correct = (correct_revised / float(revised)) if revised > 0 else None
    err_harm = (harm_revised / float(revised)) if revised > 0 else None

    return {
        "eligible": eligible,
        "revised": revised,
        "err_rate": err_rate,
        "err_correct": err_correct,
        "err_harm": err_harm,
    }


def compute_pdr(session: SessionData) -> Optional[float]:
    """
    M3b: Premature Decision Rate (PDR)
    decisions final without any evidence_expanded on claim / decisions in assisted phase.
    """
    assisted_events = [e for e in session.events if e["phase"] == "assisted"]
    final_decisions: Dict[int, Any] = {}
    expanded_claims = set()

    for ev in assisted_events:
        if ev["event"] == "evidence_expanded":
            expanded_claims.add(ev["props"]["claim_ordinal"])
        elif ev["event"] == "decision_submitted" and ev["props"]["stage"] == "final":
            final_decisions[ev["props"]["claim_ordinal"]] = ev

    if not final_decisions:
        return None

    premature_count = sum(1 for co in final_decisions if co not in expanded_claims)
    return premature_count / float(len(final_decisions))


def compute_confidence_calibration(decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    M4: Confidence Calibration
    p = conf / 100.
    Brier = mean((p - o)^2).
    Overconfidence gap = mean(p) - mean(o).
    ECE (5 bins) ONLY if n_decisions >= 100.
    """
    n = len(decisions)
    if n == 0:
        return {"brier": None, "overconfidence_gap": None, "ece": None, "ece_omitted": True, "reason": "no_decisions"}

    brier_sum = 0.0
    p_sum = 0.0
    o_sum = 0.0

    for d in decisions:
        p = d["conf"] / 100.0
        o = 1.0 if d["is_correct"] else 0.0
        brier_sum += (p - o) ** 2
        p_sum += p
        o_sum += o

    brier = brier_sum / float(n)
    overconfidence_gap = (p_sum / float(n)) - (o_sum / float(n))

    ece = None
    ece_omitted = True
    reason = "n_decisions_below_100"

    if n >= 100:
        ece_omitted = False
        reason = None
        # 5 equal-width bins: [0, 0.2), [0.2, 0.4), [0.4, 0.6), [0.6, 0.8), [0.8, 1.0]
        bins: List[List[Dict[str, Any]]] = [[] for _ in range(5)]
        for d in decisions:
            p = d["conf"] / 100.0
            idx = min(4, int(p * 5))
            bins[idx].append(d)

        ece_acc = 0.0
        for b in bins:
            if b:
                bin_acc = sum(1.0 for item in b if item["is_correct"]) / float(len(b))
                bin_conf = sum(item["conf"] / 100.0 for item in b) / float(len(b))
                ece_acc += (len(b) / float(n)) * abs(bin_acc - bin_conf)
        ece = ece_acc

    return {
        "brier": brier,
        "overconfidence_gap": overconfidence_gap,
        "ece": ece,
        "ece_omitted": ece_omitted,
        "reason": reason,
        "n_decisions": n,
    }


def compute_accuracy_per_phase(session: SessionData, gt_map: Dict[str, Dict[str, str]], phase: str) -> Optional[float]:
    """Computes final decision accuracy for a specific phase."""
    events = [e for e in session.events if e["phase"] == phase and e["event"] == "decision_submitted" and e["props"]["stage"] == "final"]
    if not events:
        return None

    correct = 0
    total = 0
    for ev in events:
        item_id = ev["item_id"]
        co = str(ev["props"]["claim_ordinal"])
        gt = gt_map.get(item_id, {}).get(co)
        if gt:
            total += 1
            if ev["props"]["decision"] == gt:
                correct += 1

    return (correct / float(total)) if total > 0 else None


def compute_ttc(session: SessionData) -> List[float]:
    """
    M7: Time to Conclusion (TTC) in seconds per claim.
    TTC_c = (t_final_decision - t_first_claim_selected) / 1000.
    """
    assisted_events = [e for e in session.events if e["phase"] == "assisted"]
    claim_first_selected: Dict[int, int] = {}
    claim_final_decision: Dict[int, int] = {}

    for ev in assisted_events:
        co = ev["props"].get("claim_ordinal")
        if not co:
            continue
        if ev["event"] == "claim_selected" and co not in claim_first_selected:
            claim_first_selected[co] = ev["t_ms"]
        elif ev["event"] == "decision_submitted" and ev["props"]["stage"] == "final":
            claim_final_decision[co] = ev["t_ms"]

    ttcs: List[float] = []
    for co, fin_t in claim_final_decision.items():
        start_t = claim_first_selected.get(co)
        if start_t is not None and fin_t >= start_t:
            ttcs.append((fin_t - start_t) / 1000.0)

    return ttcs


def compute_vsc(session: SessionData) -> Optional[int]:
    """
    M6b: Verification Steps Count (VSC)
    Count of distinct steps in transfer questionnaire, excluding 'none'.
    """
    for ev in reversed(session.events):
        if ev["event"] == "post_task_questionnaire":
            steps = ev["props"].get("verification_steps", [])
            valid_steps = [s for s in steps if s != "none"]
            return len(set(valid_steps))
    return None


def compute_seq(session: SessionData) -> Optional[int]:
    """M8: Subjective Effort (SEQ 1 to 7)."""
    for ev in reversed(session.events):
        if ev["event"] == "post_task_questionnaire":
            return ev["props"].get("effort_seq")
    return None


def compute_ibr(session: SessionData, eir: Optional[float], sor: Optional[float], rir: Optional[float]) -> Dict[str, Optional[float]]:
    """
    M9: Investigation Behavior Rate (IBR).
    Operational non-psychometric metric. Never displayed as a score.
    """
    assisted_events = [e for e in session.events if e["phase"] == "assisted"]
    claims_viewed_counts = [e["props"]["n_claims_visible"] for e in assisted_events if e["event"] == "claims_viewed"]
    if not claims_viewed_counts or max(claims_viewed_counts) == 0:
        return {"ibr_common": None, "ibr_b": None}

    denom = max(claims_viewed_counts)
    selected_claims = {e["props"]["claim_ordinal"] for e in assisted_events if e["event"] == "claim_selected"}
    ce = min(1.0, len(selected_claims) / float(denom))

    eir_val = eir if eir is not None else 0.0
    sor_val = sor if sor is not None else 0.0
    ibr_common = (ce + eir_val + sor_val) / 3.0

    ibr_b = None
    if session.cond == "B":
        rir_val = rir if rir is not None else 0.0
        ibr_b = (ce + eir_val + sor_val + rir_val) / 4.0

    return {"ibr_common": ibr_common, "ibr_b": ibr_b}


# =============================================================================
# BOOTSTRAP RESAMPLING & SUMMARY COMPILATION
# =============================================================================

def bootstrap_ci(
    data: List[float],
    n_resamples: int = 10000,
    rng: Optional[random.Random] = None,
    alpha: float = 0.05
) -> Optional[Tuple[float, float]]:
    """Estimates percentile bootstrap 95% confidence interval."""
    if not data:
        return None
    if len(data) == 1:
        return (data[0], data[0])

    if rng is None:
        rng = random.Random(42)

    n = len(data)
    boot_means: List[float] = []
    for _ in range(n_resamples):
        sample = [data[rng.randint(0, n - 1)] for _ in range(n)]
        boot_means.append(sum(sample) / float(n))

    boot_means.sort()
    lower_idx = int((alpha / 2.0) * n_resamples)
    upper_idx = int((1.0 - alpha / 2.0) * n_resamples)
    upper_idx = min(upper_idx, n_resamples - 1)

    return (boot_means[lower_idx], boot_means[upper_idx])


def bootstrap_diff_ci(
    data_b: List[float],
    data_a: List[float],
    n_resamples: int = 10000,
    rng: Optional[random.Random] = None,
    alpha: float = 0.05
) -> Optional[Tuple[float, float]]:
    """Estimates bootstrap confidence interval for difference (B - A)."""
    if not data_b or not data_a:
        return None

    if rng is None:
        rng = random.Random(42)

    nb = len(data_b)
    na = len(data_a)
    boot_diffs: List[float] = []

    for _ in range(n_resamples):
        sb = sum(data_b[rng.randint(0, nb - 1)] for _ in range(nb)) / float(nb)
        sa = sum(data_a[rng.randint(0, na - 1)] for _ in range(na)) / float(na)
        boot_diffs.append(sb - sa)

    boot_diffs.sort()
    lower_idx = int((alpha / 2.0) * n_resamples)
    upper_idx = min(int((1.0 - alpha / 2.0) * n_resamples), n_resamples - 1)

    return (boot_diffs[lower_idx], boot_diffs[upper_idx])


def median_and_iqr(vals: List[float]) -> Dict[str, Optional[float]]:
    if not vals:
        return {"median": None, "iqr": None, "q25": None, "q75": None}
    sorted_v = sorted(vals)
    n = len(sorted_v)

    def percentile(p: float) -> float:
        idx = p * (n - 1)
        lo = int(math.floor(idx))
        hi = int(math.ceil(idx))
        if lo == hi:
            return sorted_v[lo]
        return sorted_v[lo] + (idx - lo) * (sorted_v[hi] - sorted_v[lo])

    med = percentile(0.5)
    q25 = percentile(0.25)
    q75 = percentile(0.75)
    return {"median": med, "iqr": q75 - q25, "q25": q25, "q75": q75}


def compute_all_metrics(
    sessions: Dict[str, SessionData],
    gt_map: Dict[str, Dict[str, str]],
    seed: int = 42,
    n_bootstraps: int = 10000
) -> Dict[str, Any]:
    """Computes all summary metrics across sessions."""
    rng = random.Random(seed)

    sessions_a = [s for s in sessions.values() if s.cond == "A"]
    sessions_b = [s for s in sessions.values() if s.cond == "B"]

    def extract_session_metrics(sess_list: List[SessionData]):
        eirs, sors, rirs, pdrs = [], [], [], []
        acc_baselines, acc_assisteds, delta_accs, ttas, vscs, seqs = [], [], [], [], [], []
        ttcs: List[float] = []
        ibr_commons, ibr_bs = [], []
        decisions_for_calib: List[Dict[str, Any]] = []

        err_eligible_total = 0
        err_revised_total = 0
        err_correct_total = 0
        err_harm_total = 0

        for s in sess_list:
            eir = compute_eir(s)
            if eir is not None:
                eirs.append(eir)

            sor = compute_sor(s)
            if sor is not None:
                sors.append(sor)

            rir = compute_rir(s)
            if rir is not None:
                rirs.append(rir)

            pdr = compute_pdr(s)
            if pdr is not None:
                pdrs.append(pdr)

            err_res = compute_err(s, gt_map)
            err_eligible_total += err_res["eligible"]
            err_revised_total += err_res["revised"]
            if err_res["err_correct"] is not None:
                err_correct_total += int(round(err_res["err_correct"] * err_res["revised"]))
            if err_res["err_harm"] is not None:
                err_harm_total += int(round(err_res["err_harm"] * err_res["revised"]))

            acc_base = compute_accuracy_per_phase(s, gt_map, "baseline")
            if acc_base is not None:
                acc_baselines.append(acc_base)

            acc_asst = compute_accuracy_per_phase(s, gt_map, "assisted")
            if acc_asst is not None:
                acc_assisteds.append(acc_asst)

            if acc_base is not None and acc_asst is not None:
                delta_accs.append(acc_asst - acc_base)

            tta = compute_accuracy_per_phase(s, gt_map, "transfer")
            if tta is not None:
                ttas.append(tta)

            vsc = compute_vsc(s)
            if vsc is not None:
                vscs.append(float(vsc))

            seq = compute_seq(s)
            if seq is not None:
                seqs.append(float(seq))

            ttcs.extend(compute_ttc(s))

            ibr = compute_ibr(s, eir, sor, rir)
            if ibr["ibr_common"] is not None:
                ibr_commons.append(ibr["ibr_common"])
            if ibr["ibr_b"] is not None:
                ibr_bs.append(ibr["ibr_b"])

            # Decisions for calibration in assisted phase
            for ev in s.events:
                if ev["phase"] == "assisted" and ev["event"] == "decision_submitted" and ev["props"]["stage"] == "final":
                    gt = gt_map.get(ev["item_id"], {}).get(str(ev["props"]["claim_ordinal"]))
                    if gt:
                        decisions_for_calib.append({
                            "conf": ev["props"]["confidence"],
                            "is_correct": ev["props"]["decision"] == gt
                        })

        err_agg = {
            "eligible": err_eligible_total,
            "revised": err_revised_total,
            "err_rate": (err_revised_total / float(err_eligible_total)) if err_eligible_total > 0 else 0.0,
            "err_correct": (err_correct_total / float(err_revised_total)) if err_revised_total > 0 else None,
            "err_harm": (err_harm_total / float(err_revised_total)) if err_revised_total > 0 else None,
        }

        calib = compute_confidence_calibration(decisions_for_calib)

        def pack_metric(vals: List[float]):
            if not vals:
                return {"n": 0, "mean": None, "ci_95": None}
            m = sum(vals) / float(len(vals))
            ci = bootstrap_ci(vals, n_bootstraps, rng)
            return {"n": len(vals), "mean": m, "ci_95": ci}

        return {
            "eir": pack_metric(eirs),
            "sor": pack_metric(sors),
            "rir": pack_metric(rirs),
            "pdr": pack_metric(pdrs),
            "err": err_agg,
            "accuracy_baseline": pack_metric(acc_baselines),
            "accuracy_assisted": pack_metric(acc_assisteds),
            "delta_accuracy": pack_metric(delta_accs),
            "tta": pack_metric(ttas),
            "vsc": pack_metric(vscs),
            "seq": {
                **pack_metric(seqs),
                **median_and_iqr(seqs)
            },
            "ttc": median_and_iqr(ttcs),
            "ibr_common": pack_metric(ibr_commons),
            "ibr_b": pack_metric(ibr_bs),
            "calibration": calib,
            "raw_lists": {
                "eirs": eirs,
                "sors": sors,
                "pdrs": pdrs,
                "acc_assisteds": acc_assisteds,
                "ttas": ttas,
                "seqs": seqs,
                "ttcs": ttcs,
            }
        }

    res_a = extract_session_metrics(sessions_a)
    res_b = extract_session_metrics(sessions_b)

    # Cross-condition differences (B - A)
    diff_eir = bootstrap_diff_ci(res_b["raw_lists"]["eirs"], res_a["raw_lists"]["eirs"], n_bootstraps, rng)
    diff_acc = bootstrap_diff_ci(res_b["raw_lists"]["acc_assisteds"], res_a["raw_lists"]["acc_assisteds"], n_bootstraps, rng)
    diff_tta = bootstrap_diff_ci(res_b["raw_lists"]["ttas"], res_a["raw_lists"]["ttas"], n_bootstraps, rng)

    ttc_ratio = None
    if res_a["ttc"]["median"] and res_b["ttc"]["median"] and res_a["ttc"]["median"] > 0:
        ttc_ratio = res_b["ttc"]["median"] / float(res_a["ttc"]["median"])

    # Clean raw lists from final output
    del res_a["raw_lists"]
    del res_b["raw_lists"]

    return {
        "condition_A": res_a,
        "condition_B": res_b,
        "comparisons": {
            "diff_eir_b_minus_a_ci95": diff_eir,
            "diff_acc_b_minus_a_ci95": diff_acc,
            "diff_tta_b_minus_a_ci95": diff_tta,
            "ttc_median_ratio_b_over_a": ttc_ratio,
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Compute CBL Act behavioral experiment metrics.")
    parser.add_argument("--sessions", required=True, help="Path to JSONL session file or directory")
    parser.add_argument("--ground-truth", required=True, help="Path to ground_truth.json")
    parser.add_argument("--out", default="analysis/act/out/summary.json", help="Output summary JSON path")
    parser.add_argument("--seed", type=int, default=42, help="Pseudo-random seed for bootstrap")
    parser.add_argument("--n-bootstraps", type=int, default=10000, help="Number of bootstrap resamples")
    args = parser.parse_args()

    rejections: Dict[str, int] = {}
    sessions = load_sessions(args.sessions, rejections)
    gt_map = load_ground_truth(args.ground_truth)

    metrics_result = compute_all_metrics(sessions, gt_map, seed=args.seed, n_bootstraps=args.n_bootstraps)

    n_sessions_a = sum(1 for s in sessions.values() if s.cond == "A")
    n_sessions_b = sum(1 for s in sessions.values() if s.cond == "B")

    summary_payload = {
        "schema_version": SCHEMA_VERSION,
        "seed": args.seed,
        "n_bootstraps": args.n_bootstraps,
        "n_sessions": {
            "condition_A": n_sessions_a,
            "condition_B": n_sessions_b,
            "total": len(sessions),
        },
        "rejections": rejections,
        "exclusions": [],
        "metrics": metrics_result,
    }

    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)

    json_str = json.dumps(summary_payload, indent=2, sort_keys=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(json_str + "\n")

    sha256_hash = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    print(f"summary_sha256: sha256:{sha256_hash}")
    print(f"Output successfully written to {args.out}")


if __name__ == "__main__":
    main()
