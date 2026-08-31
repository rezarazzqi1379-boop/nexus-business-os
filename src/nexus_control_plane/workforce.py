from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Department(str, Enum):
    SALES = "sales"
    DEALS = "deals"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    INTELLIGENCE = "intelligence"
    CUSTOMER = "customer"
    BACK_OFFICE = "back_office"
    NEXUS_CORE = "nexus_core"


class ActionClass(str, Enum):
    READ = "read"
    RESEARCH = "research"
    DRAFT = "draft"
    INTERNAL_WRITE = "internal_write"
    EXTERNAL_WRITE = "external_write"
    FINANCIAL = "financial"


class EvidenceClass(str, Enum):
    OBSERVED_PUBLIC = "observed_public"
    NEXUS_ORIGINAL = "nexus_original"
    INFERRED_EQUIVALENT = "inferred_equivalent"


@dataclass(frozen=True)
class CapabilitySpec:
    capability_id: str
    label: str
    department: Department
    action_class: ActionClass
    evidence_class: EvidenceClass
    description: str
    source_ref: str | None = None
    requires_human_approval: bool = False

    def validate(self) -> None:
        if not self.capability_id or self.capability_id.strip() != self.capability_id:
            raise ValueError("capability_id must be canonical")
        if not self.label.strip():
            raise ValueError("label is required")
        if self.evidence_class is EvidenceClass.OBSERVED_PUBLIC and not self.source_ref:
            raise ValueError("publicly observed capabilities require a source_ref")
        if self.action_class in {ActionClass.EXTERNAL_WRITE, ActionClass.FINANCIAL} and not self.requires_human_approval:
            raise ValueError("consequential capabilities must require human approval")


