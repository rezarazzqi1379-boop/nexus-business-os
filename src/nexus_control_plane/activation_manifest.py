from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


_ALLOWED_MODES = {
    "shadow",
    "shadow_enforced",
    "shadow_runtime",
    "policy_active",
    "governance_active",
    "experiment",
    "hold",
}


@dataclass(frozen=True)
class ActivationComponent:
    component: str
    owner_pr: int
    mode: str
    production_authorized: bool = False


@dataclass(frozen=True)
class ActivationManifest:
    manifest_id: str
    mode: str
    production_authorized: bool
    components: tuple[ActivationComponent, ...]
    incubators: tuple[int, ...] = ()
    superseded: tuple[int, ...] = ()
    integration_only: tuple[int, ...] = ()
    global_invariants: tuple[str, ...] = ()


def _clean_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _unique(values: Iterable[object]) -> bool:
    seq = tuple(values)
    try:
        return len(set(seq)) == len(seq)
    except TypeError:
        return False


def validate_activation_manifest(manifest: ActivationManifest) -> tuple[bool, tuple[str, ...]]:
    errors: list[str] = []
    if not isinstance(manifest, ActivationManifest):
        return False, ("invalid_manifest_type",)
    if not _clean_text(manifest.manifest_id):
        errors.append("invalid_manifest_id")
    if manifest.mode != "shadow":
        errors.append("project_activation_must_remain_shadow_until_explicit_promotion")
    if manifest.production_authorized is not False:
        errors.append("manifest_must_not_self_authorize_production")
    if not isinstance(manifest.components, tuple) or not manifest.components:
        errors.append("components_required")
        return False, tuple(errors)

    names: list[str] = []
    owners: list[int] = []
    for item in manifest.components:
        if not isinstance(item, ActivationComponent):
            errors.append("invalid_component_type")
            continue
        if not _clean_text(item.component):
            errors.append("invalid_component_name")
        else:
            names.append(item.component)
        if not isinstance(item.owner_pr, int) or isinstance(item.owner_pr, bool) or item.owner_pr <= 0:
            errors.append("invalid_owner_pr")
        else:
            owners.append(item.owner_pr)
        if item.mode not in _ALLOWED_MODES:
            errors.append(f"invalid_mode:{item.component}")
        if item.production_authorized is not False:
            errors.append(f"draft_component_cannot_claim_production:{item.component}")

    if not _unique(names):
        errors.append("duplicate_component")
    if any(not isinstance(x, int) or isinstance(x, bool) or x <= 0 for group in (manifest.incubators, manifest.superseded, manifest.integration_only) for x in group):
        errors.append("invalid_pr_classification")
    all_classified = tuple(owners) + manifest.incubators + manifest.superseded + manifest.integration_only
    if not _unique(all_classified):
        errors.append("pr_cannot_have_multiple_activation_roles")
    if not isinstance(manifest.global_invariants, tuple) or any(not _clean_text(x) for x in manifest.global_invariants):
        errors.append("invalid_global_invariants")
    elif not _unique(manifest.global_invariants):
        errors.append("duplicate_global_invariant")

    required = {
        "single_canonical_owner_per_concern",
        "verified_state_before_state_change",
        "exact_action_human_gate_for_consequential_actions",
        "no_draft_or_unmerged_component_may_claim_production",
        "telemetry_failure_must_not_repeat_business_action",
    }
    if isinstance(manifest.global_invariants, tuple) and not required.issubset(set(manifest.global_invariants)):
        errors.append("required_global_invariant_missing")
    return not errors, tuple(errors)
