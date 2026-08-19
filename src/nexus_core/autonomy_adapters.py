from nexus_core.autonomy import WorkItem


def inbox_reply_work_item(
    *,
    message_ref: str,
    thread_key: str,
    decision_relevant: bool,
    external_reply_needed: bool,
) -> WorkItem:
    if external_reply_needed:
        return WorkItem(
            task_id=f"reply-review:{thread_key}",
            domain="inbox_monitoring",
            objective="Review a decision-relevant inbox reply and prepare the next external response.",
            action_kind="draft",
            acceptable_capability_ids=("gmail.read", "notion.write"),
            evidence_refs=(message_ref,),
            value="high" if decision_relevant else "medium",
            urgency="high" if decision_relevant else "medium",
            evidence="strong",
            cost="low",
        )
    return WorkItem(
        task_id=f"inbox-monitor:{thread_key}",
        domain="inbox_monitoring",
        objective="Review the inbox signal and update internal project state if it changes a decision.",
        action_kind="read",
        acceptable_capability_ids=("gmail.read",),
        evidence_refs=(message_ref,),
        value="high" if decision_relevant else "low",
        urgency="high" if decision_relevant else "low",
        evidence="strong",
        cost="low",
    )


def ci_failure_work_item(*, run_ref: str, branch_key: str) -> WorkItem:
    return WorkItem(
        task_id=f"ci-failure:{branch_key}",
        domain="security",
        objective="Inspect the failed CI run, identify the failing contract, and prepare a reversible fix with regression coverage.",
        action_kind="branch_commit",
        acceptable_capability_ids=("github.write",),
        evidence_refs=(run_ref,),
        value="high",
        urgency="high",
        evidence="strong",
        cost="medium",
        write_required=True,
    )


def research_signal_work_item(*, source_ref: str, topic_key: str, decision_relevant: bool) -> WorkItem:
    return WorkItem(
        task_id=f"research:{topic_key}",
        domain="research",
        objective="Verify the research signal against primary or authoritative sources and record only decision-relevant findings.",
        action_kind="research",
        acceptable_capability_ids=("web.search", "exa.search"),
        evidence_refs=(source_ref,),
        value="high" if decision_relevant else "medium",
        urgency="medium",
        evidence="partial",
        cost="medium",
    )


def customer_network_research_work_item(*, source_ref: str, market_key: str, commercially_relevant: bool) -> WorkItem:
    return WorkItem(
        task_id=f"customer-network:{market_key}",
        domain="customer_network",
        objective="Map and qualify potential customers, buyers, integrators and decision-maker paths using retrievable evidence; prepare candidates for human-reviewed outreach only.",
        action_kind="research",
        acceptable_capability_ids=("web.search", "exa.search", "linkedin.read"),
        evidence_refs=(source_ref,),
        value="high" if commercially_relevant else "medium",
        urgency="medium",
        evidence="partial",
        cost="medium",
    )


def learning_signal_work_item(*, source_ref: str, topic_key: str, implementation_relevant: bool) -> WorkItem:
    return WorkItem(
        task_id=f"learning:{topic_key}",
        domain="coding_learning",
        objective="Study the authoritative technical source, extract only implementation-relevant techniques, compare them with the current NEXUS architecture, and propose a testable code or review change if justified.",
        action_kind="research",
        acceptable_capability_ids=("web.search", "exa.search", "github.read"),
        evidence_refs=(source_ref,),
        value="high" if implementation_relevant else "medium",
        urgency="medium" if implementation_relevant else "low",
        evidence="partial",
        cost="medium",
    )


def news_signal_work_item(*, source_ref: str, topic_key: str, business_impact: bool) -> WorkItem:
    return WorkItem(
        task_id=f"news:{topic_key}",
        domain="news_monitoring",
        objective="Verify the news signal against authoritative or primary sources, identify concrete business impact, and record only changes that alter a decision, risk, route, supplier, buyer or market assumption.",
        action_kind="research",
        acceptable_capability_ids=("web.search", "exa.search"),
        evidence_refs=(source_ref,),
        value="high" if business_impact else "low",
        urgency="high" if business_impact else "low",
        evidence="partial",
        cost="low",
    )


def backup_due_work_item(*, source_ref: str, scope_key: str) -> WorkItem:
    return WorkItem(
        task_id=f"backup:{scope_key}",
        domain="backup",
        objective="Create a categorized internal backup manifest for the selected NEXUS scope without deleting or moving source data.",
        action_kind="internal_record_write",
        acceptable_capability_ids=("notion.write", "drive.write"),
        evidence_refs=(source_ref,),
        value="high",
        urgency="medium",
        evidence="strong",
        cost="low",
        write_required=True,
    )


def plugin_candidate_work_item(*, source_ref: str, plugin_key: str) -> WorkItem:
    return WorkItem(
        task_id=f"plugin-review:{plugin_key}",
        domain="innovation",
        objective="Evaluate a candidate plugin or connector for unique value, overlap, permissions, security risk and measurable benefit before any installation or access change.",
        action_kind="research",
        acceptable_capability_ids=("plugin.catalog", "web.search"),
        evidence_refs=(source_ref,),
        value="medium",
        urgency="low",
        evidence="partial",
        cost="low",
    )


def plugin_connect_work_item(*, source_ref: str, plugin_key: str) -> WorkItem:
    return WorkItem(
        task_id=f"plugin-connect:{plugin_key}",
        domain="innovation",
        objective="Connect the reviewed plugin or connector using the minimum required permissions.",
        action_kind="change_access",
        acceptable_capability_ids=("plugin.manage",),
        evidence_refs=(source_ref,),
        value="medium",
        urgency="low",
        evidence="strong",
        cost="low",
        write_required=True,
    )
