from nexus_control_plane import AgentSpec, Authority, ControlPlane, Goal, Health, Maturity, WorkItem, WorkState


def plane():
    cp = ControlPlane()
    cp.register_goal(Goal("north-star", "Commercial outcomes", "gross_margin"))
    cp.register_agent(AgentSpec(
        id="researcher", role="research", capabilities={"web_research", "evidence"},
        authorities={Authority.READ, Authority.ANALYZE, Authority.WRITE_STATE},
        maturity=Maturity.TESTED, quality_score=.9, cost_score=.2, latency_score=.3,
    ))
    cp.register_agent(AgentSpec(
        id="writer", role="communication", capabilities={"draft_email"},
        authorities={Authority.READ, Authority.DRAFT}, maturity=Maturity.TESTED,
    ))
    return cp


def test_routes_by_capability_and_authority():
    cp = plane()
    cp.submit(WorkItem("w1", "kcl", "north-star", "supplier_research", {"web_research"}, {Authority.READ, Authority.ANALYZE}))
    assert cp.route("w1") == "researcher"
    assert cp.work["w1"].state == WorkState.RUNNING


def test_external_action_requires_gateway():
    cp = plane()
    cp.submit(WorkItem("send1", "kcl", "north-star", "send_email", {"draft_email"}, {Authority.EXTERNAL_ACTION}))
    assert cp.route("send1") is None
    assert cp.work["send1"].state == WorkState.BLOCKED
    assert "requires_human_approval_gateway" in cp.work["send1"].blockers


def test_dependency_blocks_until_done():
    cp = plane()
    cp.submit(WorkItem("a", "kcl", "north-star", "research", {"web_research"}, {Authority.READ}))
    cp.submit(WorkItem("b", "kcl", "north-star", "analysis", {"evidence"}, {Authority.ANALYZE}, depends_on=("a",)))
    assert cp.route("b") is None
    cp.route("a")
    cp.complete("a", success=True, quality=.9)
    assert cp.route("b") == "researcher"


def test_dedupe_after_completed_action():
    cp = plane()
    cp.submit(WorkItem("w1", "kcl", "north-star", "research", {"web_research"}, {Authority.READ}, dedupe_key="supplier:X:kcl"))
    cp.route("w1")
    cp.complete("w1", success=True, quality=.9)
    cp.submit(WorkItem("w2", "kcl", "north-star", "research", {"web_research"}, {Authority.READ}, dedupe_key="supplier:X:kcl"))
    assert cp.work["w2"].state == WorkState.REJECTED


def test_detects_active_duplicate_work():
    cp = plane()
    cp.submit(WorkItem("w1", "kcl", "north-star", "research", {"web_research"}, {Authority.READ}, dedupe_key="same"))
    cp.submit(WorkItem("w2", "kcl", "north-star", "research", {"web_research"}, {Authority.READ}, dedupe_key="same"))
    assert any(x.startswith("duplicate_active_work") for x in cp.conflicts())


def test_offline_agents_do_not_receive_work():
    cp = plane()
    cp.agents["researcher"].health = Health.OFFLINE
    cp.submit(WorkItem("w1", "kcl", "north-star", "research", {"web_research"}, {Authority.READ}))
    assert cp.route("w1") is None


def test_improvement_loop_never_auto_promotes_bad_agent():
    cp = plane()
    for i in range(3):
        cp.submit(WorkItem(f"w{i}", "kcl", "north-star", "research", {"web_research"}, {Authority.READ}))
        cp.route(f"w{i}")
        cp.complete(f"w{i}", success=(i != 2), quality=.6, human_correction=True)
    proposals = cp.improvement_proposals(min_samples=3)
    assert proposals
    assert proposals[0].agent_id == "researcher"
    assert proposals[0].auto_promotable is False
    assert "cross_project_contamination" in proposals[0].required_regressions
