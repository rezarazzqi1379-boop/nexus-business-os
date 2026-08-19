from nexus_core.provider_failover import ProviderRoute, choose_provider_route


def _route(provider_id: str, *, state: str = "healthy", priority: int = 1, can_read: bool = True, can_write: bool = False):
    return ProviderRoute(
        provider_id=provider_id,
        capability="prospecting",
        state=state,  # type: ignore[arg-type]
        priority=priority,
        can_read=can_read,
        can_write=can_write,
        evidence_refs=(f"health:{provider_id}",),
    )


def test_degraded_primary_fails_over_to_healthy_secondary() -> None:
    decision = choose_provider_route((
        _route("apollo", state="degraded", priority=1),
        _route("exa", state="healthy", priority=2),
    ), capability="prospecting")
    assert decision.selected_provider_id == "exa"
    assert decision.attempted_provider_ids == ("apollo", "exa")


def test_write_request_never_uses_read_only_fallback() -> None:
    decision = choose_provider_route((
        _route("provider-a", priority=1, can_write=False),
        _route("provider-b", priority=2, can_write=True),
    ), capability="prospecting", write_required=True)
    assert decision.selected_provider_id == "provider-b"


def test_no_route_fails_closed() -> None:
    decision = choose_provider_route((
        _route("apollo", state="blocked"),
        _route("exa", state="unknown", priority=2),
    ), capability="prospecting")
    assert decision.selected_provider_id is None
    assert "no verified healthy route" in decision.reason


def test_duplicate_provider_ids_do_not_create_ambiguous_success() -> None:
    decision = choose_provider_route((
        _route("exa", priority=1),
        _route("exa", priority=2),
    ), capability="prospecting")
    assert decision.selected_provider_id == "exa"
