from __future__ import annotations

import hashlib
import json
import re
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MAX_CONVERSATIONS = 100_000
MAX_MESSAGES = 2_000_000
MAX_MESSAGE_CHARS = 1_000_000


@dataclass(frozen=True)
class ArchiveMessage:
    conversation_id: str
    message_id: str
    role: str
    created_at: float
    text: str

    @property
    def evidence_ref(self) -> str:
        return f"chat-export:{self.conversation_id}:{self.message_id}"


@dataclass(frozen=True)
class ConversationArchive:
    conversation_id: str
    title: str
    created_at: float
    updated_at: float
    messages: tuple[ArchiveMessage, ...]

    @property
    def digest(self) -> str:
        body = [(m.message_id, m.role, m.created_at, m.text) for m in self.messages]
        return hashlib.sha256(json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class GoalCandidate:
    goal_id: str
    project_hint: str
    statement: str
    evidence_ref: str
    status: str = "review_required"


@dataclass(frozen=True)
class PortfolioDecision:
    active_goal_ids: tuple[str, ...]
    execution_goal_ids: tuple[str, ...]
    queued_goal_ids: tuple[str, ...]


_GOAL_MARKERS = (
    "میخوام", "می‌خوام", "می خواهم", "هدف", "بریم برای", "انجام بده", "بساز", "طراحی کن",
    "i want", "my goal", "build", "create", "implement", "continue the project",
)

_PROJECT_TERMS = {
    "hydrostatic_tester": ("gsy", "hydrostatic", "هیدرواستاتیک", "هیدروتست"),
    "kcl_mop": ("kcl", "mop", "potassium chloride", "کلرید پتاسیم", "اورالکالی"),
    "can_forming": ("can forming", "necking", "flanging", "beading", "قوطی"),
    "heat_treatment": ("heat treatment", "walking beam", "عملیات حرارتی"),
    "food_additives": ("xanthan", "carrageenan", "vanilla flavor", "افزودنی غذایی"),
    "coffee_import": ("coffee", "قهوه"),
    "tinplate_pi": ("tinplate", "proforma", "پروفرما"),
    "portfolio_platform": ("portfolio", "next.js", "وبسایت", "سایت"),
    "ai_mastery": ("ai engineer", "هوش مصنوعی", "پایتون", "claude"),
    "personal_os": ("personal os", "سیستم شخصی", "زندگی"),
}


def _text_from_message(message: dict) -> str:
    content = message.get("content") or {}
    parts = content.get("parts") or []
    text_parts = [part for part in parts if isinstance(part, str)]
    text = "\n".join(text_parts).strip()
    if len(text) > MAX_MESSAGE_CHARS:
        raise ValueError("message_too_large")
    return text


def load_chatgpt_export(path: Path) -> tuple[ConversationArchive, ...]:
    """Load an official ChatGPT conversations JSON export without network writes."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or len(raw) > MAX_CONVERSATIONS:
        raise ValueError("invalid_conversation_export")
    archives: list[ConversationArchive] = []
    seen: dict[str, str] = {}
    message_total = 0
    for conversation in raw:
        if not isinstance(conversation, dict):
            raise ValueError("invalid_conversation_record")
        conversation_id = str(conversation.get("id") or conversation.get("conversation_id") or "").strip()
        if not conversation_id:
            raise ValueError("missing_conversation_id")
        messages: list[ArchiveMessage] = []
        mapping = conversation.get("mapping") or {}
        if not isinstance(mapping, dict):
            raise ValueError("invalid_conversation_mapping")
        for node_id, node in mapping.items():
            message = node.get("message") if isinstance(node, dict) else None
            if not isinstance(message, dict):
                continue
            author = message.get("author") or {}
            role = str(author.get("role") or "unknown")
            text = _text_from_message(message)
            if not text:
                continue
            message_id = str(message.get("id") or node_id).strip()
            messages.append(ArchiveMessage(conversation_id, message_id, role, float(message.get("create_time") or 0), text))
        messages.sort(key=lambda item: (item.created_at, item.message_id))
        message_total += len(messages)
        if message_total > MAX_MESSAGES:
            raise ValueError("message_limit_exceeded")
        archive = ConversationArchive(
            conversation_id,
            str(conversation.get("title") or "Untitled").strip(),
            float(conversation.get("create_time") or 0),
            float(conversation.get("update_time") or 0),
            tuple(messages),
        )
        previous = seen.get(conversation_id)
        if previous and previous != archive.digest:
            raise ValueError("conversation_id_collision")
        if not previous:
            archives.append(archive)
            seen[conversation_id] = archive.digest
    return tuple(sorted(archives, key=lambda item: (item.created_at, item.conversation_id)))


def _project_hint(text: str) -> str:
    lowered = text.casefold()
    scores = {project: sum(term in lowered for term in terms) for project, terms in _PROJECT_TERMS.items()}
    project, score = max(scores.items(), key=lambda item: (item[1], item[0]))
    return project if score else "unclassified"


def extract_goal_candidates(archives: Iterable[ConversationArchive]) -> tuple[GoalCandidate, ...]:
    """Extract review candidates; never promotes a chat statement to current truth."""
    results: dict[str, GoalCandidate] = {}
    for archive in archives:
        for message in archive.messages:
            if message.role != "user":
                continue
            compact = re.sub(r"\s+", " ", message.text).strip()
            if not any(marker in compact.casefold() for marker in _GOAL_MARKERS):
                continue
            statement = compact[:1_000]
            goal_id = hashlib.sha256(f"{message.evidence_ref}\n{statement}".encode()).hexdigest()[:20]
            results[goal_id] = GoalCandidate(goal_id, _project_hint(statement), statement, message.evidence_ref)
    return tuple(sorted(results.values(), key=lambda item: (item.project_hint, item.goal_id)))


def decide_portfolio(
    candidates: Iterable[GoalCandidate], *, approved_goal_ids: Iterable[str], current_active_goal_ids: Iterable[str] = (), execution_limit: int = 4
) -> PortfolioDecision:
    """Keep approved goals active while bounding only concurrent execution."""
    if not 1 <= execution_limit <= 20:
        raise ValueError("invalid_execution_limit")
    items = {item.goal_id: item for item in candidates}
    approved = tuple(dict.fromkeys(approved_goal_ids))
    if any(goal_id not in items for goal_id in approved):
        raise ValueError("unknown_goal_approval")
    active = list(dict.fromkeys((*current_active_goal_ids, *approved)))
    return PortfolioDecision(tuple(active), tuple(active[:execution_limit]), tuple(active[execution_limit:]))


def build_recovery_report(archives: Iterable[ConversationArchive], *, include_statements: bool = False) -> dict:
    items = tuple(archives)
    goals = extract_goal_candidates(items)
    return {
        "schema": "nexus.chat-recovery.v1",
        "conversation_count": len(items),
        "message_count": sum(len(item.messages) for item in items),
        "goal_candidate_count": len(goals),
        "activation_policy": "manual_review_unbounded_portfolio_bounded_execution",
        "goals": [{
            "goal_id": goal.goal_id,
            "project_hint": goal.project_hint,
            "evidence_ref": goal.evidence_ref,
            "status": goal.status,
            **({"statement": goal.statement} if include_statements else {}),
        } for goal in goals],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Recover a ChatGPT export into a local NEXUS review report.")
    parser.add_argument("input", type=Path, help="Path to conversations.json")
    parser.add_argument("--output", type=Path, default=Path("nexus_chat_recovery_report.json"))
    parser.add_argument("--include-statements", action="store_true")
    args = parser.parse_args()
    report = build_recovery_report(load_chatgpt_export(args.input), include_statements=args.include_statements)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
