"""PRJ-HYD-01 engineering-review vertical: buyer master vs. supplier evidence.

Buyer-side authority comes only from the canonical PRJ-HYD-01 source selected
through ``CanonicalStore``. Supplier evidence is evidence, never authority: it
can only be classified as CONFIRMED, CONTRADICTED or SILENT against the
existing Hydrotester hold-point rules, and this module never authorizes any
external action or writes to the canonical store or business vault.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256

from canonical_sources import HYD_HOLD_POINT_RULES, CanonicalStore
from contracts import EvidenceClass, EvidenceRecord, canonical_digest

PRJ_HYD_01 = "PRJ-HYD-01"
DISPOSITIONS = ("CONFIRMED", "CONTRADICTED", "SILENT")
MAX_STATEMENT_CHARS = 20_000
_EXCERPT_LEAD, _EXCERPT_TRAIL = 100, 180


def _utc(value: str, field: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_must_include_timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _excerpt(text: str, start: int, end: int) -> str:
    lo, hi = max(0, start - _EXCERPT_LEAD), min(len(text), end + _EXCERPT_TRAIL)
    return " ".join(text[lo:hi].split())


@dataclass(frozen=True)
class SupplierEvidenceSnapshot:
    """A supplier reply/addendum. Evidence only -- never authority over PRJ-HYD-01 requirements.

    ``supplier_name`` is metadata for the report only; it is never consulted by the
    disposition logic and has no bearing on project isolation.
    """

    project_id: str
    source_ref: str
    supplier_name: str
    received_at: str
    statement: str
    evidence_classification: EvidenceClass
    confidence: float = 0.5

    def validate(self) -> None:
        if not all(isinstance(v, str) and v.strip() for v in (
            self.project_id, self.source_ref, self.supplier_name, self.statement
        )):
            raise ValueError("invalid_supplier_evidence_identity")
        if len(self.statement) > MAX_STATEMENT_CHARS:
            raise ValueError("supplier_statement_too_large")
        _utc(self.received_at, "received_at")
        classification = EvidenceClass(self.evidence_classification)
        # Reusing EvidenceRecord's own contract is what stops a CLAIM/ESTIMATE/ASSUMPTION/UNKNOWN
        # supplier statement from being silently treated as a FACT: EvidenceRecord enforces that a
        # FACT must carry a source_ref, and this module never assigns EvidenceClass.FACT itself --
        # the classification is only ever echoed back from what the caller supplied.
        EvidenceRecord(
            evidence_id="sup_" + sha256(f"{self.project_id}:{self.source_ref}".encode()).hexdigest()[:20],
            project_id=self.project_id,
            classification=classification,
            statement=self.statement,
            source_ref=self.source_ref,
            observed_at=self.received_at,
            confidence=self.confidence,
        )


@dataclass(frozen=True)
class RequirementDelta:
    code: str
    severity: str
    buyer_requirement_excerpt: str
    supplier_disposition: str
    supplier_evidence_excerpt: str | None
    required_action: str


def _supplier_disposition(kind: str, spec: dict, pattern: str, supplier_text: str) -> tuple[str, str | None]:
    """Conservative, explicit-evidence-only classification.

    CONTRADICTED requires an explicit differing value (numeric rules) or an explicit
    negation statement (keyword rules) -- absence of a mention is always SILENT, never
    inferred as a contradiction. For keyword rules the negation check runs first: a
    negated mention (e.g. "unable to provide a capability matrix") still contains the
    literal buyer phrase, so checking plain containment first would wrongly read a
    decline as a confirmation.
    """
    if kind == "numeric":
        expected = spec["expected_value"]
        matches = list(re.finditer(spec["value_pattern"], supplier_text, re.IGNORECASE))
        for found in matches:
            if found.group(1).strip() != expected:
                return "CONTRADICTED", _excerpt(supplier_text, found.start(), found.end())
        if matches:
            found = matches[0]
            return "CONFIRMED", _excerpt(supplier_text, found.start(), found.end())
        return "SILENT", None
    if kind == "keyword":
        negated = re.search(spec["negation_pattern"], supplier_text, re.IGNORECASE)
        if negated:
            return "CONTRADICTED", _excerpt(supplier_text, negated.start(), negated.end())
        confirmed = re.search(pattern, supplier_text, re.IGNORECASE)
        if confirmed:
            return "CONFIRMED", _excerpt(supplier_text, confirmed.start(), confirmed.end())
        return "SILENT", None
    raise ValueError("invalid_contradiction_kind")


def review_supplier_evidence(store: CanonicalStore, supplier: SupplierEvidenceSnapshot) -> dict:
    """Compare supplier evidence against the canonical PRJ-HYD-01 hold-point rules.

    Read-only: makes no write to ``store`` or to the business vault, and never sets
    ``external_action_authorized`` to anything but False. Buyer-side authority always
    comes from ``store.latest_for_project("PRJ-HYD-01")`` -- a hardcoded lookup, not the
    caller-supplied ``supplier.project_id`` -- so there is no cross-project fallback path.
    """
    supplier.validate()
    if supplier.project_id != PRJ_HYD_01:
        raise ValueError("engineering_review_scoped_to_prj_hyd_01")

    buyer_row = store.latest_for_project(PRJ_HYD_01)
    buyer_content = buyer_row["content"]

    deltas: list[RequirementDelta] = []
    for code, severity, pattern, required_action, kind, spec in HYD_HOLD_POINT_RULES:
        buyer_found = re.search(pattern, buyer_content, re.IGNORECASE)
        if not buyer_found:
            continue
        buyer_excerpt = _excerpt(buyer_content, buyer_found.start(), buyer_found.end())
        disposition, supplier_excerpt = _supplier_disposition(kind, spec, pattern, supplier.statement)

        deltas.append(RequirementDelta(code, severity, buyer_excerpt, disposition, supplier_excerpt,
                                        required_action))

    payload = {
        "schema_version": "nexus.engineering-review.v1",
        "project_id": PRJ_HYD_01,
        "buyer_source_id": buyer_row["source_id"],
        "buyer_source_sha256": buyer_row["sha256"],
        "buyer_source_version": buyer_row["version"],
        "supplier_source_ref": supplier.source_ref,
        "supplier_name": supplier.supplier_name,
        "supplier_evidence_classification": EvidenceClass(supplier.evidence_classification).value,
        "external_action_authorized": False,
        "deltas": [asdict(delta) for delta in deltas],
    }
    payload["report_digest"] = canonical_digest(payload)
    return payload
