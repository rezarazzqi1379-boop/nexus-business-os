import json
from pathlib import Path

from nexus_control_plane.activation_manifest import ActivationComponent, ActivationManifest, validate_activation_manifest


def _load_manifest():
    raw = json.loads(Path("data/nexus_activation_manifest_v0_1.json").read_text(encoding="utf-8"))
    return ActivationManifest(
        manifest_id=raw["manifest_id"],
        mode=raw["mode"],
        production_authorized=raw["production_authorized"],
        components=tuple(ActivationComponent(**item) for item in raw["components"]),
        incubators=tuple(raw["incubators"]),
        superseded=tuple(raw["superseded"]),
        integration_only=tuple(raw["integration_only"]),
        global_invariants=tuple(raw["global_invariants"]),
    )


def test_repository_activation_manifest_is_valid_and_shadow_only():
    manifest = _load_manifest()
    valid, errors = validate_activation_manifest(manifest)
    assert valid, errors
    assert manifest.mode == "shadow"
    assert manifest.production_authorized is False
    assert all(component.production_authorized is False for component in manifest.components)
    owners = {component.owner_pr for component in manifest.components}
    assert {1,2,4,6,7,10,12,16,19,28,29,30,31,33,36,37,39,40}.issubset(owners)


def test_manifest_blocks_self_promotion():
    manifest = _load_manifest()
    forged = ActivationManifest(
        manifest.manifest_id,
        "production",
        True,
        manifest.components,
        manifest.incubators,
        manifest.superseded,
        manifest.integration_only,
        manifest.global_invariants,
    )
    valid, errors = validate_activation_manifest(forged)
    assert not valid
    assert "project_activation_must_remain_shadow_until_explicit_promotion" in errors
    assert "manifest_must_not_self_authorize_production" in errors


def test_component_cannot_claim_production():
    manifest = _load_manifest()
    changed = list(manifest.components)
    first = changed[0]
    changed[0] = ActivationComponent(first.component, first.owner_pr, first.mode, True)
    forged = ActivationManifest(
        manifest.manifest_id,
        manifest.mode,
        False,
        tuple(changed),
        manifest.incubators,
        manifest.superseded,
        manifest.integration_only,
        manifest.global_invariants,
    )
    valid, errors = validate_activation_manifest(forged)
    assert not valid
    assert any(error.startswith("draft_component_cannot_claim_production") for error in errors)


def test_pr_cannot_be_owner_and_incubator_at_same_time():
    manifest = _load_manifest()
    forged = ActivationManifest(
        manifest.manifest_id,
        manifest.mode,
        False,
        manifest.components,
        manifest.incubators + (36,),
        manifest.superseded,
        manifest.integration_only,
        manifest.global_invariants,
    )
    valid, errors = validate_activation_manifest(forged)
    assert not valid
    assert "pr_cannot_have_multiple_activation_roles" in errors
