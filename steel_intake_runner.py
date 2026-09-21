"""Batch intake runner - what happens the moment the engineer's answers arrive.

WHY THIS EXISTS
===============
steel_kernel.ingest_new_evidence() handles ONE fact. A real engineer reply is a
page of them, and the useful output is not per-fact verdicts but the aggregate:

    which UNKNOWNs did this close?
    which contradictions did it create?
    which previously-computed results are now STALE?
    did any gate change state?
    what is now the highest-value remaining question?

That aggregate is what turns a page of answers into a decision. This module
produces it in one call so nothing is missed and nothing is silently accepted.

It writes nothing and opens no gate. It reports.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from steel_kernel import (
    CALC_DEPENDENCIES, EpistemicClass, IngestionVerdict, ingest_new_evidence,
)

# ---------------------------------------------------------------------------
# The project's open UNKNOWNs, and what answering each one actually unlocks.
# Kept here so an incoming answer is immediately scored for consequence rather
# than just recorded. Sourced from .nexus/steel/CHECKPOINT.md.
# ---------------------------------------------------------------------------
UNKNOWN_UNLOCK_MAP = {
    "roll_material": {
        "why_it_matters": "Neck bending stress reaches ~159 MPa at 300mm width: fine for a "
                          "forged steel roll, out of range for cast iron. Ternium-Siderar failed "
                          "at the necks and bearings, not the motor.",
        "unlocks": ("fabrication_release_allowed", "width_increase_decision",
                    "neck_stress_allowable"),
        "blocks_today": "any decision to widen the product",
    },
    "stand_rated_force": {
        "why_it_matters": "An old stand pushed past its ORIGINAL force rating fails at bearings "
                          "and roll necks. Without the rating there is nothing to compare "
                          "computed force against.",
        "unlocks": ("fabrication_release_allowed", "draft_depth_envelope"),
        "blocks_today": "any deeper-draft or higher-force proposal",
    },
    "groove_geometry": {
        "why_it_matters": "Flat-rolling spread predicts ~183mm; the mill makes 250mm. If width "
                          "comes from grooves, the concept model has the WRONG deformation mode "
                          "and every force/torque/power result must be rebuilt.",
        "unlocks": ("deformation_mode", "caliber_design_for_300mm", "roll_force", "torque", "power"),
        "blocks_today": "the validity of the entire concept model",
    },
    "process_temperature": {
        "why_it_matters": "At 1000C instead of the assumed 1150C, flow stress rises 50-60% and "
                          "both the torque and power limits are exceeded on continuous duty. The "
                          "claimed motor margin is unsupported until this is measured.",
        "unlocks": ("flow_stress", "roll_force", "torque", "power", "drive_margin"),
        "blocks_today": "any claim that the motor has headroom",
    },
    "motor_nameplate_stator": {
        "why_it_matters": "420V/2300A single-phase is 0.966 MVA, below 1250 kW - impossible. "
                          "Almost certainly a ROTOR rating on a slip-ring machine, with a medium-"
                          "voltage stator. Until split, the drive data is internally inconsistent.",
        "unlocks": ("drive_limit", "electrical_consistency"),
        "blocks_today": "trust in every drive-side number",
    },
    "st2_motor_rpm": {
        "why_it_matters": "At 1:7.8 a 1000 rpm motor would run ST2 faster than ST3, impossible in "
                          "tandem. Hypothesis is 700-800 rpm. If wrong, the stands are not a "
                          "tandem train and the capacity model must be rewritten.",
        "unlocks": ("mass_flow", "capacity", "tandem_hypothesis"),
        "blocks_today": "the whole capacity chain",
    },
    "handling_time": {
        "why_it_matters": "49-71% of cycle time on an assumption of 6 s/pass that was never "
                          "measured. Doubling it removes ~40% of output.",
        "unlocks": ("capacity", "bottleneck_ranking"),
        "blocks_today": "any capacity figure being quotable",
    },
    "furnace": {
        "why_it_matters": "No data of any kind. Could be the real throughput constraint rather "
                          "than the mill.",
        "unlocks": ("capacity", "energy_per_tonne", "bottleneck_ranking"),
        "blocks_today": "knowing where the true bottleneck is",
    },
    "p1_p10_meaning": {
        "why_it_matters": "A handwritten table exists whose columns and units are unknown. "
                          "Hypothesis: a 10-pass schedule. Never tested.",
        "unlocks": ("pass_schedule_evidence",),
        "blocks_today": "using real mill practice instead of an invented schedule",
    },
    "gearbox_rated_torque": {
        "why_it_matters": "Computed pass torque reaches 112.4 kN.m, exactly at the drive's "
                          "capability. Nothing states the gearbox's own allowable.",
        "unlocks": ("fabrication_release_allowed", "drive_limit"),
        "blocks_today": "any claim the drivetrain is adequate",
    },
    "bearing_capacity": {
        "why_it_matters": "The Ternium failure mode. No rating on file.",
        "unlocks": ("fabrication_release_allowed",),
        "blocks_today": "any force-increase proposal",
    },
    "steel_certificate": {
        "why_it_matters": "'St37' is a name the engineer recalls. No chemistry, no mill "
                          "certificate. Flow stress, and therefore every force result, rests on it.",
        "unlocks": ("flow_stress_calibration", "grade_confirmation"),
        "blocks_today": "confidence in the material model",
    },
}


@dataclass(frozen=True)
class EngineerFact:
    """One statement from the engineer, as received - not yet interpreted."""
    subject: str
    value: object
    unit: str
    epistemic_class: EpistemicClass
    source_locator: str
    equipment_id: str = "ST1"
    closes_unknown: str | None = None
    existing_value: object = None
    existing_class: EpistemicClass | None = None
    same_equipment: bool = True
    note: str = ""

    def validate(self) -> None:
        if not isinstance(self.subject, str) or not self.subject.strip():
            raise ValueError("subject is required")
        if self.closes_unknown is not None and self.closes_unknown not in UNKNOWN_UNLOCK_MAP:
            raise ValueError(f"unknown id '{self.closes_unknown}' is not in the unlock map")


@dataclass(frozen=True)
class BatchImpact:
    accepted: tuple[tuple[str, IngestionVerdict], ...]
    rejected: tuple[tuple[str, IngestionVerdict], ...]
    contradictions: tuple[str, ...]
    stale_calculations: tuple[str, ...]
    unknowns_closed: tuple[str, ...]
    unknowns_remaining: tuple[str, ...]
    gates_unlocked: tuple[str, ...]
    needs_owner_decision: tuple[str, ...]
    highest_value_remaining: tuple[str, ...]
    summary: str = ""


def _rank_remaining(remaining) -> tuple[str, ...]:
    """Rank open unknowns by how much they unlock. Deterministic."""
    return tuple(sorted(remaining,
                        key=lambda u: (-len(UNKNOWN_UNLOCK_MAP[u]["unlocks"]), u)))


def ingest_batch(facts, already_closed=()) -> BatchImpact:
    """Run a page of engineer answers through the full discipline in one pass."""
    items = tuple(facts)
    if not items:
        raise ValueError("no facts supplied - nothing to ingest")

    accepted, rejected = [], []
    contradictions, stale, closed, owner = [], [], [], []

    for f in items:
        f.validate()
        v = ingest_new_evidence(
            f.subject, f.value, f.unit, f.epistemic_class, f.source_locator,
            existing_value=f.existing_value, existing_class=f.existing_class,
            same_equipment=f.same_equipment)
        label = f"{f.equipment_id}:{f.subject}"
        if v.accepted_as == "REJECTED":
            rejected.append((label, v))
            continue
        accepted.append((label, v))
        if v.creates_contradiction:
            contradictions.append(f"{label} - {v.note}")
        if v.blockers:
            owner.extend(f"{label}: {b}" for b in v.blockers)
        stale.extend(v.affected_calculations)
        if f.closes_unknown and v.accepted_as != "REJECTED":
            # A CLAIM that merely contradicts a MEASUREMENT does not close anything.
            if not (v.creates_contradiction and not v.supersedes_existing):
                closed.append(f.closes_unknown)

    closed_set = set(closed) | set(already_closed)
    remaining = [u for u in UNKNOWN_UNLOCK_MAP if u not in closed_set]

    unlocked = set()
    for u in closed_set:
        if u in UNKNOWN_UNLOCK_MAP:
            unlocked |= set(UNKNOWN_UNLOCK_MAP[u]["unlocks"])
    # a gate only truly unlocks when NOTHING still open feeds it
    still_blocked = set()
    for u in remaining:
        still_blocked |= set(UNKNOWN_UNLOCK_MAP[u]["unlocks"])
    genuinely_unlocked = tuple(sorted(unlocked - still_blocked))

    ranked = _rank_remaining(remaining)
    summary = (
        f"{len(accepted)} accepted, {len(rejected)} rejected, "
        f"{len(contradictions)} contradiction(s), "
        f"{len(set(stale))} calculation(s) now STALE, "
        f"{len(closed_set)} unknown(s) closed, {len(remaining)} still open."
    )
    return BatchImpact(
        accepted=tuple(accepted), rejected=tuple(rejected),
        contradictions=tuple(contradictions),
        stale_calculations=tuple(sorted(set(stale))),
        unknowns_closed=tuple(sorted(closed_set)),
        unknowns_remaining=ranked,
        gates_unlocked=genuinely_unlocked,
        needs_owner_decision=tuple(owner),
        highest_value_remaining=ranked[:3],
        summary=summary,
    )


def readiness_report(already_closed=()) -> dict:
    """What is open right now, ranked by consequence. Run before data arrives."""
    closed = set(already_closed)
    remaining = [u for u in UNKNOWN_UNLOCK_MAP if u not in closed]
    ranked = _rank_remaining(remaining)
    return {
        "open_unknowns": len(remaining),
        "closed": sorted(closed),
        "ranked_by_consequence": [
            {"unknown": u,
             "unlocks": list(UNKNOWN_UNLOCK_MAP[u]["unlocks"]),
             "blocks_today": UNKNOWN_UNLOCK_MAP[u]["blocks_today"],
             "why": UNKNOWN_UNLOCK_MAP[u]["why_it_matters"]}
            for u in ranked
        ],
        "note": "Closing an unknown records evidence. It does not by itself open any "
                "fabrication, purchase or operating gate.",
    }
