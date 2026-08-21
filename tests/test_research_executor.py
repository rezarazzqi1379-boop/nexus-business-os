import pytest

from nexus_autonomy.research_executor import ResearchArtifact, make_research_executor
from nexus_core.autonomy import WorkItem, PlannedWork
from nexus_core.policy import GateDecision


def planned(domain="research"):
    task = WorkItem(
        task_id="r1",
        domain=domain,
        objective="research evidence",
        action_kind="research",
        acceptable_capability_ids=("web",),
        evidence_refs=("seed",),
    )
    return PlannedWork(task, "runnable", ("web",), (), GateDecision(True, False, "ok"))


def test_strong_research_requires_evidence():
    executor = make_research_executor(lambda _: ResearchArtifact("claim", (), "strong"))
    with pytest.raises(ValueError, match="requires retrievable evidence"):
        executor(planned())


def test_unverified_research_can_be_recorded_without_fake_evidence():
    executor = make_research_executor(lambda _: ResearchArtifact("hypothesis only", (), "unverified", ("verify it",)))
    result = executor(planned())
    assert result.status == "succeeded"
    assert "confidence=unverified" in result.summary
    assert result.evidence_refs == ()


def test_wrong_domain_fails_without_calling_provider():
    called = False
    def provider(_):
        nonlocal called
        called = True
        return ResearchArtifact("x", (), "unverified")
    result = make_research_executor(provider)(planned("backup"))
    assert result.status == "failed"
    assert called is False


def test_partial_research_preserves_retrievable_evidence():
    executor = make_research_executor(lambda _: ResearchArtifact("qualified", ("url:1",), "partial"))
    result = executor(planned())
    assert result.status == "succeeded"
    assert result.evidence_refs == ("url:1",)