# Publicly visible Altari/SkillTree job labels only. This registry deliberately
# does not claim access to paid/internal workflows, prompts, hidden files, or
# implementation details.
PUBLIC_PATTERN_CAPABILITIES: tuple[CapabilitySpec, ...] = (
    CapabilitySpec("sales.outbound_writer", "Outbound Writer", Department.SALES, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Draft personalized outbound from live prospect signals.", "https://skilltree.altari.ai/"),
    CapabilitySpec("sales.lead_sourcing", "Lead Sourcing", Department.SALES, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Discover and qualify prospective accounts/leads.", "https://skilltree.altari.ai/"),
    CapabilitySpec("sales.cold_call_scripts", "Cold-Call Scripts", Department.SALES, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Prepare call scripts from account context.", "https://altari.ai/"),
    CapabilitySpec("sales.sdr_outreach", "SDR Outreach", Department.SALES, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Prepare SDR outreach actions and drafts.", "https://altari.ai/"),
    CapabilitySpec("sales.cold_email", "Cold Email", Department.SALES, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Prepare targeted cold-email drafts.", "https://altari.ai/"),
    CapabilitySpec("sales.deal_follow_up", "Deal Follow-up", Department.SALES, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Detect and draft deal follow-up actions.", "https://altari.ai/"),
    CapabilitySpec("sales.objection_handler", "Objection Handler", Department.SALES, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Prepare evidence-aware responses to objections.", "https://altari.ai/"),
    CapabilitySpec("sales.linkedin_outreach", "LinkedIn Outreach", Department.SALES, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Draft LinkedIn outreach from prospect context.", "https://skilltree.altari.ai/"),
    CapabilitySpec("deals.proposal_writer", "Proposal Writer", Department.DEALS, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Draft proposals from call notes, requirements, and prior deal context.", "https://skilltree.altari.ai/"),
    CapabilitySpec("deals.follow_ups", "Follow-Ups", Department.DEALS, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Prepare follow-up drafts and next-step reminders.", "https://altari.ai/"),
    CapabilitySpec("deals.meeting_recaps", "Meeting Recaps", Department.DEALS, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Extract decisions, owners, and next actions from meetings.", "https://skilltree.altari.ai/"),
    CapabilitySpec("marketing.content_engine", "Content Engine", Department.MARKETING, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Turn source ideas into reusable content outputs.", "https://altari.ai/"),
    CapabilitySpec("marketing.carousel_designer", "Carousel Designer", Department.MARKETING, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Structure carousel content and assets.", "https://skilltree.altari.ai/"),
    CapabilitySpec("marketing.seo_briefs", "SEO Briefs", Department.MARKETING, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Create SEO content briefs from research.", "https://altari.ai/"),
    CapabilitySpec("marketing.ad_campaigns", "Ad Campaigns", Department.MARKETING, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Prepare ad campaign strategy and creative drafts.", "https://altari.ai/"),
    CapabilitySpec("marketing.seo_web", "SEO & Web", Department.MARKETING, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Prepare SEO/web optimization work.", "https://altari.ai/"),
    CapabilitySpec("marketing.social_scheduler", "Social Scheduler", Department.MARKETING, ActionClass.INTERNAL_WRITE, EvidenceClass.OBSERVED_PUBLIC, "Prepare scheduled social publishing plans; live publishing remains separately gated.", "https://altari.ai/", True),
    CapabilitySpec("marketing.reel_analyst", "Reel Analyst", Department.MARKETING, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Analyze short-form content patterns and performance signals.", "https://skilltree.altari.ai/"),
    CapabilitySpec("marketing.content_repurposer", "Content Repurposer", Department.MARKETING, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Repurpose a source asset across channels.", "https://skilltree.altari.ai/"),
    CapabilitySpec("marketing.hook_writer", "Hook Writer", Department.MARKETING, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Generate and test opening hooks for content.", "https://skilltree.altari.ai/"),
    CapabilitySpec("marketing.trend_analyst", "Trend Analyst", Department.MARKETING, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Research relevant content/market trends.", "https://skilltree.altari.ai/"),
    CapabilitySpec("operations.client_onboarding", "Client Onboarding", Department.OPERATIONS, ActionClass.INTERNAL_WRITE, EvidenceClass.OBSERVED_PUBLIC, "Coordinate onboarding checklists and internal records.", "https://altari.ai/", True),
    CapabilitySpec("operations.client_ops", "Client Ops", Department.OPERATIONS, ActionClass.INTERNAL_WRITE, EvidenceClass.OBSERVED_PUBLIC, "Coordinate recurring client operations.", "https://altari.ai/", True),
    CapabilitySpec("operations.status_updates", "Status Updates", Department.OPERATIONS, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Generate project/client status updates from current state.", "https://altari.ai/"),
    CapabilitySpec("operations.scheduling", "Scheduling", Department.OPERATIONS, ActionClass.INTERNAL_WRITE, EvidenceClass.OBSERVED_PUBLIC, "Prepare or perform scheduling actions subject to authority.", "https://altari.ai/", True),
    CapabilitySpec("operations.support_triage", "Support Triage", Department.OPERATIONS, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Classify inbound support and route next actions.", "https://altari.ai/"),
    CapabilitySpec("operations.doc_processing", "Doc Processing", Department.OPERATIONS, ActionClass.READ, EvidenceClass.OBSERVED_PUBLIC, "Extract structured data and action items from documents.", "https://altari.ai/"),
    CapabilitySpec("intelligence.prospect_dossiers", "Prospect Dossiers", Department.INTELLIGENCE, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Build evidence-backed prospect dossiers.", "https://altari.ai/"),
    CapabilitySpec("intelligence.competitor_watch", "Competitor Watch", Department.INTELLIGENCE, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Monitor competitor changes and assess implications.", "https://skilltree.altari.ai/"),
    CapabilitySpec("intelligence.market_sizing", "Market Sizing", Department.INTELLIGENCE, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Estimate market scope using explicit evidence and assumptions.", "https://altari.ai/"),
    CapabilitySpec("intelligence.prospect_research", "Prospect Research", Department.INTELLIGENCE, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Research prospects from multiple sources.", "https://skilltree.altari.ai/"),
    CapabilitySpec("intelligence.company_research", "Company Research", Department.INTELLIGENCE, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Build company intelligence from retrievable sources.", "https://skilltree.altari.ai/"),
    CapabilitySpec("intelligence.buying_committee_mapping", "Buying-Committee Mapping", Department.INTELLIGENCE, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Map likely business decision participants without treating inference as fact.", "https://skilltree.altari.ai/"),
    CapabilitySpec("customer.support_answerer", "Support Answerer", Department.CUSTOMER, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Draft support answers grounded in the company knowledge base.", "https://skilltree.altari.ai/"),
    CapabilitySpec("customer.faq_engine", "FAQ Engine", Department.CUSTOMER, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Maintain FAQ answer drafts from validated knowledge.", "https://altari.ai/"),
    CapabilitySpec("customer.churn_watch", "Churn Watch", Department.CUSTOMER, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Detect customer-risk signals for human review.", "https://altari.ai/"),
    CapabilitySpec("back_office.invoice_generator", "Invoice Generator", Department.BACK_OFFICE, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Prepare invoice drafts from approved commercial data.", "https://skilltree.altari.ai/"),
    CapabilitySpec("back_office.invoicing", "Invoicing", Department.BACK_OFFICE, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Prepare invoicing work from approved records.", "https://altari.ai/"),
    CapabilitySpec("back_office.reconciliation", "Reconciliation", Department.BACK_OFFICE, ActionClass.RESEARCH, EvidenceClass.OBSERVED_PUBLIC, "Compare records and surface reconciliation differences.", "https://altari.ai/"),
    CapabilitySpec("back_office.reporting", "Reporting", Department.BACK_OFFICE, ActionClass.DRAFT, EvidenceClass.OBSERVED_PUBLIC, "Generate operational/financial reports from verified data.", "https://altari.ai/"),
    CapabilitySpec("back_office.expense_tracking", "Expense Tracking", Department.BACK_OFFICE, ActionClass.INTERNAL_WRITE, EvidenceClass.OBSERVED_PUBLIC, "Prepare expense classifications/records subject to internal authority.", "https://altari.ai/", True),
    CapabilitySpec("back_office.expense_coding", "Expense Coding", Department.BACK_OFFICE, ActionClass.INTERNAL_WRITE, EvidenceClass.OBSERVED_PUBLIC, "Prepare expense-coding suggestions/records subject to internal authority.", "https://altari.ai/", True),
)


NEXUS_NATIVE_CAPABILITIES: tuple[CapabilitySpec, ...] = (
    CapabilitySpec("nexus.evidence_verifier", "Evidence Verifier", Department.NEXUS_CORE, ActionClass.RESEARCH, EvidenceClass.NEXUS_ORIGINAL, "Separate Fact, Claim, Estimate, Inference, Hypothesis, Assumption and Unknown; preserve provenance."),
    CapabilitySpec("nexus.engineering_reviewer", "Engineering Reviewer", Department.NEXUS_CORE, ActionClass.RESEARCH, EvidenceClass.NEXUS_ORIGINAL, "Compare supplier evidence against authority-ranked technical requirements and fail closed on blockers."),
    CapabilitySpec("nexus.opportunity_scout", "Opportunity Scout", Department.NEXUS_CORE, ActionClass.RESEARCH, EvidenceClass.NEXUS_ORIGINAL, "Discover and score commercial opportunities without granting outreach authority."),
    CapabilitySpec("nexus.duplicate_guard", "Duplicate Guard", Department.NEXUS_CORE, ActionClass.READ, EvidenceClass.NEXUS_ORIGINAL, "Prevent duplicate outreach/actions by checking prior communications and action fingerprints."),
    CapabilitySpec("nexus.approval_gateway", "Approval Gateway", Department.NEXUS_CORE, ActionClass.EXTERNAL_WRITE, EvidenceClass.NEXUS_ORIGINAL, "Authorize only exact consequential actions after human approval.", requires_human_approval=True),
    CapabilitySpec("nexus.qa_evaluator", "QA / Evaluator", Department.NEXUS_CORE, ActionClass.READ, EvidenceClass.NEXUS_ORIGINAL, "Run deterministic and adversarial checks before promotion or consequential execution."),
    CapabilitySpec("nexus.learning_governor", "Learning Governor", Department.NEXUS_CORE, ActionClass.INTERNAL_WRITE, EvidenceClass.NEXUS_ORIGINAL, "Convert measured outcomes into versioned improvement proposals; never self-promote without gates.", requires_human_approval=True),
)


def catalog() -> tuple[CapabilitySpec, ...]:
    capabilities = PUBLIC_PATTERN_CAPABILITIES + NEXUS_NATIVE_CAPABILITIES
    for capability in capabilities:
        capability.validate()
    ids = [capability.capability_id for capability in capabilities]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate capability_id")
    return capabilities


def select_capabilities(*, departments: Iterable[Department] | None = None, action_classes: Iterable[ActionClass] | None = None) -> tuple[CapabilitySpec, ...]:
    selected = catalog()
    if departments is not None:
        allowed_departments = set(departments)
        selected = tuple(item for item in selected if item.department in allowed_departments)
    if action_classes is not None:
        allowed_actions = set(action_classes)
        selected = tuple(item for item in selected if item.action_class in allowed_actions)
    return selected
