"""Measurement campaign M1 - one field visit, one data structure.

WHY ONE PACKAGE
===============
Three separate asks (P-1 cycle timing, P-2 inter-pass width, P-3 nameplate and
roll material) plus the six conditions the independent review set on 2026-09-19
all need the same thing: somebody standing at the mill for one shift with a
camera, a pyrometer and a tape. Splitting them into three visits wastes the
expensive part, which is the visit, not the instrument.

This module is the contract for what that visit must bring back. It validates
the record, refuses anonymous or incomplete data, and hands the pass geometry
straight to caliber_spread_model so the width question is answered from the same
record that answers the timing question.

WHAT IT CLOSES
==============
  P-1  cycle-time breakdown          -> TimingEvent series
  P-2  inter-pass width mechanism    -> PassGeometry -> caliber_spread_model
  P-3  ST2 nameplate, roll material  -> CampaignFacts
  IR-1 grooved vs flat               -> same as P-2
  IR-2 motor nameplate stator/rotor  -> CampaignFacts.motor_nameplate_*
  IR-3 process temperature           -> PassGeometry.temperature_c
  IR-4 handling time over >=20 pieces-> BilletRun series
  IR-5 roll material and hardness    -> CampaignFacts
  IR-6 governing-pass force check    -> needs IR-3 + real widths, both here
  BM-1 original stand force rating   -> CampaignFacts.stand_rated_force_kn
       (added after the Ternium-Siderar benchmark: an old stand pushed past its
        original force rating failed at the bearings and roll necks, not the
        motor. Establishing that rating is now a campaign requirement.)

This module proposes no setpoint, gap, speed, temperature or schedule. It
records what the mill already does.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from caliber_spread_model import PassMeasurement

MIN_BILLETS_FOR_TIMING = 20   # per independent review condition 4


class EventKind(str, Enum):
    FURNACE_EXIT = "furnace_exit"
    PASS_START = "pass_start"
    PASS_END = "pass_end"
    MANIPULATION = "manipulation"      # return, turn, transfer between grooves
    WAIT = "wait"                      # idle, not working the piece
    SHEAR = "shear"
    PIECE_CLEAR = "piece_clear"


@dataclass(frozen=True)
class TimingEvent:
    """One timestamped event from the shift video. t_seconds is relative to the
    start of that billet's cycle."""
    kind: EventKind
    t_seconds: float
    pass_index: int | None = None
    note: str = ""

    def validate(self) -> None:
        if not isinstance(self.kind, EventKind):
            raise ValueError("kind must be an EventKind")
        if isinstance(self.t_seconds, bool) or not isinstance(self.t_seconds, (int, float)) or self.t_seconds < 0:
            raise ValueError("t_seconds must be a non-negative number")
        if self.pass_index is not None and (
            isinstance(self.pass_index, bool) or not isinstance(self.pass_index, int) or self.pass_index < 1
        ):
            raise ValueError("pass_index must be a positive integer when supplied")


@dataclass(frozen=True)
class BilletRun:
    """One billet, start to finish."""
    billet_id: str
    events: tuple[TimingEvent, ...]
    passes: tuple[PassMeasurement, ...]
    source: str

    def validate(self) -> None:
        if not isinstance(self.billet_id, str) or not self.billet_id.strip():
            raise ValueError("billet_id is required")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("every billet run needs a source locator - no anonymous data")
        if not self.events:
            raise ValueError("a billet run needs timing events")
        for e in self.events:
            e.validate()
        for p in self.passes:
            p.validate()
        times = [e.t_seconds for e in self.events]
        if times != sorted(times):
            raise ValueError("timing events must be in ascending time order")

    @property
    def cycle_seconds(self) -> float:
        return self.events[-1].t_seconds - self.events[0].t_seconds

    @property
    def rolling_seconds(self) -> float:
        """Time the rolls are actually working the piece."""
        total, open_start = 0.0, None
        for e in self.events:
            if e.kind is EventKind.PASS_START:
                open_start = e.t_seconds
            elif e.kind is EventKind.PASS_END and open_start is not None:
                total += e.t_seconds - open_start
                open_start = None
        return total

    @property
    def non_rolling_seconds(self) -> float:
        return self.cycle_seconds - self.rolling_seconds

    @property
    def handling_fraction(self) -> float:
        if self.cycle_seconds <= 0:
            raise ValueError("cycle time must be positive")
        return self.non_rolling_seconds / self.cycle_seconds


