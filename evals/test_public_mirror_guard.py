from __future__ import annotations

import unittest

from coordination_kit import HandoffPackageV2
from public_mirror_guard import (
    PublicationDecision,
    build_ack_record,
    find_disallowed_urls,
    find_high_entropy_tokens,
    load_schema,
    project_private_package_to_public,
    reject_protected_action_language,
    review_for_publication,
    scan_text_for_sensitive_data,
    shannon_entropy,
    validate_against_schema,
)

UTC_NOW = "2026-09-05T00:00:00+00:00"


def clean_record(**changes) -> dict:
    record = dict(
        schema_version="nexus.public-handoff.v1", record_type="status", task_id="BUS-TEST-001",
        project_id="NEXUS_CORE", lane_id="coordination", state="PUBLISHED", risk_class="LOW",
        protected_action_required=False, created_at=UTC_NOW,
    )
    record.update(changes)
    return record


def private_package(**changes) -> HandoffPackageV2:
    values = dict(
        task_id="task-1", owner="claude-code", branch="feat/x", base_sha="a" * 40, head_sha="b" * 40,
        state="TESTS_PASSED", risk_class="LOW", review_round=1, protected_action_required=False,
        next_deterministic_action="continue", generated_from_git=True, remote_ref=None, remote_head_sha=None,
        ahead_by=0, behind_by=0, worktree_clean=True, untracked_files=(), diff_digest="d" * 12,
        test_head_sha="b" * 40, authority_refs=(), review_status="APPROVED", reviewed_head_sha=None,
        supersedes_handoff_digest=None, project_id="NEXUS_CORE", lane_id="coordination",
    )
    values.update(changes)
    return HandoffPackageV2(**values)


class SchemaEnforcementTests(unittest.TestCase):
    def test_clean_record_passes(self):
        validate_against_schema(clean_record(), load_schema())

    def test_unknown_field_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown_fields_rejected"):
            validate_against_schema(clean_record(sneaky_field="x"), load_schema())

    def test_missing_required_field_is_rejected(self):
        record = clean_record()
        del record["project_id"]
        with self.assertRaisesRegex(ValueError, "missing_required_field:project_id"):
            validate_against_schema(record, load_schema())

    def test_wrong_schema_version_const_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_const"):
            validate_against_schema(clean_record(schema_version="v0.9"), load_schema())

    def test_illegal_state_value_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_enum_value:state"):
            validate_against_schema(clean_record(state="APPROVED"), load_schema())

    def test_illegal_state_transition_like_authorized_is_rejected(self):
        for bad_state in ("AUTHORIZED", "ACCEPTED", "MERGED", "DEPLOYED"):
            with self.assertRaises(ValueError):
                validate_against_schema(clean_record(state=bad_state), load_schema())

    def test_wrong_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_type"):
            validate_against_schema(clean_record(protected_action_required="false"), load_schema())

    def test_bad_head_sha_pattern_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "pattern_mismatch:head_sha"):
            validate_against_schema(clean_record(head_sha="not-a-sha"), load_schema())

    def test_bad_date_time_format_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_date_time"):
            validate_against_schema(clean_record(created_at="not-a-date"), load_schema())

    def test_fake_project_id_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_type:project_id"):
            validate_against_schema(clean_record(project_id=12345), load_schema())


class SecretAndPiiGuardTests(unittest.TestCase):
    def test_clean_text_has_no_findings(self):
        self.assertEqual(scan_text_for_sensitive_data("Tests passed, ready for review."), ())

    def test_github_token_is_detected(self):
        findings = scan_text_for_sensitive_data("token: ghp_abcdefghijklmnopqrstuvwxyz012345")
        self.assertTrue(any("secret" in f for f in findings))

    def test_bearer_token_is_detected(self):
        findings = scan_text_for_sensitive_data("Authorization: Bearer abcdef0123456789ABCDEF")
        self.assertIn("bearer_token", findings)

    def test_pem_private_key_is_detected(self):
        findings = scan_text_for_sensitive_data("-----BEGIN RSA PRIVATE KEY-----\nMIIB...")
        self.assertTrue(any("secret" in f for f in findings))

    def test_jwt_like_token_is_detected(self):
        findings = scan_text_for_sensitive_data("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dQw4w9WgXcQ")
        self.assertIn("jwt_like_token", findings)

    def test_env_style_secret_assignment_is_detected(self):
        findings = scan_text_for_sensitive_data("API_KEY=sk_live_abcdefghijklmnop")
        self.assertIn("env_style_secret_assignment", findings)

    def test_email_is_detected(self):
        findings = scan_text_for_sensitive_data("Contact ops at someone@example.com for details.")
        self.assertIn("pii_email_or_phone", findings)

    def test_phone_number_is_detected(self):
        findings = scan_text_for_sensitive_data("Call +1 415 555 0134 for support.")
        self.assertIn("pii_email_or_phone", findings)

    def test_price_or_contract_language_is_detected(self):
        findings = scan_text_for_sensitive_data("Final price is USD 12,000 per contract terms.")
        self.assertIn("pricing_or_contract_language", findings)

    def test_code_snippet_is_detected(self):
        findings = scan_text_for_sensitive_data("```python\ndef run():\n    pass\n```")
        self.assertIn("code_snippet", findings)

    def test_high_entropy_blob_is_detected_even_with_no_known_pattern(self):
        # deliberately not shaped like any of the fixed patterns above, but random-looking
        blob = "Qx7ZmP2vR9kLtN4wJ8hB3sD6fG1cA5eY0uV_xK+9zW"
        self.assertTrue(find_high_entropy_tokens(blob))
        self.assertTrue(any("high_entropy_blob" in f for f in scan_text_for_sensitive_data(blob)))

    def test_low_entropy_repeated_text_is_not_flagged_as_high_entropy(self):
        self.assertEqual(find_high_entropy_tokens("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"), ())

    def test_shannon_entropy_of_empty_string_is_zero(self):
        self.assertEqual(shannon_entropy(""), 0.0)

    def test_disallowed_url_is_detected(self):
        self.assertEqual(find_disallowed_urls("See http://internal.example.local/secret"), ("internal.example.local",))

    def test_allowed_url_host_is_not_flagged(self):
        self.assertEqual(find_disallowed_urls("See https://github.com/some/repo"), ())

    def test_raw_ip_private_url_is_detected(self):
        self.assertTrue(find_disallowed_urls("connect to http://192.168.1.10:8080/admin"))


