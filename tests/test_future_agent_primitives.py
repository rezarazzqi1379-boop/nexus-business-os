from nexus_agents.agent_identity import AgentIdentityManifest
from nexus_agents.experience_ledger import ExperienceTrajectory, eligible_for_learning
from nexus_agents.skill_compiler import SkillProposal, decide_skill_proposal


def test_agent_identity_blocks_consequential_actions():
    m = AgentIdentityManifest(
        agent_id="agent-1", version="0.1", purpose="research",
        capabilities=("READ",), allowed_projects=("PRJ-HYD-01",),
        allowed_actions=("READ", "EXTERNAL_SEND"), forbidden_actions=(),
        data_classes=("PUBLIC",), risk="LOW", rollback_ref="rb-1",
    )
    assert "consequential actions require separate runtime approval gate" in m.validate()


def test_agent_identity_preserves_project_scope():
    m = AgentIdentityManifest(
        agent_id="agent-1", version="0.1", purpose="research",
        capabilities=("READ",), allowed_projects=("PRJ-HYD-01",),
        allowed_actions=("READ",), forbidden_actions=("PRODUCTION",),
        data_classes=("PUBLIC",), risk="LOW", rollback_ref="rb-1",
    )
    assert m.can_touch_project("PRJ-HYD-01") is True
    assert m.can_touch_project("PRJ-KCL-01") is False


def test_unknown_outcome_cannot_teach():
    t = ExperienceTrajectory(
        trajectory_id="t1", agent_id="a1", project_id="PRJ-HYD-01", task_id="x",
        source_refs=("s1",), actions=("READ",), tests=("eval",), outcome="UNKNOWN",
        human_corrections=0, reusable_lessons=("promote me",), provenance_hash="abc",
    )
    assert "unknown outcome cannot produce reusable lessons" in t.validate()
    assert eligible_for_learning(t) is False


def test_only_clean_success_is_learning_eligible():
    t = ExperienceTrajectory(
        trajectory_id="t1", agent_id="a1", project_id="PRJ-HYD-01", task_id="x",
        source_refs=("s1",), actions=("READ",), tests=("eval",), outcome="SUCCESS",
        human_corrections=0, reusable_lessons=("use canonical first",), provenance_hash="abc",
    )
    assert eligible_for_learning(t) is True


def test_skill_compiler_requires_three_clean_trajectories():
    p = SkillProposal(
        skill_id="skill-1", source_trajectory_ids=("t1", "t2"), project_scope=("PRJ-HYD-01",),
        instruction="Do safe research", acceptance_tests=("eval-1",), rollback_ref="rb-1",
    )
    assert decide_skill_proposal(p) == "REJECT"


def test_external_skill_never_auto_promotes():
    p = SkillProposal(
        skill_id="skill-1", source_trajectory_ids=("t1", "t2", "t3"), project_scope=("PRJ-HYD-01",),
        instruction="Draft then send", acceptance_tests=("eval-1",), rollback_ref="rb-1",
        requires_external_action=True,
    )
    assert decide_skill_proposal(p) == "DRAFT_SKILL"
