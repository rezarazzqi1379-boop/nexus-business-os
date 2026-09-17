"""NEXUS Coordination Kit v0.2: git-derived, independently verifiable handoff
packages for Claude Code <-> ChatGPT/NEXUS coordination.

Reuses task_handoff.py's constants and patterns (SAFE_ID/SHA_HEX validation,
OWNERS/RISK_CLASSES, HandoffConflict, canonical_digest, the atomic
write-then-os.replace pattern) rather than duplicating them. It does not
modify task_handoff.py or its v1 schema -- v1 stays exactly as already
reviewed and accepted; this module adds a v2 package format alongside it.

Note on ``cross_project_touch``: task_handoff.TaskHandoff.cross_project_touch
is a bool. This v0.2 spec calls for it to be a list (empty if none) --
carrying that field forward unchanged would silently narrow it, so
HandoffPackageV2 defines its own ``cross_project_touch: tuple[str, ...]``
(a list of affected project_ids) rather than reusing the v1 field or
retroactively changing v1's already-accepted schema.

Every fact in a HandoffPackageV2 is derived FROM the actual git repository by
``capture_git_facts()`` -- never typed by an AI. All git calls use a fixed
argv list via subprocess with shell=False; no shell string is ever built by
interpolating repo content. A secret-leakage guard scans the actual diff text
before any package is written and refuses (raising, printing a warning) if
anything matches a known secret shape. Test evidence is bound to the exact
HEAD it was captured against and is rejected if the repository has since
moved on -- there is no code path here that parses free-form test-runner
prose into trusted evidence; callers must supply already-structured
``TestEvidenceV2`` values.

Peer-AI handoff text (next_deterministic_action, claims, reasons, etc.) is
always inert data. Nothing in this module calls eval, exec, or subprocess
with content taken from a received package -- every subprocess call here
uses a hardcoded git argv list, never a field from a HandoffPackageV2.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar, Mapping, Sequence

from approvals import ApprovalRequest, ApprovalStore
from contracts import canonical_digest
from task_handoff import HandoffConflict, OWNERS, RISK_CLASSES, SAFE_ID, SHA_HEX, STATES, _safe_id, _sha, utc_now

SCHEMA_VERSION = "nexus.handoff-package.v2"
REVIEW_STATUSES = frozenset({"PENDING", "APPROVED", "REJECTED", "STALE", "SUPERSEDED"})
VERIFICATION_STATUSES = frozenset({"VERIFIED", "STALE", "CONFLICT", "INVALID"})
OWNERSHIP_EVENTS = frozenset({"RELEASE", "TRANSFER"})
EVIDENCE_PROVENANCE_STATES = frozenset({"CALLER_DECLARED", "INDEPENDENTLY_CAPTURED"})
DEFAULT_REVIEW_ROUND_BUDGET = 2
EXTRA_REVIEW_ROUND_ACTION = "coordination_kit.extra_review_round"
EXTRA_REVIEW_ROUND_PROJECT = "coordination_kit"


# ---------------------------------------------------------------------------
# 1. Git-derived facts
# ---------------------------------------------------------------------------

class AmbiguousRepoState(ValueError):
    """The repository is in a state a handoff cannot be honestly generated from
    (detached HEAD, unmerged/conflicted paths, or git itself refusing a query)."""


def _run_git(args: Sequence[str], cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        raise RuntimeError(f"git_command_failed:{' '.join(args)}:{result.stderr.strip()}")
    return result.stdout.strip()


def _run_git_allow_fail(args: Sequence[str], cwd: Path) -> tuple[int, str, str]:
    result = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, shell=False)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


@dataclass(frozen=True)
class GitFacts:
    branch: str
    head_sha: str
    remote_ref: str | None
    remote_head_sha: str | None
    merge_base_sha: str | None
    ahead_by: int
    behind_by: int
    changed_files: tuple[str, ...]
    file_statuses: Mapping[str, str]
    diff_stat: str
    worktree_clean: bool
    untracked_files: tuple[str, ...]
    generated_at: str

    @property
    def diff_digest(self) -> str:
        return canonical_digest({
            "changed_files": list(self.changed_files),
            "file_statuses": dict(self.file_statuses),
            "diff_stat": self.diff_stat,
        })


def capture_git_facts(repo_root: Path, *, base_ref: str = "main") -> GitFacts:
    """Every field here comes from an actual git query against ``repo_root`` -- nothing is
    supplied by the caller. Raises AmbiguousRepoState rather than guessing for a detached
    HEAD or unmerged/conflicted paths.
    """
    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo_root)
    if branch == "HEAD":
        raise AmbiguousRepoState("detached_head")
    head_sha = _run_git(["rev-parse", "HEAD"], repo_root)

    status_code, status_out, status_err = _run_git_allow_fail(["status", "--porcelain=v2", "--branch"], repo_root)
    if status_code != 0:
        raise AmbiguousRepoState(f"git_status_failed:{status_err}")
    lines = status_out.splitlines()
    if any(line.startswith("u ") for line in lines):
        raise AmbiguousRepoState("unmerged_paths")
    worktree_clean = not any(line and not line.startswith("#") for line in lines)
    untracked_files = tuple(sorted(line[2:].strip() for line in lines if line.startswith("? ")))

    remote_code, remote_ref_out, _ = _run_git_allow_fail(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], repo_root)
    remote_ref = remote_ref_out if remote_code == 0 and remote_ref_out else None
    remote_head_sha = _run_git(["rev-parse", remote_ref], repo_root) if remote_ref else None

    merge_base_code, merge_base_out, _ = _run_git_allow_fail(["merge-base", "HEAD", base_ref], repo_root)
    merge_base_sha = merge_base_out if merge_base_code == 0 and merge_base_out else None

    ahead_by = behind_by = 0
    if remote_ref:
        counts = _run_git(["rev-list", "--left-right", "--count", f"HEAD...{remote_ref}"], repo_root)
        parts = counts.split()
        if len(parts) == 2:
            ahead_by, behind_by = int(parts[0]), int(parts[1])

    diff_base = merge_base_sha or base_ref
    name_status = _run_git(["diff", "--name-status", diff_base, "HEAD"], repo_root)
    file_statuses: dict[str, str] = {}
    for line in name_status.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        file_statuses[parts[-1]] = parts[0][0]
    changed_files = tuple(sorted(file_statuses))
    diff_stat = _run_git(["diff", "--stat", diff_base, "HEAD"], repo_root)

    return GitFacts(
        branch=branch, head_sha=head_sha, remote_ref=remote_ref, remote_head_sha=remote_head_sha,
        merge_base_sha=merge_base_sha, ahead_by=ahead_by, behind_by=behind_by, changed_files=changed_files,
        file_statuses=file_statuses, diff_stat=diff_stat, worktree_clean=worktree_clean,
        untracked_files=untracked_files, generated_at=utc_now(),
    )


# ---------------------------------------------------------------------------
# 2. Secret-leakage guard
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(?:api[_-]?key|secret|token|password)['\"]?\s*[:=]\s*['\"][A-Za-z0-9_\-/+]{16,}['\"]"),
    re.compile(r"[A-Za-z0-9+/]{60,}={0,2}"),
)


class SecretLeakageDetected(ValueError):
    def __init__(self, findings: Sequence[str]):
        super().__init__("secret_pattern_detected_in_diff:" + ",".join(findings))
        self.findings = tuple(findings)


def scan_diff_for_secrets(diff_text: str) -> tuple[str, ...]:
    """Returns the (deduplicated) pattern names that matched. Empty means clean."""
    findings = []
    for index, pattern in enumerate(_SECRET_PATTERNS):
        if pattern.search(diff_text):
            findings.append(f"secret_pattern_{index}")
    return tuple(findings)


# ---------------------------------------------------------------------------
# 3. HEAD-bound test evidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TestEvidenceV2:
    # This is a domain record, not a pytest test container.
    __test__: ClassVar[bool] = False
    """Evidence must be constructed from already-structured fields the caller obtained by
    actually running the command and reading its own exit code/counts -- there is no function
    in this module that parses free-form test-runner text into trusted evidence.

    ``provenance`` has no default: a caller must be explicit about which of the two it is.
    ``CALLER_DECLARED`` means the caller asserts these fields (including head_sha) themselves --
    this module cannot verify the command was actually run. ``INDEPENDENTLY_CAPTURED`` means
    head_sha was derived by this module's own capture_test_evidence(), not supplied by the
    caller -- it still trusts the caller's counts/exit_code (nothing here re-runs an arbitrary
    command), but at least binds them to a freshly, independently observed HEAD.
    """

    command: str
    exit_code: int
    passed: int
    failed: int
    errors: int
    skipped: int
    head_sha: str
    provenance: str

    def validate(self) -> None:
        if not self.command.strip():
            raise ValueError("invalid_test_command")
        for value in (self.exit_code, self.passed, self.failed, self.errors, self.skipped):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("invalid_test_evidence_count")
        _sha(self.head_sha, "test_head_sha")
        if self.provenance not in EVIDENCE_PROVENANCE_STATES:
            raise ValueError("invalid_evidence_provenance")


def capture_test_evidence(repo_root: Path, *, command: str, exit_code: int, passed: int, failed: int,
                          errors: int, skipped: int, base_ref: str = "main") -> TestEvidenceV2:
    """The only way to produce INDEPENDENTLY_CAPTURED evidence: head_sha comes from an actual
    git query against ``repo_root`` at the moment of capture, never from the caller's say-so.
    """
    facts = capture_git_facts(repo_root, base_ref=base_ref)
    return TestEvidenceV2(command=command, exit_code=exit_code, passed=passed, failed=failed, errors=errors,
                          skipped=skipped, head_sha=facts.head_sha, provenance="INDEPENDENTLY_CAPTURED")

    def is_current_for(self, current_head_sha: str) -> bool:
        return self.head_sha == current_head_sha


# ---------------------------------------------------------------------------
# 4. Handoff package v2 schema
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HandoffPackageV2:
    task_id: str
    owner: str
    branch: str
    base_sha: str
    head_sha: str
    state: str
    risk_class: str
    review_round: int
    protected_action_required: bool
    next_deterministic_action: str
    generated_from_git: bool
    remote_ref: str | None
    remote_head_sha: str | None
    ahead_by: int
    behind_by: int
    worktree_clean: bool
    untracked_files: tuple[str, ...]
    diff_digest: str
    test_head_sha: str
    authority_refs: tuple[str, ...]
    review_status: str
    reviewed_head_sha: str | None
    supersedes_handoff_digest: str | None
    project_id: str | None = None
    lane_id: str | None = None
    cross_project_touch: tuple[str, ...] = ()
    files_changed: tuple[str, ...] = ()
    tests_run: tuple[TestEvidenceV2, ...] = ()
    claims: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    extra_round_approval_id: str | None = None
    created_at: str = field(default_factory=utc_now)
    schema_version: str = SCHEMA_VERSION

    def validate(self) -> None:
        _safe_id(self.task_id, "task_id")
        if self.owner not in OWNERS:
            raise ValueError("invalid_owner")
        if not self.branch.strip():
            raise ValueError("invalid_branch")
        _sha(self.base_sha, "base_sha")
        _sha(self.head_sha, "head_sha")
        if self.state not in STATES:
            raise ValueError("invalid_state")
        if self.risk_class not in RISK_CLASSES:
            raise ValueError("invalid_risk_class")
        if isinstance(self.review_round, bool) or not isinstance(self.review_round, int) or self.review_round < 1:
            raise ValueError("invalid_review_round")
        if self.review_round > DEFAULT_REVIEW_ROUND_BUDGET:
            if not self.extra_round_approval_id or not self.extra_round_approval_id.strip():
                raise ValueError("review_round_exceeds_budget_without_human_authorization")
        if not isinstance(self.protected_action_required, bool):
            raise ValueError("invalid_protected_action_required")
        if not self.next_deterministic_action.strip():
            raise ValueError("invalid_next_deterministic_action")
        if not isinstance(self.generated_from_git, bool) or not self.generated_from_git:
            raise ValueError("package_must_be_generated_from_git")
        if self.remote_head_sha is not None:
            _sha(self.remote_head_sha, "remote_head_sha")
        if isinstance(self.ahead_by, bool) or not isinstance(self.ahead_by, int) or self.ahead_by < 0:
            raise ValueError("invalid_ahead_by")
        if isinstance(self.behind_by, bool) or not isinstance(self.behind_by, int) or self.behind_by < 0:
            raise ValueError("invalid_behind_by")
        if not isinstance(self.worktree_clean, bool):
            raise ValueError("invalid_worktree_clean")
        if not self.diff_digest.strip():
            raise ValueError("invalid_diff_digest")
        _sha(self.test_head_sha, "test_head_sha")
        if self.test_head_sha != self.head_sha:
            raise ValueError("test_head_sha_must_match_head_sha")
        if self.review_status not in REVIEW_STATUSES:
            raise ValueError("invalid_review_status")
        if self.reviewed_head_sha is not None:
            _sha(self.reviewed_head_sha, "reviewed_head_sha")
        if len(set(self.cross_project_touch)) != len(self.cross_project_touch):
            raise ValueError("duplicate_cross_project_touch")
        if len(set(self.files_changed)) != len(self.files_changed):
            raise ValueError("duplicate_files_changed")
        for test in self.tests_run:
            test.validate()
            if test.head_sha != self.head_sha:
                raise ValueError("test_evidence_head_mismatch")

    def to_digest_payload(self) -> dict:
        return asdict(self)

    @property
    def digest(self) -> str:
        self.validate()
        return canonical_digest(self.to_digest_payload())


def convert_v1_cross_project_touch(v1_cross_project_touch: bool) -> tuple[str, ...]:
    """task_handoff.TaskHandoff.cross_project_touch is a bool; HandoffPackageV2's is a list of
    project_ids. False converts safely to (). True does NOT convert to a specific project list
    -- a boolean carries no project identity, and inventing one would be exactly the kind of
    guess this codebase's evidence discipline forbids. Callers with a v1 record whose
    cross_project_touch is True must supply the real affected project_ids themselves (as their
    own ``cross_project_touch=(...)`` argument to generate_handoff_package); this function
    fails closed rather than silently discarding the signal or fabricating identities.
    """
    if not isinstance(v1_cross_project_touch, bool):
        raise ValueError("invalid_v1_cross_project_touch")
    if v1_cross_project_touch:
        raise ValueError(
            "cross_project_touch_unknown_fail_closed:v1_true_requires_explicit_project_ids"
        )
    return ()


def request_extra_review_round(store: ApprovalStore, *, task_id: str, head_sha: str, review_round: int,
                               requested_by: str) -> str:
    """Request an extra round; this module never decides its own request.

    ``decided_by`` in :class:`ApprovalStore` is claimed audit metadata, not
    authenticated actor identity.  Deployments needing identity proof must add
    an authenticated actor primitive outside this kit.
    """
    request = ApprovalRequest(
        project_id=EXTRA_REVIEW_ROUND_PROJECT, action=EXTRA_REVIEW_ROUND_ACTION, target=task_id,
        parameters={"head_sha": head_sha, "review_round": review_round}, requested_by=requested_by,
    )
    return store.request(request)


def consume_extra_review_round_approval(store: ApprovalStore, *, approval_id: str, task_id: str,
                                        head_sha: str, review_round: int) -> bool:
    """Fail closed unless an exact approval claims ``decided_by='human'``.

    That string is metadata only and is not proof of actor identity.  The check
    prevents accidental/non-human-labelled grants; it does not replace an
    authenticated approval service.
    Single-use: a second call for the same approval_id returns False. A fabricated/unknown
    approval_id (ApprovalStore.consume raises KeyError for those) is treated identically to an
    unapproved one -- both simply mean "not a valid, human-decided approval".
    """
    action_digest = ApprovalRequest(
        project_id=EXTRA_REVIEW_ROUND_PROJECT, action=EXTRA_REVIEW_ROUND_ACTION, target=task_id,
        parameters={"head_sha": head_sha, "review_round": review_round}, requested_by="",
    ).action_digest
    record = store.get(approval_id)
    if record is None or record["status"] != "approved":
        return False
    if record["action_digest"] != action_digest or record["decided_by"] != "human":
        return False
    try:
        return store.consume(approval_id, action_digest=action_digest)
    except KeyError:
        return False


def generate_handoff_package(
    repo_root: Path, *, task_id: str, owner: str, state: str, risk_class: str, review_round: int,
    protected_action_required: bool, next_deterministic_action: str, project_id: str | None = None,
    lane_id: str | None = None, cross_project_touch: Sequence[str] = (), claims: Sequence[str] = (),
    evidence_refs: Sequence[str] = (), unknowns: Sequence[str] = (), tests: Sequence[TestEvidenceV2] = (),
    authority_refs: Sequence[str] = (), review_status: str = "PENDING", reviewed_head_sha: str | None = None,
    supersedes_handoff_digest: str | None = None, extra_round_approval_id: str | None = None,
    approval_store: ApprovalStore | None = None, base_ref: str = "main",
) -> HandoffPackageV2:
    """Captures real git facts, scans the real diff for secrets (refusing to proceed if any
    are found), rejects any supplied test evidence not bound to the current HEAD, and returns
    a fully validated HandoffPackageV2. Never writes anything by itself -- pass the result to
    HandoffStoreV2.claim()/.update() to persist it.

    For review_round > 2, ``extra_round_approval_id`` must name an exact,
    single-use grant whose caller-claimed ``decided_by`` metadata is ``human``.
    This repository has no actor-authentication primitive, so this is not an
    identity attestation and must not be represented as one.
    """
    facts = capture_git_facts(repo_root, base_ref=base_ref)
    diff_base = facts.merge_base_sha or base_ref
    full_diff = _run_git(["diff", diff_base, "HEAD"], repo_root)
    findings = scan_diff_for_secrets(full_diff)
    if findings:
        print(f"WARNING: refusing to generate handoff package for {task_id!r} -- "
              f"secret-like pattern(s) detected in diff: {findings}")
        raise SecretLeakageDetected(findings)

    for test in tests:
        test.validate()
        if test.head_sha != facts.head_sha:
            raise ValueError(f"stale_test_evidence:test_head={test.head_sha}:actual_head={facts.head_sha}")

    if review_round > DEFAULT_REVIEW_ROUND_BUDGET:
        if approval_store is None or not extra_round_approval_id:
            raise ValueError("extra_review_round_requires_a_consumed_human_approval")
        consumed = consume_extra_review_round_approval(
            approval_store, approval_id=extra_round_approval_id, task_id=task_id,
            head_sha=facts.head_sha, review_round=review_round,
        )
        if not consumed:
            raise ValueError("extra_review_round_approval_invalid_or_not_human_decided")

    package = HandoffPackageV2(
        task_id=task_id, owner=owner, branch=facts.branch, base_sha=diff_base, head_sha=facts.head_sha,
        state=state, risk_class=risk_class, review_round=review_round,
        protected_action_required=protected_action_required, next_deterministic_action=next_deterministic_action,
        generated_from_git=True, remote_ref=facts.remote_ref, remote_head_sha=facts.remote_head_sha,
        ahead_by=facts.ahead_by, behind_by=facts.behind_by, worktree_clean=facts.worktree_clean,
        untracked_files=facts.untracked_files, diff_digest=facts.diff_digest, test_head_sha=facts.head_sha,
        authority_refs=tuple(authority_refs), review_status=review_status, reviewed_head_sha=reviewed_head_sha,
        supersedes_handoff_digest=supersedes_handoff_digest, project_id=project_id, lane_id=lane_id,
        cross_project_touch=tuple(cross_project_touch), files_changed=facts.changed_files,
        tests_run=tuple(tests), claims=tuple(claims), evidence_refs=tuple(evidence_refs),
        unknowns=tuple(unknowns), extra_round_approval_id=extra_round_approval_id,
    )
    package.validate()
    return package


# ---------------------------------------------------------------------------
# 5. Verifier
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VerificationResult:
    status: str
    reasons: tuple[str, ...]

    def validate(self) -> None:
        if self.status not in VERIFICATION_STATUSES:
            raise ValueError("invalid_verification_status")


def verify_handoff_package(package: HandoffPackageV2, stored_digest: str, repo_root: Path,
                          *, base_ref: str = "main",
                          approval_store: ApprovalStore | None = None) -> VerificationResult:
    """Independently recomputes everything a received package claims, against the actual
    local repository -- never trusts the package's own say-so. Never touches
    ``next_deterministic_action`` or any other field as executable content.
    """
    try:
        package.validate()
    except ValueError as exc:
        return VerificationResult("INVALID", (f"package_failed_self_validation:{exc}",))

    if stored_digest != package.digest:
        return VerificationResult("INVALID", ("package_digest_mismatch",))

    if package.review_round > DEFAULT_REVIEW_ROUND_BUDGET:
        if approval_store is None or not package.extra_round_approval_id:
            return VerificationResult("INVALID", ("over_budget_approval_not_verifiable",))
        record = approval_store.get(package.extra_round_approval_id)
        expected_digest = ApprovalRequest(
            project_id=EXTRA_REVIEW_ROUND_PROJECT,
            action=EXTRA_REVIEW_ROUND_ACTION,
            target=package.task_id,
            parameters={"head_sha": package.head_sha, "review_round": package.review_round},
            requested_by="",
        ).action_digest
        if (
            record is None
            or record["status"] != "consumed"
            or record["action_digest"] != expected_digest
            or record["decided_by"] != "human"
        ):
            return VerificationResult("INVALID", ("over_budget_approval_record_invalid",))

    branch_code, _, _ = _run_git_allow_fail(["rev-parse", "--verify", package.branch], repo_root)
    if branch_code != 0:
        return VerificationResult("INVALID", ("branch_does_not_exist",))

    head_code, actual_head, _ = _run_git_allow_fail(["rev-parse", package.branch], repo_root)
    if head_code != 0:
        return VerificationResult("INVALID", ("cannot_resolve_branch_head",))
    if actual_head != package.head_sha:
        return VerificationResult("STALE", (f"stated_head={package.head_sha}:actual_head={actual_head}",))

    base_code, _, _ = _run_git_allow_fail(["cat-file", "-e", package.base_sha], repo_root)
    if base_code != 0:
        return VerificationResult("INVALID", ("base_sha_does_not_exist",))

    name_status_code, name_status, _ = _run_git_allow_fail(
        ["diff", "--name-status", package.base_sha, package.head_sha], repo_root)
    if name_status_code != 0:
        return VerificationResult("INVALID", ("cannot_compute_actual_diff",))
    actual_file_statuses = {
        line.split("\t")[-1]: line.split("\t")[0][0] for line in name_status.splitlines() if line.strip()
    }
    actual_files = tuple(sorted(actual_file_statuses))
    if actual_files != tuple(sorted(package.files_changed)):
        return VerificationResult("CONFLICT", (
            f"declared_files={sorted(package.files_changed)}:actual_files={list(actual_files)}",
        ))

    diff_stat = _run_git(["diff", "--stat", package.base_sha, package.head_sha], repo_root)
    actual_digest = canonical_digest({
        "changed_files": list(actual_files), "file_statuses": actual_file_statuses, "diff_stat": diff_stat,
    })
    if actual_digest != package.diff_digest:
        return VerificationResult("CONFLICT", (f"diff_digest_mismatch:{package.diff_digest}!={actual_digest}",))

    reasons: list[str] = []
    if package.remote_ref:
        remote_code, remote_head, _ = _run_git_allow_fail(["rev-parse", package.remote_ref], repo_root)
        if remote_code == 0 and remote_head and remote_head != package.remote_head_sha:
            reasons.append(f"remote_head_drifted:{package.remote_head_sha}!={remote_head}")

    for test in package.tests_run:
        if test.head_sha != package.head_sha:
            return VerificationResult("INVALID", (f"test_evidence_not_bound_to_package_head:{test.head_sha}",))

    if reasons:
        return VerificationResult("STALE", tuple(reasons))
    return VerificationResult("VERIFIED", ())


# ---------------------------------------------------------------------------
# 6. Ownership safety
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OwnershipEvent:
    task_id: str
    event: str
    released_by: str
    released_at: str
    new_owner: str | None = None

    def validate(self) -> None:
        _safe_id(self.task_id, "task_id")
        if self.event not in OWNERSHIP_EVENTS:
            raise ValueError("invalid_ownership_event")
        if self.released_by not in OWNERS:
            raise ValueError("invalid_released_by")
        if self.event == "TRANSFER" and (self.new_owner is None or self.new_owner not in OWNERS):
            raise ValueError("transfer_requires_a_valid_new_owner")
        if self.event == "RELEASE" and self.new_owner is not None:
            raise ValueError("release_must_not_name_a_new_owner")


# ---------------------------------------------------------------------------
# 8. Shared exchange (repository-backed only)
# ---------------------------------------------------------------------------

def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


class HandoffStoreV2:
    """File-backed only: .nexus/handoffs/, .nexus/reviews/, .nexus/evidence/. No database, no
    queue, no webhook, no message bus, no autonomous polling loop -- reading/writing these
    files IS the exchange.
    """

    def __init__(self, root: Path) -> None:
        self.handoffs_dir = (root / ".nexus" / "handoffs").resolve()
        self.reviews_dir = (root / ".nexus" / "reviews").resolve()
        self.evidence_dir = (root / ".nexus" / "evidence").resolve()
        for directory in (self.handoffs_dir, self.reviews_dir, self.evidence_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def _package_path(self, task_id: str) -> Path:
        return self.handoffs_dir / f"{_safe_id(task_id, 'task_id')}.v2.json"

    def _release_path(self, task_id: str) -> Path:
        return self.handoffs_dir / f"{_safe_id(task_id, 'task_id')}.release.json"

    def read(self, task_id: str) -> HandoffPackageV2 | None:
        path = self._package_path(task_id)
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw.pop("digest", None)
        raw["tests_run"] = tuple(TestEvidenceV2(**item) for item in raw.get("tests_run", ()))
        for key in ("untracked_files", "authority_refs", "cross_project_touch", "files_changed",
                   "claims", "evidence_refs", "unknowns"):
            raw[key] = tuple(raw.get(key, ()))
        return HandoffPackageV2(**raw)

    def _read_release(self, task_id: str) -> OwnershipEvent | None:
        path = self._release_path(task_id)
        if not path.exists():
            return None
        return OwnershipEvent(**json.loads(path.read_text(encoding="utf-8")))

    def release_ownership(self, event: OwnershipEvent) -> Path:
        """Only the current owner may release or transfer their own task."""
        event.validate()
        existing = self.read(event.task_id)
        if existing is None:
            raise KeyError("unknown_task_handoff")
        if existing.owner != event.released_by:
            raise HandoffConflict(f"only_current_owner_can_release_or_transfer:{existing.owner}")
        path = self._release_path(event.task_id)
        _atomic_write(path, json.dumps(asdict(event), ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        return path

    def claim(self, package: HandoffPackageV2) -> Path:
        """BLOCKED is never itself takeover-eligible: a different owner may only claim a task
        that is DONE, or for which the current owner has explicitly recorded a RELEASE (any
        new owner) or a TRANSFER naming this exact new owner.
        """
        package.validate()
        existing = self.read(package.task_id)
        if existing is not None and existing.owner != package.owner:
            if existing.state != "DONE":
                release = self._read_release(package.task_id)
                if release is None:
                    raise HandoffConflict(
                        f"task_not_released_owner={existing.owner}:state={existing.state}"
                    )
                if release.event == "TRANSFER" and release.new_owner != package.owner:
                    raise HandoffConflict(f"task_transferred_to_different_owner:{release.new_owner}")
        return self._write(package)

    def update(self, package: HandoffPackageV2) -> Path:
        package.validate()
        existing = self.read(package.task_id)
        if existing is None:
            raise KeyError("unknown_task_handoff")
        if existing.owner != package.owner:
            raise HandoffConflict(f"task_owned_by:{existing.owner}")
        return self._write(package)

    def _write(self, package: HandoffPackageV2) -> Path:
        path = self._package_path(package.task_id)
        payload = asdict(package)
        payload["digest"] = package.digest
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        _atomic_write(path, text)
        return path

    def write_review(self, task_id: str, round_index: int, reviewer: str, decision: dict) -> Path:
        path = self.reviews_dir / f"{_safe_id(task_id, 'task_id')}__round{round_index}.json"
        payload = {"task_id": task_id, "round_index": round_index, "reviewer": reviewer,
                  "decision": decision, "recorded_at": utc_now()}
        _atomic_write(path, json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        return path

    def write_evidence(self, task_id: str, head_sha: str, tests: Sequence[TestEvidenceV2]) -> Path:
        for test in tests:
            test.validate()
        path = self.evidence_dir / f"{_safe_id(task_id, 'task_id')}__{head_sha}.json"
        payload = {"task_id": task_id, "head_sha": head_sha, "tests": [asdict(t) for t in tests],
                  "recorded_at": utc_now()}
        _atomic_write(path, json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        return path
