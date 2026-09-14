import pytest

from external_account_orchestrator import AccountTarget, approval_request_for, authorize_commit, build_onboarding_plan


def target(**changes):
    values = dict(target_id="P1", service_name="Example", signup_url="https://example.com/signup",
                  purpose="Research", jurisdiction="DE", account_owner="Owner")
    values.update(changes)
    return AccountTarget(**values)


def test_safe_preparation_is_automatic_but_commit_is_approval_bound():
    plan = build_onboarding_plan(target(), public_fields={"display_name": "NEXUS"},
                                 terms_url="https://example.com/terms")
    request = approval_request_for(plan, action="create_account", requested_by="owner")
    assert "navigate_to_signup" in plan.allowed_automatic_steps
    with pytest.raises(PermissionError, match="human_presence"):
        authorize_commit(plan, action="create_account", approved_action_digest=request.action_digest)
    assert authorize_commit(plan, action="create_account", approved_action_digest=request.action_digest,
                            human_present=True) == "COMMIT_READY"


def test_kyc_and_payment_require_owner_input_even_with_digest():
    plan = build_onboarding_plan(target(requires_kyc=True, requires_payment=True), public_fields={"name": "NEXUS"})
    request = approval_request_for(plan, action="submit_kyc", requested_by="owner")
    with pytest.raises(PermissionError, match="owner_input"):
        authorize_commit(plan, action="submit_kyc", approved_action_digest=request.action_digest, human_present=True)


def test_sensitive_fields_cannot_enter_plan():
    with pytest.raises(ValueError, match="sensitive"):
        build_onboarding_plan(target(), public_fields={"password": "do-not-store"})


def test_wrong_approval_digest_fails_closed():
    plan = build_onboarding_plan(target(), public_fields={"name": "NEXUS"})
    with pytest.raises(PermissionError, match="mismatch"):
        authorize_commit(plan, action="create_account", approved_action_digest="wrong", human_present=True)
