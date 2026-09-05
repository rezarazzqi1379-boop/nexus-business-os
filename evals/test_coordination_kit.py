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
    generate_handoff_package,
    scan_diff_for_secrets,
    verify_handoff_package,
)
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
    values = dict(command="pytest -q", exit_code=0, passed=10, failed=0, errors=0, skipped=0, head_sha=head_sha)
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

    def test_round_three_is_rejected_without_human_flag(self):
        with self.assertRaisesRegex(ValueError, "review_round_exceeds_budget_without_human_authorization"):
            self._package(review_round=3).validate()

    def test_round_three_is_accepted_with_explicit_human_flag(self):
        self._package(review_round=3, human_authorized_extra_rounds=True).validate()  # must not raise

    def test_ai_cannot_self_certify_by_only_setting_the_flag_without_intent(self):
        # the flag exists and is respected, but it is a distinct, explicit, named field --
        # nothing in validate()/generate_handoff_package() ever sets it to True automatically.
        package = self._package(review_round=1)
        self.assertFalse(package.human_authorized_extra_rounds)


class VerificationResultTests(unittest.TestCase):
    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            VerificationResult("NOT_A_REAL_STATUS", ()).validate()


if __name__ == "__main__":
    unittest.main()
