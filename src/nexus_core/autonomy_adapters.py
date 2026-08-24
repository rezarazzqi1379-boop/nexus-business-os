from nexus_core.autonomy import WorkItem


def inbox_reply_work_item(*, message_ref: str, thread_key: str, decision_relevant: bool, external_reply_needed: bool) -> WorkItem:
    if external_reply_needed:
        return WorkItem(f"reply-review:{thread_key}", "inbox_monitoring", "Review a decision-relevant inbox reply and prepare the next external response.", "draft", ("gmail.read", "notion.write"), (message_ref,), "high" if decision_relevant else "medium", "high" if decision_relevant else "medium", "strong", "low", False, True, goal_ref=f"goal:commercial-thread:{thread_key}", success_signal="A verified blocker is resolved or a human-reviewed next response is ready with no invented facts.", failure_signal="The thread remains blocked because required engineering/commercial evidence is still missing or the reply would rely on an unsupported claim.")
    return WorkItem(f"inbox-monitor:{thread_key}", "inbox_monitoring", "Review the inbox signal and update internal project state if it changes a decision.", "read", ("gmail.read",), (message_ref,), "high" if decision_relevant else "low", "high" if decision_relevant else "low", "strong", "low", False, True, goal_ref=f"goal:commercial-thread:{thread_key}", success_signal="A decision-relevant state change is identified and linked to retrievable evidence.", failure_signal="No material state change is found; do not generate follow-up work merely for activity.")

def ci_failure_work_item(*, run_ref: str, branch_key: str) -> WorkItem:
    return WorkItem(f"ci-failure:{branch_key}", "security", "Inspect the failed CI run, identify the failing contract, and prepare a reversible fix with regression coverage.", "branch_commit", ("github.write",), (run_ref,), "high", "high", "strong", "medium", True)

def research_signal_work_item(*, source_ref: str, topic_key: str, decision_relevant: bool) -> WorkItem:
    return WorkItem(f"research:{topic_key}", "research", "Verify the research signal against primary or authoritative sources and record only decision-relevant findings.", "research", ("web.search", "exa.search"), (source_ref,), "high" if decision_relevant else "medium", "medium", "partial", "medium")

def cross_ai_review_work_item(*, source_ref: str, review_key: str, code_change_relevant: bool, reviewer_read_code: bool = False) -> WorkItem:
    return WorkItem(task_id=f"cross-ai-review:{review_key}", domain="security" if code_change_relevant else "research", objective="Verify the external AI review against the current GitHub head, tests, security policy and retrievable evidence before accepting any finding or proposing a reversible change; the review itself is not authorization, trusted evidence, or merge approval.", action_kind="research", acceptable_capability_ids=("github.read",), evidence_refs=(source_ref,), value="high" if code_change_relevant else "medium", urgency="high" if code_change_relevant else "medium", evidence="partial" if reviewer_read_code else "unverified", cost="low")

def customer_network_research_work_item(*, source_ref: str, market_key: str, commercially_relevant: bool) -> WorkItem:
    return WorkItem(f"customer-network:{market_key}", "customer_network", "Map and qualify potential customers, buyers, integrators and decision-maker paths using retrievable evidence; prepare candidates for human-reviewed outreach only.", "research", ("web.search", "exa.search", "linkedin.read"), (source_ref,), "high" if commercially_relevant else "medium", "medium", "partial", "medium", False, True, goal_ref=f"goal:customer-network:{market_key}", success_signal="At least one prospect has a verified company fit plus a retrievable buyer/decision-maker or contact path suitable for human review.", failure_signal="Research produces only unverified names, generic directories, duplicate leads or no credible purchasing/fit evidence; kill or narrow the search loop.")

def learning_signal_work_item(*, source_ref: str, topic_key: str, implementation_relevant: bool) -> WorkItem:
    return WorkItem(f"learning:{topic_key}", "coding_learning", "Study the authoritative technical source, extract only implementation-relevant techniques, compare them with the current NEXUS architecture, and propose a testable code or review change if justified.", "research", ("web.search", "exa.search", "github.read"), (source_ref,), "high" if implementation_relevant else "medium", "medium" if implementation_relevant else "low", "partial", "medium", False, True, goal_ref=f"goal:technical-learning:{topic_key}", success_signal="The source yields a testable implementation, regression, security rule, architecture decision or explicit no-action conclusion tied to an active NEXUS need.", failure_signal="The source produces only passive summary or novelty with no measurable effect on an active requirement; do not retain it as active work.")

def news_signal_work_item(*, source_ref: str, topic_key: str, business_impact: bool) -> WorkItem:
    return WorkItem(f"news:{topic_key}", "news_monitoring", "Verify the news signal against authoritative or primary sources, identify concrete business impact, and record only changes that alter a decision, risk, route, supplier, buyer or market assumption.", "research", ("web.search", "exa.search"), (source_ref,), "high" if business_impact else "low", "high" if business_impact else "low", "partial", "low")

def backup_due_work_item(*, source_ref: str, scope_key: str) -> WorkItem:
    return WorkItem(f"backup:{scope_key}", "backup", "Create a categorized internal backup manifest for the selected NEXUS scope without deleting or moving source data.", "internal_record_write", ("notion.write", "drive.write"), (source_ref,), "high", "medium", "strong", "low", True)

def plugin_candidate_work_item(*, source_ref: str, plugin_key: str) -> WorkItem:
    return WorkItem(f"plugin-review:{plugin_key}", "innovation", "Evaluate a candidate plugin or connector for unique value, overlap, permissions, security risk and measurable benefit before any installation or access change.", "research", ("plugin.catalog", "web.search"), (source_ref,), "medium", "low", "partial", "low")

def plugin_connect_work_item(*, source_ref: str, plugin_key: str) -> WorkItem:
    return WorkItem(f"plugin-connect:{plugin_key}", "innovation", "Connect the reviewed plugin or connector using the minimum required permissions.", "change_access", ("plugin.manage",), (source_ref,), "medium", "low", "strong", "low", True)
