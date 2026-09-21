"""NEXUS Persistent Steel Kernel - preflight, routing, freshness, ingestion.

DESIGN DECISION: THIS KERNEL POINTS, IT DOES NOT COPY
=====================================================
An audit on 2026-09-21 found that most of the registers a kernel would want
already exist in this repository under other names. Duplicating them would
create two sources of truth, which is the exact failure this kernel is meant to
prevent. So the kernel holds routing, policy and checks - and POINTS at the
existing artifacts for the data:

  claims            -> intake JSON, initial_claims (append-only, _batch tagged)
  contradictions    -> intake JSON, open_contradictions
  supersession      -> intake JSON, claim states + _reconciliation_note
  evidence index    -> intake JSON, evidence_log + docs/expert_foundry/evidence/
  failure memory    -> .nexus/expert_foundry/registers/ENGINEERING_FAILURE_MEMORY.md
  sources/benchmark -> .nexus/expert_foundry/registers/PRIOR_ART_AND_BENCHMARK_REGISTER.md
  market/technology -> .nexus/expert_foundry/registers/TECHNOLOGY_RADAR_AND_MARKET_EVIDENCE.md
  authority         -> docs/authority/AUTHORITY_STATUS.md
  action gates      -> steel_action_gates.py
  obsolete-data bar -> steel_action_gates.detect_obsolete_values()

WHAT IS GENUINELY NEW HERE: project scoping, freshness/TTL, capability routing,
token budgeting, the evidence-ingestion event, and the fail-loud checks.

This module performs no external action, proposes no operating parameter, and
opens no gate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum

PROJECT_ID = "rolling_mill_strip_300_pilot"
PROJECT_ALIASES = ("PRJ-STEEL-ROLLING-LINE-01", "expert foundry", "rolling mill",
                   "خط نورد", "steel rolling line")

# Other projects in this repository. Their data must never enter a steel answer.
FOREIGN_PROJECTS = {
    "PRJ-HYD-01": ("hydrotester", "hydrostatic", "هیدرو"),
    "PRJ-KCL-01": ("kcl", "potassium chloride", "پتاس"),
    "PRJ-CAN-01": ("can forming", "can-forming"),
    "PRJ-FAL-01": ("ferroalloy", "ferromanganese", "ferrosilicon", "فروآلیاژ"),
}


class EpistemicClass(str, Enum):
    FACT = "FACT"
    MEASUREMENT = "MEASUREMENT"
    CLAIM = "CLAIM"
    ESTIMATE = "ESTIMATE"
    ASSUMPTION = "ASSUMPTION"
    HYPOTHESIS = "HYPOTHESIS"
    UNKNOWN = "UNKNOWN"


class ExecutionStatus(str, Enum):
    DESIGNED = "DESIGNED"
    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    COMMITTED = "COMMITTED"
    PUSHED = "PUSHED"
    MERGED = "MERGED"
    DEPLOYED = "DEPLOYED"
    ACTIVE = "ACTIVE"
    PRODUCTION_VERIFIED = "PRODUCTION-VERIFIED"


class Freshness(str, Enum):
    STABLE = "STABLE"      # no TTL - drawings, measurements, physics
    FRESH = "FRESH"
    AGING = "AGING"
    STALE = "STALE"


class TokenClass(str, Enum):
    T1 = "T1"   # simple answer - checkpoint + directly relevant records only
    T2 = "T2"   # technical analysis - project state, code/skill, at most one agent
    T3 = "T3"   # major decision - full retrieval, up to three independent roles


# TTLs in days for data that changes on its own. STABLE subjects are absent
# deliberately: a CAD measurement does not expire.
TTL_DAYS = {
    "price": 14,
    "market": 30,
    "supplier": 60,
    "technology": 120,
    "patent": 180,
    "standard": 365,
    "git_state": 0,          # always re-fetch before any code operation
    "production_rate": 30,
    "deployment_state": 1,
}

STABLE_SUBJECTS = frozenset({
    "drawing", "measurement", "physics", "nameplate", "geometry", "chemistry",
})


@dataclass(frozen=True)
class ScopeResult:
    project_id: str | None
    matched_alias: str | None
    foreign_projects_mentioned: tuple[str, ...]
    contaminated: bool
    note: str


def resolve_scope(text: str) -> ScopeResult:
    """Decide which project a request belongs to, and refuse silent blending."""
    if not isinstance(text, str):
        raise ValueError("request text must be a string")
    low = text.casefold()
    alias = next((a for a in PROJECT_ALIASES if a.casefold() in low), None)
    if PROJECT_ID.casefold() in low:
        alias = alias or PROJECT_ID
    foreign = tuple(pid for pid, keys in FOREIGN_PROJECTS.items()
                    if pid.casefold() in low or any(k.casefold() in low for k in keys))
    is_steel = alias is not None
    contaminated = bool(is_steel and foreign)
    if contaminated:
        note = ("request names the steel project AND " + ", ".join(foreign) +
                " - data must NOT be blended; answer each project from its own records")
    elif is_steel:
        note = "steel project scope confirmed"
    elif foreign:
        note = "not a steel request - route to " + ", ".join(foreign)
    else:
        note = "no project identified; ask before assuming steel"
    return ScopeResult(PROJECT_ID if is_steel else None, alias, foreign, contaminated, note)


def freshness_of(subject: str, retrieved_at: date, today: date | None = None) -> Freshness:
    """Classify a record's freshness. STABLE subjects never go stale."""
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("subject is required")
    if not isinstance(retrieved_at, date):
        raise ValueError("retrieved_at must be a date")
    today = today or date.today()
    if today < retrieved_at:
        raise ValueError("retrieved_at is in the future")
    key = subject.strip().casefold()
    if key in STABLE_SUBJECTS:
        return Freshness.STABLE
    ttl = TTL_DAYS.get(key)
    if ttl is None:
        raise ValueError(f"no TTL policy for subject '{subject}' - add one before relying on it")
    age = (today - retrieved_at).days
    if ttl == 0:
        return Freshness.FRESH if age == 0 else Freshness.STALE
    if age <= ttl:
        return Freshness.FRESH
    if age <= 2 * ttl:
        return Freshness.AGING
    return Freshness.STALE


