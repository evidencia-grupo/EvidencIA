"""Domain models and verdict calculation for the Completeness Audit."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class Priority(str, Enum):
    P0 = "P0"  # Blocker
    P1 = "P1"  # Serious / Debt
    P2 = "P2"  # Low / Minor Debt


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


class Verdict(str, Enum):
    GO = "GO"
    GO_WITH_DEBT = "GO WITH DEBT"
    NO_GO = "NO-GO"


IMMEDIATE_NOGO_CHECK_IDS = {"ENG-01", "EDA-01", "ACT-03", "ACT-07", "ACT-08"}


@dataclass(frozen=True)
class Check:
    """Specification of an individual audit check."""

    id: str
    domain: str
    priority: Priority
    expected: str
    description: str
    repo: str  # "docs", "code", or "both"
    immediate_nogo: bool = False

    def __post_init__(self) -> None:
        if self.id in IMMEDIATE_NOGO_CHECK_IDS:
            object.__setattr__(self, "immediate_nogo", True)


@dataclass
class CheckResult:
    """Outcome of evaluating an individual audit check."""

    check_id: str
    status: Status
    found: str
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "status": self.status.value,
            "found": self.found,
            "details": self.details,
        }


@dataclass
class AuditSummary:
    """Aggregated verdict and summary counts for the audit run."""

    verdict: Verdict
    immediate_nogo_triggered: bool
    immediate_nogo_reasons: List[str]
    blockers: List[CheckResult]
    debts: List[CheckResult]
    skips: List[CheckResult]
    domain_counts: Dict[str, Dict[str, int]]
    overall_counts: Dict[str, int]
    exit_code: int


def calculate_verdict(
    results: List[CheckResult],
    checks_by_id: Dict[str, Check],
) -> AuditSummary:
    """Calculates the overall verdict following fail-closed rules.

    Rules:
    1. A P0 check that has status FAIL or SKIP is a BLOCKER.
    2. Any BLOCKER produces a NO-GO verdict.
    3. If any check in IMMEDIATE_NOGO_CHECK_IDS is not PASS,
       immediate_nogo_triggered is set to True (and verdict is NO-GO).
    4. If no BLOCKER exists, but P1/P2 checks have FAIL or WARN,
       verdict is GO WITH DEBT.
    5. If all checks PASS (or non-P0 SKIP), verdict is GO.
    """
    blockers: List[CheckResult] = []
    debts: List[CheckResult] = []
    skips: List[CheckResult] = []
    immediate_nogo_reasons: List[str] = []

    domain_counts: Dict[str, Dict[str, int]] = {}
    overall_counts: Dict[str, int] = {s.value: 0 for s in Status}

    for res in results:
        check = checks_by_id.get(res.check_id)
        domain = check.domain if check else "OTHER"
        priority = check.priority if check else Priority.P1

        if domain not in domain_counts:
            domain_counts[domain] = {s.value: 0 for s in Status}
        domain_counts[domain][res.status.value] += 1
        overall_counts[res.status.value] += 1

        if res.status == Status.SKIP:
            skips.append(res)

        # Check immediate NO-GO conditions
        if check and check.immediate_nogo and res.status != Status.PASS:
            immediate_nogo_reasons.append(
                f"{check.id}: {res.status.value} - {res.found} ({res.details})"
            )

        # Fail-closed: P0 SKIP is treated as FAIL / Blocker
        if priority == Priority.P0:
            if res.status in (Status.FAIL, Status.SKIP):
                blockers.append(res)
        elif priority in (Priority.P1, Priority.P2):
            if res.status in (Status.FAIL, Status.WARN):
                debts.append(res)

    immediate_triggered = len(immediate_nogo_reasons) > 0

    if blockers or immediate_triggered:
        verdict = Verdict.NO_GO
        exit_code = 20
    elif debts:
        verdict = Verdict.GO_WITH_DEBT
        exit_code = 10
    else:
        verdict = Verdict.GO
        exit_code = 0

    return AuditSummary(
        verdict=verdict,
        immediate_nogo_triggered=immediate_triggered,
        immediate_nogo_reasons=immediate_nogo_reasons,
        blockers=blockers,
        debts=debts,
        skips=skips,
        domain_counts=domain_counts,
        overall_counts=overall_counts,
        exit_code=exit_code,
    )
