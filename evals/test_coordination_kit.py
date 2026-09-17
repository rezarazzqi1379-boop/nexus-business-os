from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from coordination_kit import (
    AmbiguousRepoState,
    GitFacts,
    HandoffPackageV2,
    HandoffStoreV2,
    OwnershipEvent,
    SecretLeakageDetected,
    TestEvidenceV2,
    VerificationResult,
    capture_git_facts,
    capture_test_evidence,
    consume_extra_review_round_approval,
    convert_v1_cross_project_touch,
    generate_handoff_package,
    request_extra_review_round,
    scan_diff_for_secrets,
    verify_handoff_package,
)
from approvals import ApprovalRequest, ApprovalStore
from task_handoff import HandoffConflict

SHA_ZEROS = "0" * 40


def _git(args, cwd) -> str:
    result = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, shell=False)
    if result.returncode != 0:
        raise RuntimeError(f"git failed: {args}: {result.stderr}")
    return result.stdout.strip()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class _TempRepo:
    """A real, throwaway git repository -- never the project repo -- so
    capture_git_facts()/verify_handoff_package() are exercised against actual git behavior.
    """

    def __enter__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(["init", "-q"], self.root)
        _git(["config", "user.email", "test@example.invalid"], self.root)
        _git(["config", "user.name", "Test User"], self.root)
        _write(self.root / "README.md", "hello\n")
        _git(["add", "README.md"], self.root)
        _git(["commit", "-q", "-m", "initial commit"], self.root)
        _git(["branch", "-m", "main"], self.root)
        return self

    def __exit__(self, *exc):
        bare_tmp = getattr(self, "_bare_tmp", None)
        if bare_tmp is not None:
            bare_tmp.cleanup()
        self._tmp.cleanup()

    def new_branch(self, name: str) -> None:
        _git(["checkout", "-q", "-b", name], self.root)

    def commit_file(self, relpath: str, content: str, message: str = "change") -> str:
        _write(self.root / relpath, content)
        _git(["add", relpath], self.root)
        _git(["commit", "-q", "-m", message], self.root)
        return _git(["rev-parse", "HEAD"], self.root)

    def head(self) -> str:
        return _git(["rev-parse", "HEAD"], self.root)

    def add_bare_remote(self) -> Path:
        bare_tmp = tempfile.TemporaryDirectory()
        self._bare_tmp = bare_tmp  # keep alive
        bare_path = Path(bare_tmp.name)
        _git(["init", "-q", "--bare"], bare_path)
        _git(["remote", "add", "origin", str(bare_path)], self.root)
        return bare_path

    def push(self, branch: str = "main") -> None:
        _git(["push", "-q", "-u", "origin", branch], self.root)


def evidence(head_sha: str, **changes) -> TestEvidenceV2:
    values = dict(command="pytest -q", exit_code=0, passed=10, failed=0, errors=0, skipped=0, head_sha=head_sha,
                 provenance="CALLER_DECLARED")
    values.update(changes)
    return TestEvidenceV2(**values)


