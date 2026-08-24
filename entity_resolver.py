from __future__ import annotations

from dataclasses import dataclass
from email.utils import parseaddr

from classifier_guard import TrustedClassificationContext
from gmail_need_adapter import GmailMessageSnapshot
from need_radar import COMPANY_ROLES, FIT_LEVELS, RELATIONSHIP_LEVELS, TIMING_LEVELS
from projects import get_project


def normalize_domain(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("invalid_domain")
    candidate = value.strip().lower().rstrip(".")
    if not candidate or "@" in candidate or "." not in candidate:
        raise ValueError("invalid_domain")
    try:
        encoded = candidate.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("invalid_domain") from exc
    labels = encoded.split(".")
    if any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-") for label in labels):
        raise ValueError("invalid_domain")
    return encoded


def normalize_email(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("invalid_email")
    _, parsed = parseaddr(value)
    candidate = parsed.strip().lower()
    if candidate.count("@") != 1:
        raise ValueError("invalid_email")
    local, domain = candidate.rsplit("@", 1)
    if not local or any(character.isspace() for character in local):
        raise ValueError("invalid_email")
    return f"{local}@{normalize_domain(domain)}"


@dataclass(frozen=True)
class EntityRecord:
    company_id: str
    company_name: str
    verified_emails: tuple[str, ...] = ()
    verified_domains: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProjectBinding:
    company_id: str
    project_id: str
    company_role: str
    fit: str
    timing: str
    relationship: str


@dataclass(frozen=True)
class ResolutionEvidence:
    sender_email: str
    sender_domain: str
    entity_match: str
    binding_key: str


@dataclass(frozen=True)
class TrustedResolution:
    context: TrustedClassificationContext
    evidence: ResolutionEvidence


class EntityProjectRegistry:
    """Deterministic identity control plane. Email content is never consulted."""

    def __init__(self, entities: tuple[EntityRecord, ...], bindings: tuple[ProjectBinding, ...]):
        self._entities: dict[str, EntityRecord] = {}
        self._email_to_company: dict[str, str] = {}
        self._domain_to_company: dict[str, str] = {}
        self._bindings: dict[tuple[str, str], ProjectBinding] = {}

        for entity in entities:
            if not entity.company_id.strip() or not entity.company_name.strip():
                raise ValueError("invalid_entity")
            if entity.company_id in self._entities:
                raise ValueError("duplicate_company_id")
            normalized_emails = tuple(normalize_email(item) for item in entity.verified_emails)
            normalized_domains = tuple(normalize_domain(item) for item in entity.verified_domains)
            if not normalized_emails and not normalized_domains:
                raise ValueError("entity_requires_verified_identity")
            normalized = EntityRecord(
                entity.company_id.strip(), entity.company_name.strip(), normalized_emails,
                normalized_domains, tuple(item.strip() for item in entity.aliases if item.strip()),
            )
            self._entities[normalized.company_id] = normalized
            for email in normalized.verified_emails:
                self._claim_identity(self._email_to_company, email, normalized.company_id, "ambiguous_verified_email")
            for domain in normalized.verified_domains:
                self._claim_identity(self._domain_to_company, domain, normalized.company_id, "ambiguous_verified_domain")

        for binding in bindings:
            if binding.company_id not in self._entities:
                raise ValueError("binding_unknown_company")
            get_project(binding.project_id)
            key = (binding.company_id, binding.project_id)
            if key in self._bindings:
                raise ValueError("duplicate_project_binding")
            if (binding.company_role not in COMPANY_ROLES or binding.fit not in FIT_LEVELS
                    or binding.timing not in TIMING_LEVELS
                    or binding.relationship not in RELATIONSHIP_LEVELS):
                raise ValueError("invalid_project_binding")
            self._bindings[key] = binding

    @staticmethod
    def _claim_identity(index: dict[str, str], identity: str, company_id: str, error: str) -> None:
        owner = index.get(identity)
        if owner is not None and owner != company_id:
            raise ValueError(error)
        index[identity] = company_id

    def resolve_gmail(self, snapshot: GmailMessageSnapshot, *, project_hint: str | None = None) -> TrustedResolution:
        snapshot.validate()
        sender = normalize_email(snapshot.sender)
        domain = sender.rsplit("@", 1)[1]
        email_owner = self._email_to_company.get(sender)
        domain_owner = self._domain_to_company.get(domain)
        if email_owner and domain_owner and email_owner != domain_owner:
            raise ValueError("sender_identity_conflict")
        company_id = email_owner or domain_owner
        if company_id is None:
            raise ValueError("unresolved_sender_identity")
        entity_match = "verified_email" if email_owner else "verified_domain"

        candidates = [binding for key, binding in self._bindings.items() if key[0] == company_id]
        if project_hint is not None:
            get_project(project_hint)
            candidates = [binding for binding in candidates if binding.project_id == project_hint]
            if not candidates:
                raise ValueError("sender_not_bound_to_project")
        elif len(candidates) != 1:
            raise ValueError("ambiguous_project_binding" if candidates else "missing_project_binding")
        binding = candidates[0]
        entity = self._entities[company_id]
        context = TrustedClassificationContext(
            company_id=entity.company_id,
            company_name=entity.company_name,
            company_role=binding.company_role,
            project_id=binding.project_id,
            fit=binding.fit,
            timing=binding.timing,
            relationship=binding.relationship,
        )
        return TrustedResolution(
            context=context,
            evidence=ResolutionEvidence(
                sender_email=sender,
                sender_domain=domain,
                entity_match=entity_match,
                binding_key=f"{company_id}:{binding.project_id}",
            ),
        )
