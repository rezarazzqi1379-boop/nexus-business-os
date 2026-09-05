"""Public mirror publication guard: enforces docs/PUBLIC_HANDOFF_MIRROR_CONTRACT_v0.1.md and
schemas/public_handoff_record_v1.schema.json before anything is written to the public
coordination mirror (rezarazzqi1379-boop/nexus-ai-handoff-public).

No external JSON-schema library is used -- this validates exactly the subset of JSON Schema
draft 2020-12 features the one schema file actually uses (type, enum, const, pattern,
minLength/maxLength, format: date-time, required, additionalProperties). That schema file is
the source of truth for the field allowlist; this module does not duplicate it by hand.

A publishable record is DATA. Nothing in this module, and nothing that reads a published
record, may treat any field -- especially ``next_safe_action`` -- as an instruction to execute,
a shell argument, or an authorization for merge/deploy/outreach/bid/quote/payment/contract/
signing/order/permission-change/production-write. That boundary is enforced structurally
(the schema's own ``state``/``review_status`` enums contain no such value) and defensively
(explicit keyword rejection in ``reject_protected_action_language`` for the free-text fields).

"Regex found nothing" is not treated as proof of no secret: every free-text field is also
checked for high-entropy tokens via Shannon entropy, independent of any fixed pattern list.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from coordination_kit import HandoffPackageV2, scan_diff_for_secrets

SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "public_handoff_record_v1.schema.json"
FREE_TEXT_FIELDS = ("tests_summary", "unknowns_summary", "next_safe_action")

PUBLICATION_STATES = frozenset({
    "PREPARED", "SANITIZED", "PUBLISHED", "OBSERVED", "ACKNOWLEDGED", "HOLD_FOR_REVIEW",
    "SUPERSEDED", "ARCHIVED",
})
ACK_STATES = frozenset({"OBSERVED", "ACKNOWLEDGED"})
RECORD_TYPES = frozenset({"handoff", "ack", "status", "archive"})

_ALLOWED_URL_HOSTS = frozenset({"github.com", "raw.githubusercontent.com"})

_PII_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}\b"),  # email
    re.compile(r"(?<!\d)(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}(?!\d)"),  # phone-ish
)
_JWT_LIKE = re.compile(r"\b[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")
_BEARER_LIKE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9_\-.]{10,}\b")
_ENV_ASSIGNMENT_LIKE = re.compile(
    r"(?im)^\s*[A-Z_][A-Z0-9_]{2,}\s*=\s*['\"]?[A-Za-z0-9/+_.\-]{8,}['\"]?\s*$"
)
_URL_LIKE = re.compile(r"https?://([^/\s]+)")
_PRICE_LIKE = re.compile(r"(?i)\b(?:usd|eur|gbp|irr|rial|toman|\$|price|quote[d]?|invoice|contract)\b")
_CODE_LIKE = re.compile(r"```|^\s*(?:def |class |import |from .+ import |function\s*\()", re.MULTILINE)
_HIGH_ENTROPY_TOKEN = re.compile(r"[A-Za-z0-9+/_=\-]{24,}")


class HoldForReview(ValueError):
    """Content could not be proven safe to publish -- fails closed to HOLD_FOR_REVIEW, never
    published as-is."""

    def __init__(self, reasons: tuple[str, ...]):
        super().__init__("hold_for_review:" + ",".join(reasons))
        self.reasons = reasons


def shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    length = len(text)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def find_high_entropy_tokens(text: str, *, min_length: int = 24, min_entropy: float = 3.6) -> tuple[str, ...]:
    """Catches secret-shaped blobs no fixed pattern matches -- "regex found nothing" is never
    treated as proof of safety; this runs unconditionally alongside the pattern list.
    """
    findings = []
    for token in _HIGH_ENTROPY_TOKEN.findall(text):
        if len(token) >= min_length and shannon_entropy(token) >= min_entropy:
            findings.append(token[:8] + "...")
    return tuple(dict.fromkeys(findings))


def find_disallowed_urls(text: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(
        host for host in _URL_LIKE.findall(text) if host.split(":")[0] not in _ALLOWED_URL_HOSTS
    ))


def scan_text_for_sensitive_data(text: str) -> tuple[str, ...]:
    """Runs every guard: known secret shapes, PII, JWT/bearer/env-assignment shapes, price/
    contract-ish language, code-snippet shapes, disallowed URLs, and entropy -- returns every
    distinct reason found (empty means nothing detected, not "proven clean").
    """
    reasons: list[str] = []
    reasons.extend(f"secret:{f}" for f in scan_diff_for_secrets(text))
    if any(p.search(text) for p in _PII_PATTERNS):
        reasons.append("pii_email_or_phone")
    if _JWT_LIKE.search(text):
        reasons.append("jwt_like_token")
    if _BEARER_LIKE.search(text):
        reasons.append("bearer_token")
    if _ENV_ASSIGNMENT_LIKE.search(text):
        reasons.append("env_style_secret_assignment")
    if _PRICE_LIKE.search(text):
        reasons.append("pricing_or_contract_language")
    if _CODE_LIKE.search(text):
        reasons.append("code_snippet")
    disallowed_urls = find_disallowed_urls(text)
    if disallowed_urls:
        reasons.append(f"private_url:{','.join(disallowed_urls)}")
    entropy_hits = find_high_entropy_tokens(text)
    if entropy_hits:
        reasons.append(f"high_entropy_blob:{','.join(entropy_hits)}")
    return tuple(dict.fromkeys(reasons))


_PROTECTED_ACTION_KEYWORDS = (
    "merge", "deploy", "outreach", "bid", "quote", "payment", "pay ", "contract", "sign",
    "signing", "order", "permission change", "grant access", "production access",
    "production write", "authoriz", "approve this", "go ahead and", "execute this",
)


def reject_protected_action_language(text: str) -> tuple[str, ...]:
    """A public record's free text must never read as authorization for a protected action."""
    lowered = text.lower()
    return tuple(dict.fromkeys(keyword.strip() for keyword in _PROTECTED_ACTION_KEYWORDS if keyword in lowered))


