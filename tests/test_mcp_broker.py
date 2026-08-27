from nexus_core.mcp_broker import MCPCandidate, assess_mcp, deduplicate_candidates


def _candidate(**overrides):
    base = dict(
        server_id="mcp.example.readonly",
        name="Example Readonly",
        registry_source="https://registry.modelcontextprotocol.io/servers/example",
        repository_url="https://github.com/example/mcp-server",
        publisher="example",
        trust_state="TRUSTED",
        requested_access=("READ_ONLY",),
        tool_names=("search", "fetch"),
        provenance_verified=True,
        schema_reviewed=True,
        secrets_required=False,
        external_side_effects=False,
    )
    base.update(overrides)
    return MCPCandidate(**base)


def test_only_trusted_readonly_candidate_can_reach_sandbox():
    result = assess_mcp(_candidate())
    assert result.decision == "SANDBOX_ELIGIBLE"
    assert not result.reasons


def test_unverified_server_never_auto_connects():
    result = assess_mcp(_candidate(trust_state="UNVERIFIED", provenance_verified=False))
    assert result.decision == "REVIEW"
    assert "server trust is unverified" in result.reasons


def test_write_access_requires_review_even_when_trusted():
    result = assess_mcp(_candidate(requested_access=("READ_ONLY", "WRITE")))
    assert result.decision == "REVIEW"
    assert any("write/execute" in reason for reason in result.reasons)


def test_secret_requiring_server_requires_review():
    result = assess_mcp(_candidate(secrets_required=True))
    assert result.decision == "REVIEW"
    assert any("credential" in reason for reason in result.reasons)


def test_external_side_effect_server_requires_human_gate():
    result = assess_mcp(_candidate(external_side_effects=True))
    assert result.decision == "REVIEW"
    assert any("human-gated" in reason for reason in result.reasons)


def test_malformed_registry_source_is_rejected():
    result = assess_mcp(_candidate(registry_source="http://insecure.example"))
    assert result.decision == "REJECT"


def test_duplicate_tool_names_are_rejected():
    result = assess_mcp(_candidate(tool_names=("search", "search")))
    assert result.decision == "REJECT"


def test_identical_duplicate_candidates_dedupe_but_conflicts_fail():
    item = _candidate()
    assert deduplicate_candidates((item, item)) == (item,)
    conflicting = _candidate(name="Different")
    try:
        deduplicate_candidates((item, conflicting))
    except ValueError as exc:
        assert "conflicting MCP candidate identity" in str(exc)
    else:
        raise AssertionError("conflicting identity must fail closed")
