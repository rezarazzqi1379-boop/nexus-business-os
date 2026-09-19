from dataclasses import dataclass

from nexus_evals import evaluate_case
from nexus_evals.adapters import (
    action_scope_case,
    procurement_evidence_semantics_case,
    requirement_readiness_case,
)


@dataclass(frozen=True)
class _Evidence:
    kind: str
    summary: str


@dataclass(frozen=True)
class _Signal:
    description: str


@dataclass(frozen=True)
class _Outcome:
    result: str


@dataclass(frozen=True)
class _Record:
    case_id: str
    evidence: _Evidence
    signal: _Signal
    outcome: _Outcome

    def validate(self):
        return []


@dataclass(frozen=True)
class _Readiness:
    ready_for_discovery: bool
    ready_for_final_request: bool
    blocking_ids: tuple[str, ...]
    provisional_ids: tuple[str, ...]
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Intent:
    action_id: str
    kind: str


@dataclass(frozen=True)
class _Approval:
    action_id: str
    approved: bool = True


@dataclass(frozen=True)
class _Decision:
    allowed_now: bool
    requires_human_approval: bool
    reason: str


def test_pr1_adapter_preserves_claim_semantics():
    record = _Record(
        case_id="suppliertr-2026-08-18",
        evidence=_Evidence(
            kind="claim",
            summary="SupplierTR stated that engineering evaluation had started.",
        ),
        signal=_Signal(description="SupplierTR reports engineering evaluation started."),
        outcome=_Outcome(
            result="SupplierTR reported engineering evaluation started; verification remains open."
        ),
    )

    result = evaluate_case(
        procurement_evidence_semantics_case(
            record,
            expected_kind="claim",
            input_ref="github:pull:1",
            evidence_refs=("github:pull:1", "gmail:message:1a014a58e73ec883"),
        )
    )

    assert result.passed is True


def test_pr1_adapter_catches_claim_promoted_to_fact():
    record = _Record(
        case_id="suppliertr-regression",
        evidence=_Evidence(kind="fact", summary="Supplier confirmed evaluation."),
        signal=_Signal(description="Engineering evaluation started."),
        outcome=_Outcome(result="Engineering evaluation started."),
    )

    result = evaluate_case(
        procurement_evidence_semantics_case(
            record,
            expected_kind="claim",
            input_ref="github:pull:1:historical-regression",
            evidence_refs=("github:pull:1",),
        )
    )

    assert result.passed is False
    assert "epistemic-kind-preserved" in result.failed_assertion_ids


def test_pr2_adapter_preserves_real_hydrotester_blockers():
    assessment = _Readiness(
        ready_for_discovery=True,
        ready_for_final_request=False,
        blocking_ids=("hydrotester.length", "hydrotester.wall_thickness_or_id"),
        provisional_ids=("hydrotester.od", "hydrotester.max_pressure"),
    )

    result = evaluate_case(
        requirement_readiness_case(
            assessment,
            input_ref="github:pull:2",
            evidence_refs=("github:pull:2", "gmail:message:1a018c1b2c80c8e3"),
            expected_blocking_ids=(
                "hydrotester.length",
                "hydrotester.wall_thickness_or_id",
            ),
            expected_provisional_ids=(
                "hydrotester.od",
                "hydrotester.max_pressure",
            ),
        )
    )

    assert result.passed is True


def test_pr2_adapter_catches_silent_final_readiness_promotion():
    assessment = _Readiness(
        ready_for_discovery=True,
        ready_for_final_request=True,
        blocking_ids=("hydrotester.length",),
        provisional_ids=("hydrotester.od",),
    )

    result = evaluate_case(
        requirement_readiness_case(
            assessment,
            input_ref="github:pull:2:fail-open-replay",
            evidence_refs=("github:pull:2",),
            expected_blocking_ids=("hydrotester.length",),
            expected_provisional_ids=("hydrotester.od",),
        )
    )

    assert result.passed is False
    assert "final-readiness-fails-closed" in result.failed_assertion_ids


def test_pr4_adapter_accepts_matching_action_scoped_approval():
    intent = _Intent(action_id="merge-1", kind="merge_code")
    approval = _Approval(action_id="merge-1")
    decision = _Decision(
        allowed_now=True,
        requires_human_approval=False,
        reason="matching action-specific approval",
    )

    result = evaluate_case(
        action_scope_case(
            intent,
            approval,
            decision,
            input_ref="github:pull:4",
            evidence_refs=("github:pull:4",),
            expect_allowed=True,
            expect_human_approval=False,
        )
    )

    assert result.passed is True


def test_pr4_adapter_catches_blanket_approval_drift():
    intent = _Intent(action_id="payment-2", kind="payment")
    approval = _Approval(action_id="all-future-actions")
    fail_open_decision = _Decision(
        allowed_now=True,
        requires_human_approval=False,
        reason="generic human approval recorded",
    )

    result = evaluate_case(
        action_scope_case(
            intent,
            approval,
            fail_open_decision,
            input_ref="github:pull:4:historical-regression",
            evidence_refs=("github:pull:4",),
            expect_allowed=False,
            expect_human_approval=True,
        )
    )

    assert result.passed is False
    assert result.failed_assertion_ids == (
        "allowed-state-matches-policy",
        "human-gate-state-matches-policy",
    )