# ---------------------------------------------------------------------------
# A1: schema enforcement (hand-rolled, minimal -- validates against the one schema file)
# ---------------------------------------------------------------------------

def load_schema(path: Path = SCHEMA_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


_DATE_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")


def validate_against_schema(record: Mapping, schema: dict) -> None:
    if not isinstance(record, dict):
        raise ValueError("record_must_be_an_object")
    properties = schema.get("properties", {})
    if schema.get("additionalProperties") is False:
        unknown = set(record) - set(properties)
        if unknown:
            raise ValueError(f"unknown_fields_rejected:{sorted(unknown)}")
    for required_field in schema.get("required", ()):
        if required_field not in record:
            raise ValueError(f"missing_required_field:{required_field}")
    for key, value in record.items():
        spec = properties.get(key)
        if spec is None:
            continue
        _validate_value(key, value, spec)


def _validate_value(key: str, value, spec: dict) -> None:
    if "const" in spec and value != spec["const"]:
        raise ValueError(f"invalid_const:{key}")
    if "enum" in spec and value not in spec["enum"]:
        raise ValueError(f"invalid_enum_value:{key}")
    expected_type = spec.get("type")
    if expected_type is not None:
        allowed_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not _matches_any_type(value, allowed_types):
            raise ValueError(f"invalid_type:{key}")
    if value is None:
        return
    if isinstance(value, str):
        if "pattern" in spec and not re.fullmatch(spec["pattern"], value):
            raise ValueError(f"pattern_mismatch:{key}")
        if "minLength" in spec and len(value) < spec["minLength"]:
            raise ValueError(f"too_short:{key}")
        if "maxLength" in spec and len(value) > spec["maxLength"]:
            raise ValueError(f"too_long:{key}")
        if spec.get("format") == "date-time" and not _DATE_TIME.match(value):
            raise ValueError(f"invalid_date_time:{key}")


def _matches_any_type(value, types: list[str]) -> bool:
    checks = {
        "string": lambda v: isinstance(v, str), "boolean": lambda v: isinstance(v, bool),
        "null": lambda v: v is None, "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
        "object": lambda v: isinstance(v, dict), "array": lambda v: isinstance(v, list),
    }
    return any(checks.get(t, lambda v: False)(value) for t in types)


# ---------------------------------------------------------------------------
# A6/A7: project isolation + private -> public projection
# ---------------------------------------------------------------------------

_PUBLIC_ALLOWLIST_FIELDS = (
    "schema_version", "record_type", "task_id", "project_id", "lane_id", "state", "owner_role",
    "branch", "base_sha", "head_sha", "review_status", "risk_class", "protected_action_required",
    "tests_summary", "unknowns_summary", "next_safe_action", "source_record_digest", "created_at",
)


_PUBLIC_REVIEW_STATUSES = frozenset(load_schema().get("properties", {}).get("review_status", {}).get("enum", ()))


def project_private_package_to_public(
    package: HandoffPackageV2, *, record_type: str, state: str, review_status: str, tests_summary: str = "",
    unknowns_summary: str = "", next_safe_action: str = "",
) -> dict:
    """The smallest deterministic private->public binding: the public record carries only
    allowlisted fields plus ``source_record_digest`` (the private package's own digest, reused
    -- not a new digest mechanism). It never copies claims, evidence_refs, files_changed, or
    any other private free-form content. cross_project_touch is deliberately never projected:
    if the private package touched another project, publishing that fact risks leaking which
    project without leaking what -- callers needing to disclose it must do so explicitly via
    unknowns_summary in their own words, never automatically.

    project_id/lane_id are REQUIRED and never inferred: this function raises if either is
    missing on the private package, rather than defaulting to a guess.

    ``review_status`` is a REQUIRED caller-supplied argument, not read from
    ``package.review_status``: the public schema's review_status enum
    (PENDING/VERIFIED/STALE/CONFLICT/INVALID/SUPERSEDED) is the *independent verification*
    vocabulary from ``verify_handoff_package()``'s ``VerificationResult.status`` -- a
    deliberately different concept from the private package's own human-review-decision
    vocabulary (PENDING/APPROVED/REJECTED/STALE/SUPERSEDED). Silently reusing
    ``package.review_status`` here would either fail schema validation (e.g. "APPROVED" is not
    a valid public review_status) or, worse, misrepresent an internal review decision as an
    independent verification outcome. Callers should pass the actual
    ``VerificationResult.status`` they obtained by running ``verify_handoff_package()``.
    """
    package.validate()
    if not package.project_id or not package.project_id.strip():
        raise ValueError("public_projection_requires_explicit_project_id")
    if not package.lane_id or not package.lane_id.strip():
        raise ValueError("public_projection_requires_explicit_lane_id")
    if record_type not in RECORD_TYPES:
        raise ValueError("invalid_record_type")
    if state not in PUBLICATION_STATES:
        raise ValueError("invalid_publication_state")
    if review_status not in _PUBLIC_REVIEW_STATUSES:
        raise ValueError("invalid_public_review_status")

    record = {
        "schema_version": "nexus.public-handoff.v1", "record_type": record_type, "task_id": package.task_id,
        "project_id": package.project_id, "lane_id": package.lane_id, "state": state,
        "owner_role": package.owner, "branch": package.branch, "base_sha": package.base_sha,
        "head_sha": package.head_sha, "review_status": review_status, "risk_class": package.risk_class,
        "protected_action_required": package.protected_action_required, "tests_summary": tests_summary,
        "unknowns_summary": unknowns_summary, "next_safe_action": next_safe_action,
        "source_record_digest": package.digest, "created_at": package.created_at,
    }
    return record


# ---------------------------------------------------------------------------
# A5: ACK semantics
# ---------------------------------------------------------------------------

def build_ack_record(*, task_id: str, project_id: str, lane_id: str, source_record_digest: str,
                     owner_role: str, created_at: str) -> dict:
    """An ack proves only OBSERVED/ACKNOWLEDGED -- reading a record. It carries no
    review_status/risk_class/protected_action_required claim of its own and can never mean
    APPROVED, ACCEPTED, MERGED, DEPLOYED, or AUTHORIZED -- those words do not exist anywhere
    in this schema's enums, so an ack cannot express them even by mistake.
    """
    if not project_id.strip() or not lane_id.strip():
        raise ValueError("ack_requires_explicit_project_and_lane_id")
    record = {
        "schema_version": "nexus.public-handoff.v1", "record_type": "ack", "task_id": task_id,
        "project_id": project_id, "lane_id": lane_id, "state": "OBSERVED", "owner_role": owner_role,
        "risk_class": "LOW", "protected_action_required": False, "source_record_digest": source_record_digest,
        "created_at": created_at,
    }
    return record


# ---------------------------------------------------------------------------
# Full publication gate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PublicationDecision:
    publishable: bool
    state: str
    reasons: tuple[str, ...]


def review_for_publication(record: Mapping, *, schema: dict | None = None) -> PublicationDecision:
    """Runs every A1/A2/A3 guard. Any failure -> not publishable, HOLD_FOR_REVIEW. This never
    raises for "content looks bad" -- only for a structurally malformed call (e.g. record isn't
    a mapping) -- ordinary sensitive content is reported as a HOLD decision, not an exception,
    so a caller can log/queue it rather than crash.
    """
    schema = schema or load_schema()
    reasons: list[str] = []
    try:
        validate_against_schema(record, schema)
    except ValueError as exc:
        return PublicationDecision(False, "HOLD_FOR_REVIEW", (str(exc),))

    for field_name in FREE_TEXT_FIELDS:
        value = record.get(field_name)
        if not value:
            continue
        reasons.extend(f"{field_name}:{reason}" for reason in scan_text_for_sensitive_data(value))
        reasons.extend(f"{field_name}:protected_action:{kw}" for kw in reject_protected_action_language(value))

    if reasons:
        return PublicationDecision(False, "HOLD_FOR_REVIEW", tuple(dict.fromkeys(reasons)))
    return PublicationDecision(True, record.get("state", "SANITIZED"), ())
