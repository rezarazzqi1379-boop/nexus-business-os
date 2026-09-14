"""Approval-gated preparation workflow for third-party account onboarding."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Literal, Mapping
from urllib.parse import urlsplit

from approvals import ApprovalRequest

Stage = Literal["DISCOVERED", "ELIGIBILITY_REVIEW", "IDENTITY_REQUIRED", "READY_FOR_REVIEW", "APPROVAL_PENDING", "COMMIT_READY", "COMPLETED", "BLOCKED"]

_SENSITIVE_FIELDS = frozenset({
    "password", "passphrase", "otp", "mfa", "totp", "recovery_code", "api_key", "secret",
    "passport", "national_id", "tax_id", "bank_account", "card_number", "cvv",
})
_COMMIT_ACTIONS = frozenset({"create_account", "accept_terms", "submit_kyc", "link_payment", "enable_paid_plan"})


@dataclass(frozen=True)
class AccountTarget:
    target_id: str
    service_name: str
    signup_url: str
    purpose: str
    jurisdiction: str
    account_owner: str
    expected_cost: float = 0.0
    requires_kyc: bool = False
    requires_payment: bool = False

    def validate(self) -> None:
        if not all(x.strip() for x in (self.target_id, self.service_name, self.signup_url, self.purpose,
                                      self.jurisdiction, self.account_owner)):
            raise ValueError("invalid_account_target")
        parsed = urlsplit(self.signup_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("unsafe_signup_url")
        if self.expected_cost < 0:
            raise ValueError("invalid_expected_cost")


@dataclass(frozen=True)
class AccountOnboardingPlan:
    plan_id: str
    target: AccountTarget
    stage: Stage
    public_fields: Mapping[str, str]
    missing_owner_inputs: tuple[str, ...]
    terms_url: str | None
    privacy_url: str | None
    risk_flags: tuple[str, ...]
    allowed_automatic_steps: tuple[str, ...]
    approval_required_actions: tuple[str, ...]

    @property
    def commit_digest(self) -> str:
        body = {"plan_id": self.plan_id, "target": asdict(self.target), "public_fields": dict(self.public_fields),
                "approval_required_actions": self.approval_required_actions}
        return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def build_onboarding_plan(target: AccountTarget, *, public_fields: Mapping[str, str],
                          missing_owner_inputs: tuple[str, ...] = (), terms_url: str | None = None,
                          privacy_url: str | None = None) -> AccountOnboardingPlan:
    """Prepare registration while keeping identity, consent and commit owner-bound."""
    target.validate()
    normalized = {str(k).strip().casefold(): str(v).strip() for k, v in public_fields.items()}
    if any(not key or not value for key, value in normalized.items()):
        raise ValueError("invalid_public_account_field")
    if _SENSITIVE_FIELDS.intersection(normalized):
        raise ValueError("sensitive_account_data_forbidden")
    risks = []
    missing = list(dict.fromkeys(missing_owner_inputs))
    if target.requires_kyc:
        risks.append("identity_verification_required")
        missing.append("owner_supplied_kyc_in_browser")
    if target.requires_payment or target.expected_cost > 0:
        risks.append("financial_commitment")
        missing.append("owner_supplied_payment_in_browser")
    if not terms_url:
        risks.append("terms_not_reviewed")
    stage: Stage = "IDENTITY_REQUIRED" if missing else "READY_FOR_REVIEW"
    plan_id = "acct_" + hashlib.sha256(f"{target.target_id}|{target.signup_url}|{normalized}".encode()).hexdigest()[:16]
    actions = ["create_account", "accept_terms"]
    if target.requires_kyc:
        actions.append("submit_kyc")
    if target.requires_payment:
        actions.append("link_payment")
    return AccountOnboardingPlan(
        plan_id, target, stage, normalized, tuple(dict.fromkeys(missing)), terms_url, privacy_url,
        tuple(risks),
        ("research_service", "compare_plans", "check_eligibility", "prepare_public_fields", "navigate_to_signup"),
        tuple(actions),
    )


def approval_request_for(plan: AccountOnboardingPlan, *, action: str, requested_by: str) -> ApprovalRequest:
    if action not in _COMMIT_ACTIONS or action not in plan.approval_required_actions:
        raise ValueError("account_action_not_in_plan")
    return ApprovalRequest(
        project_id=plan.target.target_id,
        action=action,
        target=plan.target.signup_url,
        parameters={"plan_id": plan.plan_id, "commit_digest": plan.commit_digest,
                    "service": plan.target.service_name, "owner": plan.target.account_owner,
                    "expected_cost": plan.target.expected_cost},
        requested_by=requested_by,
        ttl_seconds=1800,
    )


def authorize_commit(plan: AccountOnboardingPlan, *, action: str, approved_action_digest: str,
                     human_present: bool = False) -> str:
    request = approval_request_for(plan, action=action, requested_by="nexus")
    if approved_action_digest != request.action_digest:
        raise PermissionError("account_commit_approval_mismatch")
    if not human_present:
        raise PermissionError("account_commit_requires_human_presence")
    if plan.missing_owner_inputs:
        raise PermissionError("account_owner_input_required")
    return "COMMIT_READY"
