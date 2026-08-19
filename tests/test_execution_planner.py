from nexus_core.execution_planner import ExecutionStep, build_execution_plan


def test_orders_dependencies_and_separates_human_gate():
    steps = (
        ExecutionStep("research", "research", "Collect evidence"),
        ExecutionStep("draft", "draft", "Prepare draft", depends_on=("research",)),
        ExecutionStep("send", "external", "Send approved message", depends_on=("draft",), human_gate=True),
    )
    plan = build_execution_plan(steps)
    assert [step.step_id for step in plan.runnable] == ["research", "draft"]
    assert [step.step_id for step in plan.gated] == ["send"]
    assert plan.blocked == ()


def test_external_without_gate_fails_closed():
    plan = build_execution_plan((ExecutionStep("send", "external", "Send message"),))
    assert plan.runnable == ()
    assert plan.gated == ()
    assert "external_step_requires_human_gate" in plan.blocked[0][1]


def test_missing_dependency_blocks_step():
    plan = build_execution_plan((ExecutionStep("draft", "draft", "Draft", depends_on=("missing",)),))
    assert plan.runnable == ()
    assert plan.blocked[0][1] == ("missing_dependency:missing",)


def test_dependency_cycle_is_blocked():
    steps = (
        ExecutionStep("a", "research", "A", depends_on=("b",)),
        ExecutionStep("b", "research", "B", depends_on=("a",)),
    )
    plan = build_execution_plan(steps)
    assert plan.runnable == ()
    assert len(plan.blocked) == 2
    assert all("dependency_cycle" in errors for _, errors in plan.blocked)
