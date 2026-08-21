from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


EntityValidity = Literal["verified", "partial", "unverified", "rejected"]
ChannelState = Literal["healthy", "degraded", "failed", "unverified"]


@dataclass(frozen=True)
class SupplierEntityState:
    supplier_id: str
    validity: EntityValidity
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.supplier_id, str) or not self.supplier_id.strip():
            raise ValueError("supplier_id must be a nonblank string")
        if not self.evidence_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs):
            raise ValueError("supplier identity requires retrievable evidence")


@dataclass(frozen=True)
class ContactChannelState:
    supplier_id: str
    channel_id: str
    channel_type: Literal["email", "phone", "whatsapp", "website", "other"]
    state: ChannelState
    observed_at: datetime
    evidence_refs: tuple[str, ...]
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        for name, value in (("supplier_id", self.supplier_id), ("channel_id", self.channel_id)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonblank string")
        if not isinstance(self.observed_at, datetime) or self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        if not self.evidence_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs):
            raise ValueError("channel state requires retrievable evidence")
        if self.state == "failed" and (not isinstance(self.failure_reason, str) or not self.failure_reason.strip()):
            raise ValueError("failed channel requires failure_reason")


@dataclass(frozen=True)
class SupplierContactAssessment:
    supplier: SupplierEntityState
    channel: ContactChannelState
    can_research_supplier: bool
    can_use_channel_for_outreach: bool
    reason: str


def assess_supplier_channel(
    supplier: SupplierEntityState,
    channel: ContactChannelState,
) -> SupplierContactAssessment:
    """Keep entity validity and channel health independent.

    A failed channel never proves that the company is invalid. Conversely, a verified
    company never makes a failed or unverified channel safe to use for outreach.
    """
    if supplier.supplier_id != channel.supplier_id:
        raise ValueError("supplier/channel identity mismatch")

    can_research = supplier.validity != "rejected"
    can_outreach = supplier.validity in {"verified", "partial"} and channel.state == "healthy"

    if supplier.validity == "rejected":
        reason = "supplier identity rejected"
    elif channel.state == "failed":
        reason = "supplier may remain valid but selected contact channel failed"
    elif channel.state == "degraded":
        reason = "channel is degraded and should be re-verified before outreach"
    elif channel.state == "unverified":
        reason = "channel is unverified"
    elif supplier.validity == "unverified":
        reason = "supplier identity is unverified"
    else:
        reason = "supplier and channel are currently usable subject to normal action approval"

    return SupplierContactAssessment(
        supplier=supplier,
        channel=channel,
        can_research_supplier=can_research,
        can_use_channel_for_outreach=can_outreach,
        reason=reason,
    )
