from datetime import datetime, timezone

from nexus_core.auto_bootstrap import auto_bootstrap, detect_nexus_scope
from nexus_core.chat_memory_mesh import ChatShard


def shard(**overrides):
    base = dict(
        shard_id="chat-kcl",
        chat_ref="chat://kcl",
        created_at=datetime(2026, 8, 20, 8, 0, tzinfo=timezone.utc),
        source_version_ref="notion:resume:v3.4",
        project_refs=("kcl-mop",),
        goal_refs=("commercial-revenue",),
        tags=("kcl", "supplier", "quote"),
        summary="KCl commercial state with supplier terms and compliance blocker.",
        evidence_refs=("gmail:oms-thread", "notion:resume"),
        supersedes=(),
    )
    base.update(overrides)
    return ChatShard(**base)


def test_new_chat_kcl_message_auto_resumes_without_magic_phrase():
    result = auto_bootstrap("برای KCl ادامه بده و ایمیل تامین کننده را بررسی کن", (shard(),))
    assert result.should_resume is True
    assert "kcl-mop" in result.project_refs
    assert "commercial-revenue" in result.goal_refs
    assert "AUTO-RESUME NEXUS" in result.instruction


def test_coding_message_routes_to_nexus_core():
    domains, projects, goals = detect_nexus_scope("کدنویسی GitHub و Supabase را ادامه بده")
    assert "engineering" in domains
    assert "nexus-core" in projects
    assert "ai-engineering" in goals


def test_cross_domain_message_can_recover_multiple_goal_lanes():
    domains, _, goals = detect_nexus_scope("مشتری های جدید پیدا کن و کدنویسی و پژوهش علمی را هم ادامه بده")
    assert {"commercial", "engineering", "research"}.issubset(set(domains))
    assert {"commercial-revenue", "ai-engineering", "research-science"}.issubset(set(goals))


def test_unrelated_message_does_not_force_nexus_context():
    result = auto_bootstrap("یک شعر کوتاه درباره باران بنویس", (shard(),))
    assert result.should_resume is False
    assert result.bundle is None


def test_resume_still_requires_evidence_when_no_matching_shard_exists():
    result = auto_bootstrap("GitHub پروژه NEXUS را ادامه بده", ())
    assert result.should_resume is True
    assert result.bundle is not None
    assert not result.bundle.retrieved
    assert "canonical live sources" in result.instruction
