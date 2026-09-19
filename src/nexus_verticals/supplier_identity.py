from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable
from urllib.parse import urlparse


class OutreachDecision(str, Enum):
    ALLOW = "allow"
    HOLD_DUPLICATE_SOURCE = "hold_duplicate_source"
    REVIEW_POSSIBLE_COLLISION = "review_possible_collision"


def _norm(value: str) -> str:
    return " ".join(value.casefold().strip().split())


def _norm_domain(value: str) -> str:
    raw = value.strip().casefold()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = parsed.hostname or ""
    return host.removeprefix("www.")


def _norm_email(value: str) -> str:
    return value.casefold().strip()


@dataclass(frozen=True)
class SupplierIdentity:
    supplier_id: str
    legal_name: str
    brand: str = ""
    domain: str = ""
    country: str = ""
    city: str = ""
    factory_name: str = ""
    model_families: tuple[str, ...] = ()


@dataclass(frozen=True)
class SupplierChannel:
    channel_id: str
    supplier_id: str
    channel_type: str  # direct, agent, referrer, distributor, marketplace
    organization: str
    contact_name: str = ""
    email: str = ""
    source_ref: str = ""


@dataclass(frozen=True)
class CollisionResult:
    decision: OutreachDecision
    matched_supplier_id: str | None = None
    reasons: tuple[str, ...] = ()


@dataclass
class SupplierRegistry:
    suppliers: dict[str, SupplierIdentity] = field(default_factory=dict)
    channels: list[SupplierChannel] = field(default_factory=list)

    def add_supplier(self, supplier: SupplierIdentity) -> None:
        if not supplier.supplier_id.strip() or not supplier.legal_name.strip():
            raise ValueError("supplier_id and legal_name are required")
        if supplier.supplier_id in self.suppliers:
            raise ValueError(f"supplier_id already exists: {supplier.supplier_id}")
        self.suppliers[supplier.supplier_id] = supplier

    def add_channel(self, channel: SupplierChannel) -> None:
        if channel.supplier_id not in self.suppliers:
            raise ValueError("channel must reference an existing supplier")
        if not channel.channel_id.strip() or not channel.organization.strip():
            raise ValueError("channel_id and organization are required")
        if any(c.channel_id == channel.channel_id for c in self.channels):
            raise ValueError(f"channel_id already exists: {channel.channel_id}")
        self.channels.append(channel)

    def find_identity_match(self, candidate: SupplierIdentity) -> CollisionResult:
        candidate_domain = _norm_domain(candidate.domain)
        candidate_legal = _norm(candidate.legal_name)
        candidate_factory = _norm(candidate.factory_name)
        candidate_brand = _norm(candidate.brand)

        for existing in self.suppliers.values():
            existing_domain = _norm_domain(existing.domain)
            if candidate_domain and existing_domain and candidate_domain == existing_domain:
                return CollisionResult(
                    OutreachDecision.HOLD_DUPLICATE_SOURCE,
                    existing.supplier_id,
                    ("same_domain",),
                )

            if candidate_legal and candidate_legal == _norm(existing.legal_name):
                return CollisionResult(
                    OutreachDecision.HOLD_DUPLICATE_SOURCE,
                    existing.supplier_id,
                    ("same_legal_name",),
                )

            if candidate_factory and candidate_factory == _norm(existing.factory_name):
                return CollisionResult(
                    OutreachDecision.HOLD_DUPLICATE_SOURCE,
                    existing.supplier_id,
                    ("same_factory_name",),
                )

            if candidate_brand and candidate_brand == _norm(existing.brand):
                return CollisionResult(
                    OutreachDecision.REVIEW_POSSIBLE_COLLISION,
                    existing.supplier_id,
                    ("same_brand",),
                )

            same_location = (
                _norm(candidate.country)
                and _norm(candidate.country) == _norm(existing.country)
                and _norm(candidate.city)
                and _norm(candidate.city) == _norm(existing.city)
            )
            model_overlap = {
                _norm(model) for model in candidate.model_families if _norm(model)
            } & {
                _norm(model) for model in existing.model_families if _norm(model)
            }
            if same_location and model_overlap:
                return CollisionResult(
                    OutreachDecision.REVIEW_POSSIBLE_COLLISION,
                    existing.supplier_id,
                    ("same_location", "model_overlap"),
                )

        return CollisionResult(OutreachDecision.ALLOW)

    def assess_channel_collision(self, candidate: SupplierChannel) -> CollisionResult:
        """Assess a proposed outreach route to a supplier already in the registry.

        Exact route reuse is treated as a duplicate. A second distinct intermediary
        for the same OEM is review-only: field evidence suggests parallel approaches
        can create supplier confusion, but that is not strong enough to auto-block.
        """
        if candidate.supplier_id not in self.suppliers:
            raise ValueError("channel must reference an existing supplier")

        existing_channels = self.channels_for_supplier(candidate.supplier_id)
        candidate_org = _norm(candidate.organization)
        candidate_email = _norm_email(candidate.email)

        for existing in existing_channels:
            same_org = candidate_org and candidate_org == _norm(existing.organization)
            same_email = (
                candidate_email
                and _norm_email(existing.email)
                and candidate_email == _norm_email(existing.email)
            )
            if same_org or same_email:
                reasons = []
                if same_org:
                    reasons.append("same_channel_organization")
                if same_email:
                    reasons.append("same_channel_email")
                return CollisionResult(
                    OutreachDecision.HOLD_DUPLICATE_SOURCE,
                    candidate.supplier_id,
                    tuple(reasons),
                )

        intermediary_types = {"agent", "referrer", "distributor", "marketplace"}
        candidate_type = _norm(candidate.channel_type)
        existing_intermediaries = [
            channel
            for channel in existing_channels
            if _norm(channel.channel_type) in intermediary_types
        ]
        if candidate_type in intermediary_types and existing_intermediaries:
            return CollisionResult(
                OutreachDecision.REVIEW_POSSIBLE_COLLISION,
                candidate.supplier_id,
                ("parallel_intermediary_channels",),
            )

        return CollisionResult(OutreachDecision.ALLOW, candidate.supplier_id)

    def channels_for_supplier(self, supplier_id: str) -> tuple[SupplierChannel, ...]:
        return tuple(c for c in self.channels if c.supplier_id == supplier_id)

    def unique_oem_count(self) -> int:
        return len(self.suppliers)

    def channel_count(self) -> int:
        return len(self.channels)


def deduplicate_candidates(
    existing: Iterable[SupplierIdentity], candidates: Iterable[SupplierIdentity]
) -> list[tuple[SupplierIdentity, CollisionResult]]:
    registry = SupplierRegistry()
    for supplier in existing:
        registry.add_supplier(supplier)

    results: list[tuple[SupplierIdentity, CollisionResult]] = []
    for candidate in candidates:
        result = registry.find_identity_match(candidate)
        results.append((candidate, result))
        if result.decision == OutreachDecision.ALLOW:
            registry.add_supplier(candidate)
    return results
