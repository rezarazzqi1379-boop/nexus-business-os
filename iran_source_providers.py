"""Iran-native source provider interfaces and integration-state registry (Track C).

This module defines the *shape* a real Iranian data-source adapter would need to satisfy
to plug into research_evidence.run_research_query()'s ``providers`` mapping or
deep_search_fabric.run_recursive_search()'s ``provider_fns`` routing. It does not connect
to any real Iranian data source. The only concrete implementation shipped here is
``NullIranSourceAdapter``, matching NullSearchProvider's graceful-degradation discipline:
it always returns zero results. It is fixture-tested (evals/test_iran_source_providers.py)
but has performed zero live reads against any real Iranian source.

``IRAN_SOURCE_FAMILIES`` names target classes of publicly-referenced Iranian commercial-
data source families (customs data, chambers of commerce, industrial directories, B2B
marketplaces, tender/procurement portals, company websites, trade publications). These
are intended integration targets, not claims that access, credentials, or a working
integration exists for any of them -- see ``iran_source_integration_report()`` for the
current, honestly-reported maturity of each one. No row in that report may read
LIVE_READ_VERIFIED unless a real adapter for that family has actually performed and
independently verified a live read end-to-end through this pipeline; nothing here does
that today.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from research_evidence import SearchResult  # noqa: E402

IRAN_SOURCE_FAMILIES = frozenset({
    "IRICA_CUSTOMS",
    "CHAMBER_OF_COMMERCE",
    "INDUSTRIAL_DIRECTORY",
    "INDUSTRIAL_ESTATE_DIRECTORY",
    "B2B_MARKETPLACE",
    "TENDER_PROCUREMENT_PORTAL",
    "COMPANY_WEBSITE_DIRECT",
    "TRADE_NEWS_PUBLICATION",
})

PROVIDER_INTERFACE_STATUSES = frozenset({
    "INTERFACE_READY",
    "FIXTURE_TESTED",
    "LIVE_READ_VERIFIED",
    "LIVE_READ_BLOCKED",
    "NOT_INTEGRATED",
    "UNKNOWN",
})


class IranSourceAdapter(Protocol):
    provider_id: str
    source_family: str

    def search(self, query: str, *, max_results: int) -> tuple[SearchResult, ...]: ...


@dataclass(frozen=True)
class NullIranSourceAdapter:
    """The only adapter shipped for any Iranian source family: graceful degradation,
    never fabrication. Matches research_evidence.SearchProvider's shape exactly so it can
    be dropped straight into run_research_query()'s ``providers=`` mapping today, and swapped
    for a real adapter of the same source_family later without touching calling code.
    """

    source_family: str
    provider_id: str = ""

    def __post_init__(self) -> None:
        if self.source_family not in IRAN_SOURCE_FAMILIES:
            raise ValueError("invalid_iran_source_family")
        if not self.provider_id:
            object.__setattr__(self, "provider_id", f"null-{self.source_family.lower()}")

    def search(self, query: str, *, max_results: int) -> tuple[SearchResult, ...]:
        return ()


def build_null_iran_source_registry() -> dict[str, NullIranSourceAdapter]:
    """One Null adapter per known source family, keyed by ``provider_id`` -- ready to pass
    directly as the ``providers`` mapping to research_evidence.run_research_query(). Every
    entry returns zero results; none has ever performed a live read.
    """
    registry: dict[str, NullIranSourceAdapter] = {}
    for family in sorted(IRAN_SOURCE_FAMILIES):
        adapter = NullIranSourceAdapter(source_family=family)
        registry[adapter.provider_id] = adapter
    return registry


@dataclass(frozen=True)
class IranSourceIntegrationStatus:
    """One row of IRAN_REAL_SOURCE_INTEGRATION_STATE -- the honest state of one source
    family. ``provider_interface_status`` must never be reported past what has actually
    been done: an interface existing and passing fixture tests is not evidence that a live
    read has ever succeeded.
    """

    source_family: str
    intended_commercial_use: str
    provider_interface_status: str
    fixture_tested: bool
    live_access_attempted: bool
    live_read_verified: bool
    limitations: str
    dependency: str | None
    next_integration_step: str

    def validate(self) -> None:
        if self.source_family not in IRAN_SOURCE_FAMILIES:
            raise ValueError("invalid_iran_source_family")
        if self.provider_interface_status not in PROVIDER_INTERFACE_STATUSES:
            raise ValueError("invalid_provider_interface_status")
        if self.live_read_verified and not self.live_access_attempted:
            raise ValueError("live_read_verified_requires_live_access_attempted")
        if self.live_read_verified and self.provider_interface_status != "LIVE_READ_VERIFIED":
            raise ValueError("live_read_verified_flag_inconsistent_with_status")
        for field_name in ("intended_commercial_use", "limitations", "next_integration_step"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"invalid_{field_name}")


def iran_source_integration_report() -> tuple[IranSourceIntegrationStatus, ...]:
    """The current, honestly-reported integration maturity of every target Iranian source
    family. As of this report, every family is INTERFACE_READY + FIXTURE_TESTED and nothing
    further: no live read has been attempted against any real Iranian source from this
    codebase. A row may only be promoted past this once a real adapter for that family has
    actually performed and independently verified a live read end-to-end through this
    pipeline -- not on the strength of this module existing.
    """
    rows = (
        IranSourceIntegrationStatus(
            source_family="IRICA_CUSTOMS",
            intended_commercial_use=(
                "Cross-reference declared import/export commodity flows against candidate "
                "buyer/supplier entities discovered elsewhere in the pipeline."
            ),
            provider_interface_status="INTERFACE_READY",
            fixture_tested=True,
            live_access_attempted=False,
            live_read_verified=False,
            limitations=(
                "No confirmed public, machine-readable, per-shipment endpoint has been "
                "located or accessed; aggregate trade-statistics publications are a "
                "different (coarser) data shape than the per-entity signal this pipeline "
                "needs, and have not been evaluated either."
            ),
            dependency="Unknown: requires locating and confirming an accessible public data surface and its terms of use.",
            next_integration_step=(
                "Identify one concrete, publicly documented customs-data endpoint or "
                "published dataset, confirm its terms of use, and record a single read-only "
                "fixture probe against it before writing any adapter code."
            ),
        ),
        IranSourceIntegrationStatus(
            source_family="CHAMBER_OF_COMMERCE",
            intended_commercial_use=(
                "Discover member-directory listings (producer/exporter/importer entities) "
                "for national and provincial chambers as a candidate-entity source."
            ),
            provider_interface_status="INTERFACE_READY",
            fixture_tested=True,
            live_access_attempted=False,
            live_read_verified=False,
            limitations=(
                "Provincial chamber sites are not yet enumerated; whether member listings "
                "are publicly readable or login-gated is unverified."
            ),
            dependency=None,
            next_integration_step=(
                "Enumerate 2-3 candidate chamber directory URLs, confirm they are publicly "
                "readable without authentication, and record one fixture sample page shape."
            ),
        ),
        IranSourceIntegrationStatus(
            source_family="INDUSTRIAL_DIRECTORY",
            intended_commercial_use="Bulk-discover manufacturer/producer entities by sector for buyer/supplier candidate generation.",
            provider_interface_status="INTERFACE_READY",
            fixture_tested=True,
            live_access_attempted=False,
            live_read_verified=False,
            limitations="No specific directory site has been identified or evaluated for access terms.",
            dependency=None,
            next_integration_step="Identify one candidate public industrial-directory site and confirm robots.txt/ToS allow automated reads.",
        ),
        IranSourceIntegrationStatus(
            source_family="INDUSTRIAL_ESTATE_DIRECTORY",
            intended_commercial_use="Discover tenant/member companies of specific industrial estates/zones as a geography-anchored candidate-entity source.",
            provider_interface_status="INTERFACE_READY",
            fixture_tested=True,
            live_access_attempted=False,
            live_read_verified=False,
            limitations="No estate-authority directory site has been identified or evaluated.",
            dependency=None,
            next_integration_step="Identify one candidate industrial-estate authority site and confirm public tenant-listing access.",
        ),
        IranSourceIntegrationStatus(
            source_family="B2B_MARKETPLACE",
            intended_commercial_use="Discover Persian-language B2B listings (offer-to-sell/buy postings) as a demand/supply signal source.",
            provider_interface_status="INTERFACE_READY",
            fixture_tested=True,
            live_access_attempted=False,
            live_read_verified=False,
            limitations=(
                "Marketplace listings are self-reported and would enter this pipeline as "
                "EvidenceClass.CLAIM at most, never FACT; no specific marketplace site has "
                "been identified or evaluated for access terms."
            ),
            dependency=None,
            next_integration_step="Identify one candidate marketplace site, confirm public read access, and map its listing shape to SearchResult.",
        ),
        IranSourceIntegrationStatus(
            source_family="TENDER_PROCUREMENT_PORTAL",
            intended_commercial_use=(
                "Surface government/quasi-government tender notices as demand-signal "
                "evidence -- always classified as GOVERNMENT_TENDERING_BODY per "
                "market_intelligence.py's role taxonomy, never itself treated as the buyer."
            ),
            provider_interface_status="INTERFACE_READY",
            fixture_tested=True,
            live_access_attempted=False,
            live_read_verified=False,
            limitations="No specific tender-portal site has been identified or evaluated.",
            dependency=None,
            next_integration_step="Identify one candidate public tender-notice site and confirm public listing access without authentication.",
        ),
        IranSourceIntegrationStatus(
            source_family="COMPANY_WEBSITE_DIRECT",
            intended_commercial_use="Read a specific candidate entity's own public website directly once identified elsewhere, as a corroborating/contactability signal.",
            provider_interface_status="INTERFACE_READY",
            fixture_tested=True,
            live_access_attempted=False,
            live_read_verified=False,
            limitations="Depends entirely on which candidate entity is being verified; no specific target has been read.",
            dependency=None,
            next_integration_step="Once a real candidate entity exists from an approved discovery run, fetch and record its own public website as one fixture case.",
        ),
        IranSourceIntegrationStatus(
            source_family="TRADE_NEWS_PUBLICATION",
            intended_commercial_use="Surface Persian trade/industry news mentions as low-weight corroborating or freshness evidence, never as a primary buyer/supplier source.",
            provider_interface_status="INTERFACE_READY",
            fixture_tested=True,
            live_access_attempted=False,
            live_read_verified=False,
            limitations="No specific publication site has been identified or evaluated.",
            dependency=None,
            next_integration_step="Identify one candidate Persian trade-news site with a public RSS/HTML feed and confirm read access.",
        ),
    )
    for row in rows:
        row.validate()
    if {row.source_family for row in rows} != IRAN_SOURCE_FAMILIES:
        raise ValueError("integration_report_incomplete")
    return rows
