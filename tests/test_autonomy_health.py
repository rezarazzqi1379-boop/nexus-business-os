from nexus_core.autonomy import WorkItem
from nexus_core.autonomy_health import plan_autonomy_with_health
from nexus_core.capabilities import Capability
from nexus_core.capability_health import CapabilityHealth


def _capability(capability_id: str, *, can_write: bool = False) -> Capability:
    return Capability(
        capability_id=capability_id,
        purpose=f"Use {capability_id}",
        systems=(capability_id.split(".")[0],),
        can_read=True,
        can_write=can_write,
        status="available",
        proof_ref=f"registry:{capability_id}",
    )


def _task(*, write_required: bool = False, acceptable=("github.write",)) -> WorkItem:
    return WorkItem(
        task_id="health-gated-task",
        domain="security",
        objective="Run reversible internal engineering work only through a fresh proven route.",
        action_kind="branch_commit" if write_required else "read",
        acceptable_capability_ids=acceptable,
        evidence_refs=("github:repo:nexus-business-os",),
        write_required=write_required,
    )


def _health(
    capability_id: str,
    *,
    state="verified_read",
    checked_at="2026-08-19T18:00:00+00:00",
    proven_access=("read",),
) -> CapabilityHealth:
    return CapabilityHealth(
        capability_id=capability_id,
        state=state,
        checked_at=checked_at,
        route_ref=f"route:{capability_id}",
        evidence_ref=f"probe:{capability_id}",
        proven_access=proven_access,
    )


def test_fresh_read_health_allows_read_only_work():
    plan = plan_autonomy_with_health(
        (_task(acceptable=("gmail.read",)),),
        (_capability("gmail.read"),),
        (_health("gmail.read"),),
        now="2026-08-19T18:30:00+00:00",
    )
    assert len(plan.runnable) == 1
    assert plan.blocked == ()


def test_write_work_requires_explicit_verified_write_health():
    plan = plan_autonomy_with_health(
        (_task(write_required=True),),
        (_capability("github.write", can_write=True),),
        (_health("github.write"),),
        now="2026-08-19T18:30:00+00:00",
    )
    assert plan.runnable == ()
    assert len(plan.blocked) == 1
    assert "capability health unavailable: github.write" in plan.blocked[0].blockers


def test_fresh_verified_write_health_allows_reversible_branch_commit():
    plan = plan_autonomy_with_health(
        (_task(write_required=True),),
        (_capability("github.write", can_write=True),),
        (_health("github.write", state="verified_write", proven_access=("read", "write")),),
        now="2026-08-19T18:30:00+00:00",
    )
    assert len(plan.runnable) == 1
    assert plan.runnable[0].selected_capability_ids == ("github.write",)


def test_stale_health_blocks_route_even_when_registry_says_available():
    plan = plan_autonomy_with_health(
        (_task(acceptable=("gmail.read",)),),
        (_capability("gmail.read"),),
        (_health("gmail.read", checked_at="2026-08-19T00:00:00+00:00"),),
        now="2026-08-19T18:30:00+00:00",
        max_age_seconds=21_600,
    )
    assert plan.runnable == ()
    assert len(plan.blocked) == 1
    assert "capability health unavailable: gmail.read" in plan.blocked[0].blockers


def test_duplicate_health_records_fail_closed():
    duplicate = _health("gmail.read")
    plan = plan_autonomy_with_health(
        (_task(acceptable=("gmail.read",)),),
        (_capability("gmail.read"),),
        (duplicate, duplicate),
        now="2026-08-19T18:30:00+00:00",
    )
    assert plan.runnable == ()
    assert len(plan.blocked) == 1
    assert "capability health unavailable: gmail.read" in plan.blocked[0].blockers


def test_unhealthy_route_is_removed_before_selection_so_healthy_alternative_wins():
    plan = plan_autonomy_with_health(
        (_task(acceptable=("gmail.read", "notion.read")),),
        (_capability("gmail.read"), _capability("notion.read")),
        (
            _health("gmail.read", state="blocked", proven_access=()),
            _health("notion.read"),
        ),
        now="2026-08-19T18:30:00+00:00",
    )
    assert len(plan.runnable) == 1
    assert plan.runnable[0].selected_capability_ids == ("notion.read",)
    assert plan.blocked == ()
