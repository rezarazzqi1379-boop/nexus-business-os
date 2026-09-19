from dataclasses import dataclass
from typing import Literal


RequestedScope = Literal["necking_only", "full_forming"]
QuoteScope = Literal["necking_only", "full_forming", "full_production_line", "unknown"]
FitStatus = Literal["aligned", "misaligned", "blocked"]
EvidenceClass = Literal["fact", "claim", "estimate", "assumption", "unknown"]


@dataclass(frozen=True)
class CanFormingRequirement:
    requirement_id: str
    project_id: str
    diameter_mm: int
    requested_scope: RequestedScope
    existing_line_cpm: int
    source_ref: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.requirement_id.strip():
            errors.append("requirement_id is required")
        if not self.project_id.strip():
            errors.append("project_id is required")
        if self.diameter_mm <= 0:
            errors.append("diameter_mm must be positive")
        if self.requested_scope not in {"necking_only", "full_forming"}:
            errors.append("unsupported requested_scope")
        if self.existing_line_cpm <= 0:
            errors.append("existing_line_cpm must be positive")
        if not self.source_ref.strip():
            errors.append("source_ref is required")
        return errors


@dataclass(frozen=True)
class SupplierQuote:
    quote_id: str
    supplier: str
    diameter_mm: int
    quoted_scope: QuoteScope
    price_usd: float
    incoterm: str
    max_cpm: int | None
    stable_cpm: int | None
    speed_evidence_class: EvidenceClass
    source_ref: str
    clarification_already_sent: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name, value in (
            ("quote_id", self.quote_id),
            ("supplier", self.supplier),
            ("incoterm", self.incoterm),
            ("source_ref", self.source_ref),
        ):
            if not value.strip():
                errors.append(f"{name} is required")
        if self.diameter_mm <= 0:
            errors.append("diameter_mm must be positive")
        if self.price_usd <= 0:
            errors.append("price_usd must be positive")
        if self.quoted_scope not in {"necking_only", "full_forming", "full_production_line", "unknown"}:
            errors.append("unsupported quoted_scope")
        if self.speed_evidence_class not in {"fact", "claim", "estimate", "assumption", "unknown"}:
            errors.append("unsupported speed_evidence_class")
        for name, value in (("max_cpm", self.max_cpm), ("stable_cpm", self.stable_cpm)):
            if value is not None and value <= 0:
                errors.append(f"{name} must be positive when present")
        return errors


@dataclass(frozen=True)
class ScopeAssessment:
    quote_id: str
    requested_scope: RequestedScope
    fit_status: FitStatus
    scope_conflict: bool
    throughput_gap_cpm: int | None
    throughput_verified: bool
    duplicate_followup_blocked: bool
    blockers: tuple[str, ...]


def assess_quote(requirement: CanFormingRequirement, quote: SupplierQuote) -> ScopeAssessment:
    """Evaluate scope and throughput without converting supplier claims into verified performance."""
    errors = requirement.validate() + quote.validate()
    if errors or requirement.project_id != "can-forming" or requirement.diameter_mm != quote.diameter_mm:
        return ScopeAssessment(
            quote_id=quote.quote_id,
            requested_scope=requirement.requested_scope,
            fit_status="blocked",
            scope_conflict=True,
            throughput_gap_cpm=None,
            throughput_verified=False,
            duplicate_followup_blocked=quote.clarification_already_sent,
            blockers=tuple(errors or ("project or diameter mismatch",)),
        )

    scope_conflict = quote.quoted_scope != requirement.requested_scope
    blockers: list[str] = []
    if scope_conflict:
        blockers.append(
            f"quoted scope {quote.quoted_scope} is not equivalent to requested scope {requirement.requested_scope}"
        )

    throughput_verified = quote.speed_evidence_class == "fact"
    throughput_gap = None
    if quote.stable_cpm is None:
        blockers.append("stable CPM is missing")
    else:
        throughput_gap = requirement.existing_line_cpm - quote.stable_cpm
        if throughput_gap > 0:
            blockers.append(
                f"supplier-stated stable CPM is {throughput_gap} below existing line rating; required continuous throughput remains unresolved"
            )

    if not throughput_verified:
        blockers.append("speed is supplier claim/unverified evidence, not accepted throughput")

    fit_status: FitStatus = "aligned" if not blockers else "misaligned"
    return ScopeAssessment(
        quote_id=quote.quote_id,
        requested_scope=requirement.requested_scope,
        fit_status=fit_status,
        scope_conflict=scope_conflict,
        throughput_gap_cpm=throughput_gap,
        throughput_verified=throughput_verified,
        duplicate_followup_blocked=quote.clarification_already_sent,
        blockers=tuple(blockers),
    )
