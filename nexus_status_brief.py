"""Read-only NEXUS status brief.

Answers "where do things stand right now?" by reading existing canonical sources
(projects.py's registry, and optionally the opportunity/approval SQLite stores this
session added) -- it changes nothing and calls nobody. Output is structured data;
render_persian_brief() turns it into a short Persian summary for a human to skim.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from projects import PROJECTS, ProjectPolicy

STATUS_ORDER = ("blocked", "active", "research", "hold", "separate_workstream")
STATUS_LABELS_FA = {
    "active": "فعال",
    "research": "در حال تحقیق",
    "hold": "متوقف (نگه‌داشته‌شده)",
    "blocked": "مسدود",
    "separate_workstream": "جریان کاری جدا",
}


@dataclass(frozen=True)
class ProjectsByStatus:
    status: str
    projects: tuple[ProjectPolicy, ...]


def group_projects_by_status(projects: dict[str, ProjectPolicy] = PROJECTS) -> tuple[ProjectsByStatus, ...]:
    buckets: dict[str, list[ProjectPolicy]] = {status: [] for status in STATUS_ORDER}
    for policy in projects.values():
        buckets.setdefault(policy.status, []).append(policy)
    ordered_statuses = list(STATUS_ORDER) + [s for s in buckets if s not in STATUS_ORDER]
    return tuple(
        ProjectsByStatus(status, tuple(sorted(buckets[status], key=lambda p: -p.priority)))
        for status in ordered_statuses if buckets.get(status)
    )


def count_pending_opportunities(db_path: Optional[Path]) -> Optional[int]:
    """Count drafts still waiting on a human, if the opportunity queue DB exists.
    Returns None (not an error) if the DB hasn't been created yet -- absence of
    activity isn't a fault."""
    if db_path is None or not db_path.exists():
        return None
    import sqlite3
    from contextlib import closing
    with closing(sqlite3.connect(db_path)) as db:
        row = db.execute(
            "SELECT COUNT(*) FROM opportunity_drafts WHERE review_status='draft_pending_review'"
        ).fetchone()
        return row[0] if row else 0


def count_pending_approvals(db_path: Optional[Path]) -> Optional[int]:
    if db_path is None or not db_path.exists():
        return None
    import sqlite3
    from contextlib import closing
    with closing(sqlite3.connect(db_path)) as db:
        row = db.execute("SELECT COUNT(*) FROM approvals WHERE status='pending'").fetchone()
        return row[0] if row else 0


def render_persian_brief(
    *,
    opportunities_db: Optional[Path] = None,
    approvals_db: Optional[Path] = None,
    projects: dict[str, ProjectPolicy] = PROJECTS,
) -> str:
    lines = ["# خلاصهٔ وضعیت NEXUS", ""]
    for bucket in group_projects_by_status(projects):
        label = STATUS_LABELS_FA.get(bucket.status, bucket.status)
        lines.append(f"## {label} ({len(bucket.projects)})")
        for p in bucket.projects:
            forbidden = f" — ممنوع: {', '.join(p.forbidden_actions)}" if p.forbidden_actions else ""
            lines.append(f"- **{p.project_id}** (اولویت {p.priority}): {p.objective}{forbidden}")
            if p.next_evidence:
                lines.append(f"  شواهد بعدی لازم: {', '.join(p.next_evidence)}")
        lines.append("")

    pending_opp = count_pending_opportunities(opportunities_db)
    pending_apr = count_pending_approvals(approvals_db)
    if pending_opp is not None or pending_apr is not None:
        lines.append("## در انتظار تصمیم انسانی")
        if pending_opp is not None:
            lines.append(f"- {pending_opp} پیش‌نویس فرصت در صف بررسی (Opportunity Suggestion Engine)")
        if pending_apr is not None:
            lines.append(f"- {pending_apr} درخواست تایید در انتظار (Approval Store)")
    return "\n".join(lines)