@dataclass(frozen=True)
class Route:
    kind: str
    token_class: TokenClass
    capabilities: tuple[str, ...]
    needs_live_research: bool
    needs_independent_review: bool
    action_gate: str
    note: str = ""


ROUTES = {
    "lookup": Route("lookup", TokenClass.T1, ("checkpoint", "intake"), False, False,
                    "none", "single recorded value; no agent, no research"),
    "calculation": Route("calculation", TokenClass.T2,
                         ("intake", "steel_action_gates", "rolling_line_concept"),
                         False, False, "concept_calculation_allowed",
                         "run the code; do not reason numerically in prose"),
    "major_decision": Route("major_decision", TokenClass.T3,
                            ("intake", "steel_action_gates", "rolling_line_concept",
                             "independent_reviewer"),
                            True, True, "fabrication_release_allowed",
                            "independent review is mandatory here"),
    "market": Route("market", TokenClass.T3,
                    ("market_register", "steel_intelligence_agent"), True, False,
                    "none", "refresh before any economic decision; never send anything"),
    "invention": Route("invention", TokenClass.T3,
                       ("failure_memory", "prior_art_register", "steel_intelligence_agent",
                        "independent_reviewer"),
                       True, True, "none",
                       "prior art BEFORE calling anything an invention"),
    "new_engineer_data": Route("new_engineer_data", TokenClass.T2,
                               ("intake", "steel_action_gates"), False, False,
                               "none", "run ingest_new_evidence; never overwrite silently"),
    "code": Route("code", TokenClass.T2, ("git_fetch", "tests"), False, False,
                  "merge_to_protected_branch", "fetch first; branch only; no merge"),
}


def route_request(kind: str) -> Route:
    if kind not in ROUTES:
        raise ValueError(f"unknown request kind '{kind}'; known: {sorted(ROUTES)}")
    return ROUTES[kind]


# ---------------------------------------------------------------------------
# Evidence ingestion - the engineer-changes-a-number event
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IngestionVerdict:
    accepted_as: str                     # NEW | CORRECTION | SEPARATE_SUBJECT | REJECTED
    creates_contradiction: bool
    supersedes_existing: bool
    affected_calculations: tuple[str, ...]
    blockers: tuple[str, ...]
    note: str


CALC_DEPENDENCIES = {
    "roll_diameter": ("contact_length", "bite_limit", "surface_speed", "roll_force",
                      "torque", "power", "barrel_deflection"),
    "barrel_length": ("barrel_deflection",),
    "billet_section": ("mass_balance", "product_length", "reduction_ratio", "pass_schedule"),
    "billet_length": ("mass_balance", "product_length", "cycle_time"),
    "motor_power": ("drive_limit", "pass_schedule", "capacity"),
    "motor_rpm": ("surface_speed", "strain_rate", "capacity", "mass_flow"),
    "gearbox_ratio": ("surface_speed", "torque", "mass_flow"),
    "roll_material": ("neck_stress_allowable", "fabrication_gate"),
    "temperature": ("flow_stress", "roll_force", "torque", "power"),
}