@dataclass(frozen=True)
class CampaignFacts:
    """Campaign-level facts. None means NOT COLLECTED - never assume a default."""
    stand_rated_force_kn: float | None = None        # BM-1, from the Ternium lesson
    roll_material: str | None = None                 # IR-5
    roll_hardness: str | None = None                 # IR-5
    st2_motor_rpm: float | None = None               # P-3
    st2_motor_kw: float | None = None
    motor_nameplate_stator_v: float | None = None    # IR-2
    motor_nameplate_stator_a: float | None = None
    motor_nameplate_rotor_v: float | None = None
    motor_nameplate_rotor_a: float | None = None
    gearbox_rated_torque_nm: float | None = None
    bearing_rating_locator: str | None = None
    groove_drawing_locator: str | None = None
    nameplate_photo_locators: tuple[str, ...] = field(default_factory=tuple)

    def collected(self) -> tuple[str, ...]:
        return tuple(k for k, v in self.__dict__.items()
                     if v is not None and v != () and v != "")

    def missing(self) -> tuple[str, ...]:
        return tuple(k for k, v in self.__dict__.items()
                     if v is None or v == () or v == "")


@dataclass(frozen=True)
class MeasurementCampaign:
    campaign_id: str
    runs: tuple[BilletRun, ...]
    facts: CampaignFacts

    def validate(self) -> None:
        if not isinstance(self.campaign_id, str) or not self.campaign_id.strip():
            raise ValueError("campaign_id is required")
        if not self.runs:
            raise ValueError("a campaign needs at least one billet run")
        seen = set()
        for r in self.runs:
            r.validate()
            if r.billet_id in seen:
                raise ValueError(f"duplicate billet_id: {r.billet_id}")
            seen.add(r.billet_id)

    @property
    def is_synthetic(self) -> bool:
        return any(p.is_synthetic for r in self.runs for p in r.passes) or \
               any(r.source.strip().upper().startswith("SYNTHETIC:") for r in self.runs)


def timing_summary(campaign: MeasurementCampaign) -> dict:
    """P-1 / IR-4. Refuses to report a capacity-grade number on a thin sample."""
    campaign.validate()
    cycles = [r.cycle_seconds for r in campaign.runs]
    rolling = [r.rolling_seconds for r in campaign.runs]
    handling = [r.handling_fraction for r in campaign.runs]
    n = len(cycles)
    mean_cycle = sum(cycles) / n
    enough = n >= MIN_BILLETS_FOR_TIMING
    return {
        "billets_measured": n,
        "sufficient_sample": enough,
        "mean_cycle_s": round(mean_cycle, 1),
        "min_cycle_s": round(min(cycles), 1),
        "max_cycle_s": round(max(cycles), 1),
        "mean_rolling_s": round(sum(rolling) / n, 1),
        "mean_handling_fraction": round(sum(handling) / n, 3),
        "capacity_grade": enough,
        "note": (
            f"Sample of {n} billets meets the >={MIN_BILLETS_FOR_TIMING} required by "
            "independent review condition 4; these timings may be used to replace the "
            "assumed 6 s/pass in the capacity model."
            if enough else
            f"Sample of {n} billets is BELOW the {MIN_BILLETS_FOR_TIMING} required by "
            "independent review condition 4. Indicative only - must not be used as a "
            "capacity figure or to replace the assumed handling time."
        ),
        "illustrative_only": campaign.is_synthetic,
    }


def campaign_completeness(campaign: MeasurementCampaign) -> dict:
    """Which of the campaign's obligations are actually discharged."""
    campaign.validate()
    facts = campaign.facts
    timing = timing_summary(campaign)
    has_widths = any(len(r.passes) >= 2 for r in campaign.runs)
    has_temps = any(p.temperature_c is not None for r in campaign.runs for p in r.passes)

    obligations = {
        "P-1 cycle timing": timing["sufficient_sample"],
        "P-2 inter-pass width": has_widths,
        "P-3 ST2 nameplate": facts.st2_motor_rpm is not None,
        "P-3 roll material": facts.roll_material is not None,
        "IR-2 stator/rotor split": facts.motor_nameplate_stator_v is not None
                                    and facts.motor_nameplate_rotor_v is not None,
        "IR-3 process temperature": has_temps,
        "IR-5 roll hardness": facts.roll_hardness is not None,
        "BM-1 stand force rating": facts.stand_rated_force_kn is not None,
        "groove drawings": facts.groove_drawing_locator is not None,
    }
    done = [k for k, v in obligations.items() if v]
    open_items = [k for k, v in obligations.items() if not v]
    return {
        "discharged": done,
        "outstanding": open_items,
        "complete": not open_items,
        "percent_complete": round(100.0 * len(done) / len(obligations)),
        "illustrative_only": campaign.is_synthetic,
        "note": "A complete campaign discharges the field obligations. It does NOT by "
                "itself open any fabrication, purchase or operating gate.",
    }


def pass_measurements(campaign: MeasurementCampaign) -> tuple[PassMeasurement, ...]:
    """Flatten every measured pass, for caliber_spread_model."""
    campaign.validate()
    out: list[PassMeasurement] = []
    for r in campaign.runs:
        out.extend(r.passes)
    if len(out) < 2:
        raise ValueError("need at least two measured passes to characterise width")
    return tuple(out)
