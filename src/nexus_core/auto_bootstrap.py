from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from nexus_core.chat_memory_mesh import ChatShard, MemoryBundle, build_cross_chat_bootstrap, retrieve_chat_context


@dataclass(frozen=True)
class BootstrapDecision:
    should_resume: bool
    confidence: str
    project_refs: tuple[str, ...]
    goal_refs: tuple[str, ...]
    matched_domains: tuple[str, ...]
    bundle: MemoryBundle | None
    instruction: str


_DOMAIN_TERMS: dict[str, tuple[str, ...]] = {
    "commercial": (
        "supplier", "buyer", "customer", "procurement", "rfq", "quote", "deal", "kcl", "mop",
        "hydrotester", "octg", "تامین", "تأمین", "مشتری", "خریدار", "فروش", "تجارت", "بازرگانی",
    ),
    "engineering": (
        "github", "code", "coding", "python", "agent", "rag", "api", "database", "supabase", "vercel",
        "کد", "کدنویسی", "برنامه", "هوش مصنوعی", "ایجنت", "دیتابیس",
    ),
    "research": (
        "research", "paper", "science", "experiment", "hypothesis", "scispace", "study", "پژوهش", "علم", "مقاله", "آزمایش",
    ),
    "network": (
        "network", "linkedin", "apollo", "hubspot", "contact", "intermediary", "واسطه", "شبکه", "ارتباط", "کانتکت",
    ),
    "recovery": (
        "backup", "restore", "resume", "continuity", "checkpoint", "chat", "بکاپ", "بازیابی", "چت", "ادامه",
    ),
    "brand": (
        "brand", "instagram", "marketing", "website", "logo", "برند", "اینستاگرام", "مارکتینگ", "سایت", "لوگو",
    ),
    "learning": (
        "english", "russian", "learn", "course", "training", "انگلیسی", "روسی", "یادگیری", "آموزش",
    ),
    "health": (
        "health", "fitness", "crossfit", "sleep", "supplement", "سلامت", "فیتنس", "کراسفیت", "خواب", "مکمل",
    ),
}

_PROJECT_HINTS: dict[str, tuple[str, ...]] = {
    "kcl-mop": ("kcl", "mop", "potassium chloride", "کلرید پتاسیم"),
    "hydrotester": ("hydrotester", "gsy-180", "gsy180", "هیدروتستر"),
    "octg-heat-treatment": ("octg", "heat treatment", "quench", "temper", "نرمالایز"),
    "can-end-forming": ("necking", "flanging", "beading", "end forming", "قوطی"),
    "nexus-core": ("nexus", "github", "agent", "rag", "supabase", "vercel", "کدنویسی", "هوش مصنوعی"),
    "personal-brand": ("brand", "instagram", "website", "logo", "برند", "اینستاگرام", "سایت"),
}

_GOAL_BY_DOMAIN = {
    "commercial": "commercial-revenue",
    "engineering": "ai-engineering",
    "research": "research-science",
    "network": "customer-network",
    "recovery": "backup-recovery",
    "brand": "personal-brand",
    "learning": "learning",
    "health": "health-fitness",
}


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def detect_nexus_scope(message: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Infer NEXUS scope from the user's first meaningful message.

    This router is intentionally deterministic and conservative: it triggers recovery when
    the message intersects known NEXUS domains, but it never treats domain detection as
    authorization for external or consequential actions.
    """
    if not isinstance(message, str) or not message.strip():
        raise ValueError("invalid_message")
    text = _normalize(message)

    domains = tuple(
        domain
        for domain, terms in _DOMAIN_TERMS.items()
        if any(term in text for term in terms)
    )
    projects = tuple(
        project
        for project, terms in _PROJECT_HINTS.items()
        if any(term in text for term in terms)
    )
    goals = tuple(dict.fromkeys(_GOAL_BY_DOMAIN[d] for d in domains if d in _GOAL_BY_DOMAIN))
    return domains, projects, goals


def auto_bootstrap(
    message: str,
    shards: Iterable[ChatShard],
    *,
    max_shards: int = 10,
) -> BootstrapDecision:
    domains, projects, goals = detect_nexus_scope(message)
    if not domains and not projects:
        return BootstrapDecision(
            should_resume=False,
            confidence="none",
            project_refs=(),
            goal_refs=(),
            matched_domains=(),
            bundle=None,
            instruction="Handle as a normal standalone request; do not fabricate NEXUS context.",
        )

    bundle = retrieve_chat_context(
        shards,
        query=message,
        project_refs=projects,
        goal_refs=goals,
        limit=max_shards,
    )
    confidence = "high" if projects or len(domains) >= 2 else "medium"
    bootstrap = build_cross_chat_bootstrap(bundle)
    instruction = (
        "AUTO-RESUME NEXUS. The user did not need to type a resume command. "
        + bootstrap
        + " Infer missing project scope only from retrieved/canonical evidence, not guesses. "
        "Ask a question only when the missing fact blocks the next high-value safe action and cannot be resolved from connected sources. "
        "Batch internal reversible work aggressively before returning; preserve Human Gates for consequential actions."
    )
    return BootstrapDecision(
        should_resume=True,
        confidence=confidence,
        project_refs=projects,
        goal_refs=goals,
        matched_domains=domains,
        bundle=bundle,
        instruction=instruction,
    )