def ingest_new_evidence(subject: str, new_value, new_unit: str,
                        new_class: EpistemicClass, source_locator: str,
                        existing_value=None, existing_class: EpistemicClass | None = None,
                        same_equipment: bool = True) -> IngestionVerdict:
    """Section 7: a new number never silently overwrites an old one.

    Rules enforced:
      - anonymous evidence is rejected outright
      - a CLAIM may not silently displace a MEASUREMENT
      - different equipment means a separate record, not a correction
      - any change publishes the list of calculations it invalidates
    """
    blockers: list[str] = []
    if not isinstance(source_locator, str) or not source_locator.strip():
        blockers.append("no source locator - anonymous evidence is never ingested")
    if not isinstance(new_unit, str) or not new_unit.strip():
        blockers.append("no unit stated - a bare number cannot be ingested")
    if not isinstance(new_class, EpistemicClass):
        blockers.append("epistemic class must be stated explicitly")
    if blockers:
        return IngestionVerdict("REJECTED", False, False, (), tuple(blockers),
                                "fix the record before it can enter the register")

    affected = CALC_DEPENDENCIES.get(subject.strip().casefold(), ())

    if existing_value is None:
        return IngestionVerdict("NEW", False, False, affected, (),
                                "no existing record for this subject; recorded as new")

    if not same_equipment:
        return IngestionVerdict("SEPARATE_SUBJECT", False, False, (), (),
                                "different equipment - this is a new record, NOT a correction "
                                "of the existing one; neither value is superseded")

    if new_value == existing_value:
        return IngestionVerdict("NEW", False, False, (), (),
                                "value agrees with the existing record; recorded as corroboration")

    downgrade = (existing_class is EpistemicClass.MEASUREMENT
                 and new_class in (EpistemicClass.CLAIM, EpistemicClass.ESTIMATE,
                                   EpistemicClass.ASSUMPTION, EpistemicClass.HYPOTHESIS))
    if downgrade:
        return IngestionVerdict(
            "CORRECTION", True, False, affected,
            ("a CLAIM cannot silently displace a MEASUREMENT",),
            "contradiction registered; the MEASUREMENT stays the active value until an "
            "equally strong source replaces it. Owner decides.")

    return IngestionVerdict(
        "CORRECTION", True, True, affected, (),
        "contradiction registered and supersession PROPOSED; the previous value is retained "
        "in the register and the listed calculations are marked STALE until re-run")


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PreflightResult:
    project_id: str | None
    route: Route | None
    scope: ScopeResult
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    stale_subjects: tuple[str, ...]
    passed: bool
    surface_to_user: bool
    capabilities_to_load: tuple[str, ...] = field(default_factory=tuple)


def preflight(request_text: str, kind: str, intake: dict | None = None,
              retrieved: dict[str, date] | None = None,
              today: date | None = None) -> PreflightResult:
    """Run before answering anything about the steel project.

    Light by design: it reads the checkpoint-level facts and the records the
    route actually needs, not the whole history. It surfaces itself to the user
    only when it finds a blocker or a contradiction.
    """
    scope = resolve_scope(request_text)
    blockers: list[str] = []
    warnings: list[str] = []
    stale: list[str] = []

    if scope.contaminated:
        blockers.append(scope.note)
    if scope.project_id is None and not scope.foreign_projects_mentioned:
        warnings.append("project not identified from the request text")

    try:
        route = route_request(kind)
    except ValueError as exc:
        return PreflightResult(scope.project_id, None, scope, (str(exc),), (), (), False, True)

    if intake is not None:
        try:
            from steel_action_gates import detect_obsolete_values, evaluate
            obsolete = detect_obsolete_values(intake)
            if obsolete:
                blockers.extend(f"obsolete active value: {v}" for v in obsolete)
            gates = evaluate(intake)
            if route.action_gate == "concept_calculation_allowed" and not gates.concept_calculation_allowed:
                blockers.append("concept calculation gate is closed: "
                                + "; ".join(gates.concept_blockers[:3]))
            if route.action_gate == "fabrication_release_allowed" and not gates.fabrication_release_allowed:
                warnings.append(f"fabrication gate closed ({len(gates.fabrication_blockers)} blockers) "
                                "- analysis may proceed, release may not")
            contradictions = intake.get("open_contradictions", [])
            if contradictions:
                warnings.append(f"{len(contradictions)} open contradictions on record")
        except ImportError:
            warnings.append("steel_action_gates unavailable - gate state not checked")

    for subject, when in (retrieved or {}).items():
        try:
            f = freshness_of(subject, when, today)
        except ValueError:
            warnings.append(f"no freshness policy for '{subject}'")
            continue
        if f is Freshness.STALE:
            stale.append(subject)
            if route.needs_live_research:
                blockers.append(f"'{subject}' is STALE and this route requires current data")
            else:
                warnings.append(f"'{subject}' is STALE - do not use it in a decision")
        elif f is Freshness.AGING:
            warnings.append(f"'{subject}' is AGING - refresh before any commitment")

    passed = not blockers
    return PreflightResult(
        project_id=scope.project_id, route=route, scope=scope,
        blockers=tuple(blockers), warnings=tuple(warnings), stale_subjects=tuple(stale),
        passed=passed, surface_to_user=bool(blockers or stale),
        capabilities_to_load=route.capabilities,
    )


def capacity_statement(t_per_hour_low: float, t_per_hour_high: float,
                       handling_assumption_s: float, measured: bool) -> str:
    """Section 14 replay 4: an estimated capacity must never be stated as actual."""
    if measured:
        return (f"Measured capacity {t_per_hour_low:.1f}-{t_per_hour_high:.1f} t/h "
                f"from timed observation.")
    return (f"ESTIMATED capacity {t_per_hour_low:.1f}-{t_per_hour_high:.1f} t/h. "
            f"NOT a measured figure. Dominated by an ASSUMPTION of "
            f"{handling_assumption_s:.0f} s handling per pass, which has never been "
            f"measured; doubling it removes roughly 40% of the output. "
            f"Do not plan against this number.")