class GitFactsAcceptanceTests(unittest.TestCase):
    def test_generator_captures_real_git_head(self):
        with _TempRepo() as repo:
            repo.add_bare_remote()
            repo.push("main")
            facts = capture_git_facts(repo.root, base_ref="main")
            self.assertEqual(facts.head_sha, repo.head())
            self.assertEqual(facts.branch, "main")

    def test_dirty_worktree_is_honestly_represented(self):
        with _TempRepo() as repo:
            repo.add_bare_remote()
            repo.push("main")
            _write(repo.root / "scratch.txt", "uncommitted")
            facts = capture_git_facts(repo.root, base_ref="main")
            self.assertFalse(facts.worktree_clean)

    def test_clean_worktree_is_honestly_represented(self):
        with _TempRepo() as repo:
            repo.add_bare_remote()
            repo.push("main")
            facts = capture_git_facts(repo.root, base_ref="main")
            self.assertTrue(facts.worktree_clean)

    def test_untracked_files_are_honestly_represented(self):
        with _TempRepo() as repo:
            repo.add_bare_remote()
            repo.push("main")
            _write(repo.root / "not_added_yet.txt", "x")
            facts = capture_git_facts(repo.root, base_ref="main")
            self.assertIn("not_added_yet.txt", facts.untracked_files)

    def test_hidden_changed_file_is_detected(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            repo.commit_file("b.txt", "b", "add b (hidden if only a.txt were declared)")
            facts = capture_git_facts(repo.root, base_ref="main")
            self.assertIn("a.txt", facts.changed_files)
            self.assertIn("b.txt", facts.changed_files)

    def test_diff_digest_changes_when_diff_changes(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            facts_before = capture_git_facts(repo.root, base_ref="main")
            repo.commit_file("b.txt", "b", "add b")
            facts_after = capture_git_facts(repo.root, base_ref="main")
            self.assertNotEqual(facts_before.diff_digest, facts_after.diff_digest)

    def test_stale_remote_state_is_detected_via_ahead_behind(self):
        with _TempRepo() as repo:
            repo.add_bare_remote()
            repo.push("main")
            repo.commit_file("local_only.txt", "x", "local change not pushed")
            facts = capture_git_facts(repo.root, base_ref="main")
            self.assertEqual(facts.ahead_by, 1)
            self.assertNotEqual(facts.remote_head_sha, facts.head_sha)

    def test_detached_head_is_ambiguous(self):
        with _TempRepo() as repo:
            head = repo.head()
            _git(["checkout", "-q", head], repo.root)
            with self.assertRaisesRegex(AmbiguousRepoState, "detached_head"):
                capture_git_facts(repo.root, base_ref="main")


class SecretGuardTests(unittest.TestCase):
    def test_clean_diff_has_no_findings(self):
        self.assertEqual(scan_diff_for_secrets("+def foo():\n+    return 1\n"), ())

    def test_openai_style_key_is_detected(self):
        findings = scan_diff_for_secrets("+API_KEY = 'sk-abcdefghijklmnopqrstuvwx1234'\n")
        self.assertTrue(findings)

    def test_aws_style_key_is_detected(self):
        findings = scan_diff_for_secrets("+aws_key = 'AKIAABCDEFGHIJKLMNOP'\n")
        self.assertTrue(findings)

    def test_secret_pattern_in_diff_blocks_package_generation(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("config.py", "TOKEN = 'sk-abcdefghijklmnopqrstuvwx1234'\n", "add token")
            head = repo.head()
            with self.assertRaises(SecretLeakageDetected):
                generate_handoff_package(
                    repo.root, task_id="task-1", owner="claude-code", state="IN_PROGRESS",
                    risk_class="LOW", review_round=1, protected_action_required=False,
                    next_deterministic_action="continue", base_ref="main",
                    tests=(evidence(head),),
                )

    def test_generation_succeeds_without_secret_patterns(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("clean.py", "def add(a, b):\n    return a + b\n", "add function")
            head = repo.head()
            package = generate_handoff_package(
                repo.root, task_id="task-1", owner="claude-code", state="IN_PROGRESS",
                risk_class="LOW", review_round=1, protected_action_required=False,
                next_deterministic_action="continue", base_ref="main", tests=(evidence(head),),
            )
            self.assertEqual(package.head_sha, head)


class TestEvidenceBindingTests(unittest.TestCase):
    def test_evidence_from_old_head_is_rejected_at_generation(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            old_head = repo.commit_file("a.txt", "a", "add a")
            repo.commit_file("b.txt", "b", "add b")
            with self.assertRaisesRegex(ValueError, "stale_test_evidence"):
                generate_handoff_package(
                    repo.root, task_id="task-1", owner="claude-code", state="IN_PROGRESS",
                    risk_class="LOW", review_round=1, protected_action_required=False,
                    next_deterministic_action="continue", base_ref="main", tests=(evidence(old_head),),
                )

    def test_evidence_matching_current_head_is_accepted(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            head = repo.commit_file("a.txt", "a", "add a")
            package = generate_handoff_package(
                repo.root, task_id="task-1", owner="claude-code", state="IN_PROGRESS",
                risk_class="LOW", review_round=1, protected_action_required=False,
                next_deterministic_action="continue", base_ref="main", tests=(evidence(head),),
            )
            self.assertEqual(package.tests_run[0].head_sha, head)


class VerifierAcceptanceTests(unittest.TestCase):
    def _generate(self, repo, **overrides):
        params = dict(task_id="task-1", owner="claude-code", state="IN_PROGRESS", risk_class="LOW",
                     review_round=1, protected_action_required=False, next_deterministic_action="continue",
                     base_ref="main")
        params.update(overrides)
        head = repo.head()
        return generate_handoff_package(repo.root, tests=(evidence(head),), **params)

    def test_verified_when_everything_matches(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            package = self._generate(repo)
            result = verify_handoff_package(package, package.digest, repo.root, base_ref="main")
            self.assertEqual(result.status, "VERIFIED")

    def test_wrong_supplied_head_fails_verification(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            package = self._generate(repo)
            forged = HandoffPackageV2(**{**package.__dict__, "head_sha": "1" * 40, "test_head_sha": "1" * 40,
                                        "tests_run": ()})
            result = verify_handoff_package(forged, forged.digest, repo.root, base_ref="main")
            self.assertEqual(result.status, "STALE")

    def test_corrupt_package_digest_is_rejected(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            package = self._generate(repo)
            result = verify_handoff_package(package, "not-the-real-digest", repo.root, base_ref="main")
            self.assertEqual(result.status, "INVALID")

    def test_diff_digest_mismatch_is_conflict(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            package = self._generate(repo)
            tampered = HandoffPackageV2(**{**package.__dict__, "diff_digest": "0" * 12})
            result = verify_handoff_package(tampered, tampered.digest, repo.root, base_ref="main")
            self.assertEqual(result.status, "CONFLICT")

    def test_stale_local_state_is_detected_after_head_moves_on(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            package = self._generate(repo)
            repo.commit_file("b.txt", "b", "add b")  # branch tip moves past what the package captured
            result = verify_handoff_package(package, package.digest, repo.root, base_ref="main")
            self.assertEqual(result.status, "STALE")

    def test_stale_remote_drift_is_detected_when_local_head_still_matches(self):
        with _TempRepo() as repo:
            repo.add_bare_remote()
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            repo.push("feature")
            package = self._generate(repo)  # remote_head_sha == current head
            _git(["update-ref", "refs/remotes/origin/feature", repo.commit_file("b.txt", "b", "b commit")],
                 repo.root)
            _git(["reset", "-q", "--hard", package.head_sha], repo.root)  # local stays put
            result = verify_handoff_package(package, package.digest, repo.root, base_ref="main")
            self.assertEqual(result.status, "STALE")

    def test_next_deterministic_action_is_never_executed(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            marker = repo.root / "SHOULD_NOT_EXIST"
            package = self._generate(repo, next_deterministic_action=f"; touch {marker} ; echo pwned")
            verify_handoff_package(package, package.digest, repo.root, base_ref="main")
            self.assertFalse(marker.exists())


class OwnershipSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = HandoffStoreV2(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def _package(self, **overrides) -> HandoffPackageV2:
        values = dict(
            task_id="task-own", owner="claude-code", branch="feat/x", base_sha="a" * 40, head_sha="b" * 40,
            state="IN_PROGRESS", risk_class="LOW", review_round=1, protected_action_required=False,
            next_deterministic_action="continue", generated_from_git=True, remote_ref=None, remote_head_sha=None,
            ahead_by=0, behind_by=0, worktree_clean=True, untracked_files=(), diff_digest="d" * 12,
            test_head_sha="b" * 40, authority_refs=(), review_status="PENDING", reviewed_head_sha=None,
            supersedes_handoff_digest=None,
        )
        values.update(overrides)
        return HandoffPackageV2(**values)

    def test_blocked_does_not_permit_silent_takeover(self):
        self.store.claim(self._package(state="BLOCKED"))
        with self.assertRaises(HandoffConflict):
            self.store.claim(self._package(owner="chatgpt-nexus"))

    def test_explicit_release_permits_takeover(self):
        self.store.claim(self._package(state="BLOCKED"))
        self.store.release_ownership(OwnershipEvent(
            task_id="task-own", event="RELEASE", released_by="claude-code", released_at="2026-09-04T00:00:00+00:00",
        ))
        self.store.claim(self._package(owner="chatgpt-nexus"))  # must not raise
        self.assertEqual(self.store.read("task-own").owner, "chatgpt-nexus")

    def test_transfer_only_permits_the_named_new_owner(self):
        self.store.claim(self._package(state="BLOCKED"))
        self.store.release_ownership(OwnershipEvent(
            task_id="task-own", event="TRANSFER", released_by="claude-code", released_at="2026-09-04T00:00:00+00:00",
            new_owner="human",
        ))
        with self.assertRaises(HandoffConflict):
            self.store.claim(self._package(owner="chatgpt-nexus"))
        self.store.claim(self._package(owner="human"))  # must not raise

    def test_done_permits_next_ownership(self):
        self.store.claim(self._package(state="DONE"))
        self.store.claim(self._package(owner="chatgpt-nexus"))  # must not raise
        self.assertEqual(self.store.read("task-own").owner, "chatgpt-nexus")

    def test_duplicate_claim_by_different_owner_remains_fail_closed(self):
        self.store.claim(self._package(owner="claude-code", state="IN_PROGRESS"))
        with self.assertRaises(HandoffConflict):
            self.store.claim(self._package(owner="chatgpt-nexus", state="IN_PROGRESS"))

    def test_release_can_only_be_recorded_by_current_owner(self):
        self.store.claim(self._package(owner="claude-code", state="BLOCKED"))
        with self.assertRaises(HandoffConflict):
            self.store.release_ownership(OwnershipEvent(
                task_id="task-own", event="RELEASE", released_by="chatgpt-nexus",
                released_at="2026-09-04T00:00:00+00:00",
            ))


class ReviewRoundBudgetTests(unittest.TestCase):
    """A8: extra review rounds require a consumed, human-decided approvals.py grant --
    a caller-set boolean is no longer sufficient authorization.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.approval_store = ApprovalStore(Path(self.temp.name) / "approvals.db")

    def tearDown(self):
        self.temp.cleanup()

    def _package(self, **overrides) -> HandoffPackageV2:
        values = dict(
            task_id="task-round", owner="claude-code", branch="feat/x", base_sha="a" * 40, head_sha="b" * 40,
            state="READY_FOR_REVIEW", risk_class="LOW", review_round=1, protected_action_required=False,
            next_deterministic_action="continue", generated_from_git=True, remote_ref=None, remote_head_sha=None,
            ahead_by=0, behind_by=0, worktree_clean=True, untracked_files=(), diff_digest="d" * 12,
            test_head_sha="b" * 40, authority_refs=(), review_status="PENDING", reviewed_head_sha=None,
            supersedes_handoff_digest=None,
        )
        values.update(overrides)
        return HandoffPackageV2(**values)

    def test_round_one_is_accepted(self):
        self._package(review_round=1).validate()

    def test_round_two_is_accepted(self):
        self._package(review_round=2).validate()

    def test_round_three_is_rejected_without_approval_id(self):
        with self.assertRaisesRegex(ValueError, "review_round_exceeds_budget_without_human_authorization"):
            self._package(review_round=3).validate()

    def test_self_asserted_approval_id_fails_at_generation_not_just_validate(self):
        # validate() alone can only check PRESENCE of the field, not that it was truly granted --
        # that deeper check lives in generate_handoff_package(), proven here.
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            head = repo.head()
            fabricated_id = "apr_" + "0" * 32  # an AI just making up an id, never requested or granted
            with self.assertRaisesRegex(ValueError, "extra_review_round_approval_invalid_or_not_human_decided"):
                generate_handoff_package(
                    repo.root, task_id="task-round", owner="claude-code", state="IN_PROGRESS", risk_class="LOW",
                    review_round=3, protected_action_required=False, next_deterministic_action="continue",
                    base_ref="main", tests=(evidence(head),), extra_round_approval_id=fabricated_id,
                    approval_store=self.approval_store,
                )

    def test_ai_requested_but_undecided_approval_fails_at_generation(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            head = repo.head()
            approval_id = request_extra_review_round(self.approval_store, task_id="task-round", head_sha=head,
                                                      review_round=3, requested_by="claude-code")
            with self.assertRaisesRegex(ValueError, "extra_review_round_approval_invalid_or_not_human_decided"):
                generate_handoff_package(
                    repo.root, task_id="task-round", owner="claude-code", state="IN_PROGRESS", risk_class="LOW",
                    review_round=3, protected_action_required=False, next_deterministic_action="continue",
                    base_ref="main", tests=(evidence(head),), extra_round_approval_id=approval_id,
                    approval_store=self.approval_store,
                )

    def test_approval_decided_for_a_different_scope_does_not_transfer(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            head = repo.head()
            approval_id = request_extra_review_round(self.approval_store, task_id="task-round", head_sha=head,
                                                      review_round=3, requested_by="claude-code")
            self.approval_store.decide(approval_id, approved=True, decided_by="human")
            wrong_scope_ok = consume_extra_review_round_approval(
                self.approval_store, approval_id=approval_id, task_id="task-round", head_sha="f" * 40,
                review_round=3,
            )
            self.assertFalse(wrong_scope_ok)

    def test_genuinely_human_decided_approval_allows_generation(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            head = repo.head()
            approval_id = request_extra_review_round(self.approval_store, task_id="task-round", head_sha=head,
                                                      review_round=3, requested_by="claude-code")
            self.approval_store.decide(approval_id, approved=True, decided_by="human")
            package = generate_handoff_package(
                repo.root, task_id="task-round", owner="claude-code", state="IN_PROGRESS", risk_class="LOW",
                review_round=3, protected_action_required=False, next_deterministic_action="continue",
                base_ref="main", tests=(evidence(head),), extra_round_approval_id=approval_id,
                approval_store=self.approval_store,
            )
            self.assertEqual(package.review_round, 3)

    def test_approval_is_single_use(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            head = repo.head()
            approval_id = request_extra_review_round(self.approval_store, task_id="task-round", head_sha=head,
                                                      review_round=3, requested_by="claude-code")
            self.approval_store.decide(approval_id, approved=True, decided_by="human")
            generate_handoff_package(
                repo.root, task_id="task-round", owner="claude-code", state="IN_PROGRESS", risk_class="LOW",
                review_round=3, protected_action_required=False, next_deterministic_action="continue",
                base_ref="main", tests=(evidence(head),), extra_round_approval_id=approval_id,
                approval_store=self.approval_store,
            )
            with self.assertRaises(ValueError):
                generate_handoff_package(
                    repo.root, task_id="task-round", owner="claude-code", state="IN_PROGRESS", risk_class="LOW",
                    review_round=3, protected_action_required=False, next_deterministic_action="continue",
                    base_ref="main", tests=(evidence(head),), extra_round_approval_id=approval_id,
                    approval_store=self.approval_store,
                )

    def test_non_human_claimed_decider_is_rejected(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            head = repo.head()
            approval_id = request_extra_review_round(
                self.approval_store, task_id="task-round", head_sha=head,
                review_round=3, requested_by="claude-code",
            )
            self.approval_store.decide(approval_id, approved=True, decided_by="agent")
            with self.assertRaisesRegex(ValueError, "extra_review_round_approval_invalid"):
                generate_handoff_package(
                    repo.root, task_id="task-round", owner="claude-code",
                    state="IN_PROGRESS", risk_class="LOW", review_round=3,
                    protected_action_required=False,
                    next_deterministic_action="continue", base_ref="main",
                    tests=(evidence(head),), extra_round_approval_id=approval_id,
                    approval_store=self.approval_store,
                )

    def test_over_budget_verification_requires_approval_store(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            repo.commit_file("a.txt", "a", "add a")
            head = repo.head()
            approval_id = request_extra_review_round(
                self.approval_store, task_id="task-round", head_sha=head,
                review_round=3, requested_by="claude-code",
            )
            self.approval_store.decide(approval_id, approved=True, decided_by="human")
            package = generate_handoff_package(
                repo.root, task_id="task-round", owner="claude-code",
                state="IN_PROGRESS", risk_class="LOW", review_round=3,
                protected_action_required=False,
                next_deterministic_action="continue", base_ref="main",
                tests=(evidence(head),), extra_round_approval_id=approval_id,
                approval_store=self.approval_store,
            )
            self.assertEqual(
                verify_handoff_package(package, package.digest, repo.root, base_ref="main").status,
                "INVALID",
            )
            self.assertEqual(
                verify_handoff_package(
                    package, package.digest, repo.root, base_ref="main",
                    approval_store=self.approval_store,
                ).status,
                "VERIFIED",
            )

    def test_approval_store_releases_sqlite_file_on_windows(self):
        path = Path(self.temp.name) / "cleanup.db"
        store = ApprovalStore(path)
        approval_id = store.request(ApprovalRequest(
            "p", "review", "target", {}, "tester",
        ))
        self.assertIsNotNone(store.get(approval_id))
        path.unlink()
        self.assertFalse(path.exists())


class CrossProjectTouchCompatibilityTests(unittest.TestCase):
    """A9: v1's bool cross_project_touch cannot be silently converted into v2's project-id list."""

    def test_v1_false_converts_to_empty_tuple(self):
        self.assertEqual(convert_v1_cross_project_touch(False), ())

    def test_v1_true_fails_closed_rather_than_guessing(self):
        with self.assertRaisesRegex(ValueError, "cross_project_touch_unknown_fail_closed"):
            convert_v1_cross_project_touch(True)

    def test_non_bool_input_is_rejected(self):
        with self.assertRaises(ValueError):
            convert_v1_cross_project_touch("true")


class TestEvidenceProvenanceTests(unittest.TestCase):
    """A10: distinguishes evidence a caller merely asserts from evidence this module
    independently captured the HEAD for."""

    def test_caller_declared_requires_explicit_provenance(self):
        with self.assertRaises(ValueError):
            TestEvidenceV2(command="pytest", exit_code=0, passed=1, failed=0, errors=0, skipped=0,
                          head_sha="a" * 40, provenance="NOT_A_REAL_PROVENANCE").validate()

    def test_caller_declared_evidence_is_accepted_when_explicit(self):
        TestEvidenceV2(command="pytest", exit_code=0, passed=1, failed=0, errors=0, skipped=0,
                      head_sha="a" * 40, provenance="CALLER_DECLARED").validate()

    def test_capture_test_evidence_stamps_independently_captured(self):
        with _TempRepo() as repo:
            repo.new_branch("feature")
            head = repo.commit_file("a.txt", "a", "add a")
            result = capture_test_evidence(repo.root, command="pytest -q", exit_code=0, passed=5, failed=0,
                                           errors=0, skipped=0, base_ref="main")
            self.assertEqual(result.provenance, "INDEPENDENTLY_CAPTURED")
            self.assertEqual(result.head_sha, head)

    def test_capture_test_evidence_head_sha_cannot_be_supplied_by_caller(self):
        # the caller has no way to pass a head_sha into capture_test_evidence() at all --
        # it is always derived from the real repo, proven by inspecting the function's own
        # keyword-only parameters never including one.
        import inspect
        params = inspect.signature(capture_test_evidence).parameters
        self.assertNotIn("head_sha", params)


class VerificationResultTests(unittest.TestCase):
    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            VerificationResult("NOT_A_REAL_STATUS", ()).validate()


if __name__ == "__main__":
    unittest.main()