class ProtectedActionLanguageTests(unittest.TestCase):
    def test_clean_text_has_no_protected_action_language(self):
        self.assertEqual(reject_protected_action_language("Continue reviewing the branch."), ())

    def test_merge_language_is_rejected(self):
        self.assertIn("merge", reject_protected_action_language("Please merge this to main."))

    def test_payment_language_is_rejected(self):
        self.assertTrue(reject_protected_action_language("Approved for payment, proceed."))

    def test_public_payload_cannot_smuggle_protected_action_authority(self):
        record = clean_record(next_safe_action="Go ahead and deploy to production now.")
        decision = review_for_publication(record)
        self.assertFalse(decision.publishable)
        self.assertTrue(any("protected_action" in r for r in decision.reasons))


class PromptInjectionInertnessTests(unittest.TestCase):
    def test_injected_instruction_text_is_treated_as_plain_data(self):
        # this must not raise, exec, or do anything but scan the string as text
        malicious = "; rm -rf / ; import os; os.system('evil') ${jndi:ldap://x}"
        record = clean_record(next_safe_action=malicious)
        decision = review_for_publication(record)
        self.assertIsInstance(decision, PublicationDecision)  # merely analyzed, never executed


class AckSemanticsTests(unittest.TestCase):
    def test_ack_record_is_schema_valid(self):
        ack = build_ack_record(task_id="task-1", project_id="NEXUS_CORE", lane_id="coordination",
                               source_record_digest="a" * 64, owner_role="claude-chat", created_at=UTC_NOW)
        validate_against_schema(ack, load_schema())

    def test_ack_state_is_observed_never_approved(self):
        ack = build_ack_record(task_id="task-1", project_id="NEXUS_CORE", lane_id="coordination",
                               source_record_digest="a" * 64, owner_role="claude-chat", created_at=UTC_NOW)
        self.assertEqual(ack["state"], "OBSERVED")
        self.assertNotIn(ack["state"], {"APPROVED", "ACCEPTED", "MERGED", "DEPLOYED", "AUTHORIZED"})

    def test_ack_never_sets_protected_action_required_true(self):
        ack = build_ack_record(task_id="task-1", project_id="NEXUS_CORE", lane_id="coordination",
                               source_record_digest="a" * 64, owner_role="claude-chat", created_at=UTC_NOW)
        self.assertFalse(ack["protected_action_required"])

    def test_malformed_ack_missing_project_id_is_rejected(self):
        with self.assertRaises(ValueError):
            build_ack_record(task_id="task-1", project_id="", lane_id="coordination",
                             source_record_digest="a" * 64, owner_role="claude-chat", created_at=UTC_NOW)

    def test_ack_cannot_promote_a_task_to_done_or_deployed(self):
        # the schema's own "state" enum for a public record contains no such value, so
        # attempting to construct an ack claiming one fails schema validation.
        forged = build_ack_record(task_id="task-1", project_id="NEXUS_CORE", lane_id="coordination",
                                  source_record_digest="a" * 64, owner_role="claude-chat", created_at=UTC_NOW)
        forged = {**forged, "state": "DEPLOYED"}
        with self.assertRaises(ValueError):
            validate_against_schema(forged, load_schema())


