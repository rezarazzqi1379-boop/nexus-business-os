from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping
from urllib.parse import urlsplit


@dataclass(frozen=True)
class CompanySnapshot:
    """Provider-neutral, read-only CRM company snapshot."""

    record_id: str
    name: str
    domain: str
    website: str = ""
    country: str = ""
    industry: str = ""


@dataclass(frozen=True)
class HygieneFinding:
    record_ids: tuple[str, ...]
    code: str
    severity: str
    detail: str


def normalize_domain(value: str) -> str:
    raw = value.strip().lower()
    if not raw:
        return ""
    parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
    host = (parsed.hostname or "").strip(".")
    if host.startswith("www."):
        host = host[4:]
    labels = host.split(".")
    if len(labels) < 2 or any(not label or label.startswith("-") or label.endswith("-") for label in labels):
        return ""
    try:
        return host.encode("idna").decode("ascii")
    except UnicodeError:
        return ""


def _one_edit_or_transposition(left: str, right: str) -> bool:
    if left == right:
        return False
    if len(left) == len(right):
        mismatches = [index for index, pair in enumerate(zip(left, right)) if pair[0] != pair[1]]
        if len(mismatches) == 1:
            return True
        if len(mismatches) == 2:
            first, second = mismatches
            return second == first + 1 and left[first] == right[second] and left[second] == right[first]
        return False
    if abs(len(left) - len(right)) != 1:
        return False
    short, long = (left, right) if len(left) < len(right) else (right, left)
    cursor = 0
    for char in long:
        if cursor < len(short) and char == short[cursor]:
            cursor += 1
    return cursor == len(short)


def audit_company_snapshots(
    records: Iterable[CompanySnapshot],
    *,
    verified_fields: Mapping[str, Mapping[str, str]] | None = None,
) -> tuple[HygieneFinding, ...]:
    """Detect identity defects without mutating the CRM or inventing corrections."""
    items = tuple(records)
    if not 1 <= len(items) <= 1_000:
        raise ValueError("invalid_company_batch")
    verified_fields = verified_fields or {}
    seen_ids: set[str] = set()
    domains: dict[str, list[str]] = {}
    findings: list[HygieneFinding] = []

    for item in items:
        if not item.record_id.strip() or item.record_id in seen_ids:
            raise ValueError("invalid_or_duplicate_company_id")
        seen_ids.add(item.record_id)
        domain = normalize_domain(item.domain)
        website_domain = normalize_domain(item.website)
        if not item.name.strip():
            findings.append(HygieneFinding((item.record_id,), "missing_name", "blocking", "company name is empty"))
        if not domain:
            findings.append(HygieneFinding((item.record_id,), "invalid_domain", "blocking", "domain is empty or invalid"))
        else:
            domains.setdefault(domain, []).append(item.record_id)
        if website_domain and domain and website_domain != domain:
            findings.append(HygieneFinding((item.record_id,), "website_domain_mismatch", "review", f"{website_domain} != {domain}"))

        expected = verified_fields.get(item.record_id, {})
        for field in ("name", "domain", "country", "industry"):
            expected_value = str(expected.get(field, "")).strip()
            actual_value = str(getattr(item, field)).strip()
            if expected_value and actual_value.casefold() != expected_value.casefold():
                findings.append(HygieneFinding((item.record_id,), f"verified_{field}_mismatch", "blocking", f"CRM={actual_value!r}; verified={expected_value!r}"))

    for domain, ids in domains.items():
        if len(ids) > 1:
            findings.append(HygieneFinding(tuple(sorted(ids)), "duplicate_domain", "blocking", domain))

    unique_domains = sorted(domains)
    for index, left in enumerate(unique_domains):
        for right in unique_domains[index + 1 :]:
            if _one_edit_or_transposition(left, right):
                ids = tuple(sorted((*domains[left], *domains[right])))
                findings.append(HygieneFinding(ids, "possible_domain_typo", "review", f"{left} ~ {right}"))

    order = {"blocking": 0, "review": 1, "info": 2}
    return tuple(sorted(findings, key=lambda finding: (order[finding.severity], finding.code, finding.record_ids)))


def clean_record_ids(records: Iterable[CompanySnapshot], findings: Iterable[HygieneFinding]) -> tuple[str, ...]:
    """Return only records without blocking identity defects."""
    items = tuple(records)
    blocked = {record_id for finding in findings if finding.severity == "blocking" for record_id in finding.record_ids}
    return tuple(item.record_id for item in items if item.record_id not in blocked)