class ProjectIsolationAndProjectionTests(unittest.TestCase):
    def test_missing_project_id_on_private_package_is_rejected(self):
        package = private_package(project_id=None)
        with self.assertRaisesRegex(ValueError, "public_projection_requires_explicit_project_id"):
            project_private_package_to_public(package, record_type="status", state="PUBLISHED", review_status="VERIFIED")

    def test_missing_lane_id_on_private_package_is_rejected(self):
        package = private_package(lane_id=None)
        with self.assertRaisesRegex(ValueError, "public_projection_requires_explicit_lane_id"):
            project_private_package_to_public(package, record_type="status", state="PUBLISHED", review_status="VERIFIED")

    def test_projection_never_infers_a_missing_project_id(self):
        # there is no default/fallback project_id anywhere in project_private_package_to_public
        package = private_package(project_id=None, lane_id="coordination")
        with self.assertRaises(ValueError):
            project_private_package_to_public(package, record_type="status", state="PUBLISHED", review_status="VERIFIED")

    def test_clean_projection_is_schema_valid(self):
        package = private_package()
        record = project_private_package_to_public(package, record_type="status", state="PUBLISHED", review_status="VERIFIED")
        validate_against_schema(record, load_schema())

    def test_private_review_status_vocabulary_cannot_leak_into_public_field(self):
        # HandoffPackageV2.review_status uses PENDING/APPROVED/REJECTED/STALE/SUPERSEDED --
        # a different vocabulary from the public schema's PENDING/VERIFIED/STALE/CONFLICT/
        # INVALID/SUPERSEDED. Passing the private value straight through must be rejected.
        package = private_package(review_status="APPROVED")
        with self.assertRaisesRegex(ValueError, "invalid_public_review_status"):
            project_private_package_to_public(package, record_type="status", state="PUBLISHED",
                                              review_status=package.review_status)

    def test_projection_binds_via_digest_not_raw_content(self):
        package = private_package()
        record = project_private_package_to_public(package, record_type="status", state="PUBLISHED", review_status="VERIFIED")
        self.assertEqual(record["source_record_digest"], package.digest)
        self.assertNotIn("claims", record)
        self.assertNotIn("files_changed", record)
        self.assertNotIn("cross_project_touch", record)

    def test_projection_digest_is_stable_for_identical_input(self):
        package = private_package()
        first = project_private_package_to_public(package, record_type="status", state="PUBLISHED", review_status="VERIFIED")
        second = project_private_package_to_public(package, record_type="status", state="PUBLISHED", review_status="VERIFIED")
        self.assertEqual(first["source_record_digest"], second["source_record_digest"])

    def test_different_project_ids_never_get_merged_in_projection(self):
        package_a = project_private_package_to_public(private_package(project_id="PRJ-A"), record_type="status",
                                                       state="PUBLISHED", review_status="VERIFIED")
        package_b = project_private_package_to_public(private_package(project_id="PRJ-B"), record_type="status",
                                                       state="PUBLISHED", review_status="VERIFIED")
        self.assertNotEqual(package_a["project_id"], package_b["project_id"])


class FullPublicationGateTests(unittest.TestCase):
    def test_clean_connectivity_fixture_is_accepted(self):
        record = clean_record(record_type="status", tests_summary="", unknowns_summary="", next_safe_action="")
        decision = review_for_publication(record)
        self.assertTrue(decision.publishable)

    def test_unknown_field_holds_for_review(self):
        decision = review_for_publication(clean_record(mystery="x"))
        self.assertFalse(decision.publishable)
        self.assertEqual(decision.state, "HOLD_FOR_REVIEW")

    def test_secret_in_free_text_holds_for_review(self):
        record = clean_record(tests_summary="ghp_abcdefghijklmnopqrstuvwxyz012345")
        decision = review_for_publication(record)
        self.assertFalse(decision.publishable)

    def test_email_in_free_text_holds_for_review(self):
        record = clean_record(unknowns_summary="ask jane@example.com about this")
        decision = review_for_publication(record)
        self.assertFalse(decision.publishable)

    def test_price_in_free_text_holds_for_review(self):
        record = clean_record(next_safe_action="Confirm the $50,000 contract value.")
        decision = review_for_publication(record)
        self.assertFalse(decision.publishable)

    def test_private_url_in_free_text_holds_for_review(self):
        record = clean_record(next_safe_action="See http://10.0.0.5/internal for details.")
        decision = review_for_publication(record)
        self.assertFalse(decision.publishable)

    def test_hold_for_review_never_raises_for_ordinary_bad_content(self):
        # sensitive content is a data decision (HOLD), not a crash
        try:
            review_for_publication(clean_record(tests_summary="AKIAABCDEFGHIJKLMNOP"))
        except Exception as exc:  # noqa: BLE001
            self.fail(f"review_for_publication raised unexpectedly: {exc}")

    def test_duplicate_field_like_payload_is_still_just_a_dict_last_write_wins_and_still_scanned(self):
        # Python dict literals can't have duplicate keys, but simulate the JSON-duplicate-key
        # scenario by explicitly overwriting after clean_record() and confirming the guard
        # still evaluates the final effective value, never an earlier shadowed one blindly.
        record = clean_record()
        record["state"] = "HOLD_FOR_REVIEW"
        record["state"] = "PUBLISHED"  # last value wins, as any JSON parser would also do
        decision = review_for_publication(record)
        self.assertEqual(record["state"], "PUBLISHED")
        self.assertTrue(decision.publishable)


if __name__ == "__main__":
    unittest.main()
