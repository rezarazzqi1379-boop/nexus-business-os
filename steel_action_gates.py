"""Two-output action gate for PRJ-STEEL-ROLLING-LINE-01.

WHY THIS EXISTS
===============
`rolling_mill_intake.assess()` returns a single `calculation_allowed` flag that
is False until the entire engineer interview is complete - furnace data, process
temperature, equipment limits, safety verification and one historical run
included. That was correct for the original retrospective-only study.

The owner has since authorised concept design and pre-engineering, and moved the
approval gate to: fabrication drawing release, final critical-material
selection, structural/electrical sign-off, physical machine change, binding
purchase, installation and hot commissioning.

Those are two genuinely different questions, and one boolean cannot answer both:

  concept_calculation_allowed - may we compute, with explicit assumptions, in
      order to decide what to investigate next? This needs only the geometry
      and drive data the concept model actually consumes.

  fabrication_release_allowed - may we release for build, buy, install or run?
      This needs everything, including the things a calculation can legitimately
      assume but a workshop cannot.

THIS MODULE IS ADDITIVE. It does not modify, wrap or weaken
`rolling_mill_intake.py`; that module keeps its meaning and its tests. Nothing
here can set `fabrication_release_allowed` True on the current data, and no
caller may treat `concept_calculation_allowed` as authorisation to touch the
machine.
"""
from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------
# Physical plausibility bands. These exist to catch transcription and unit
# errors, NOT to validate engineering choices. A value outside a band is
# rejected as a suspected bad reading and must be re-measured, never silently
# converted.
# --------------------------------------------------------------------------
PLAUSIBLE_MM = {
    "roll_barrel_diameter": (200.0, 1500.0),
    "roll_barrel_length": (300.0, 3000.0),
    "billet_section": (50.0, 400.0),
    "billet_length": (500.0, 12000.0),
}

_UNIT_TO_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0}


def to_mm(value, unit) -> float | None:
    """Normalise a length to millimetres. Returns None if it cannot be read."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    factor = _UNIT_TO_MM.get(unit)
    if factor is None:
        return None
    return float(value) * factor


def _at(payload: dict, path: str):
    value = payload
    for segment in path.split("."):
        if not isinstance(value, dict) or segment not in value:
            return None
        value = value[segment]
    return value


def _positive_number(value) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and value > 0


# --------------------------------------------------------------------------
# Obsolete-data rejection
#
# These specific readings were carried on main until 2026-09-19 and are known
# to be wrong or physically impossible for this mill. They must never become an
# active value again. This is a regression barrier, not a style check.
# --------------------------------------------------------------------------
def detect_obsolete_values(payload: dict) -> tuple[str, ...]:
    """Return a violation string per obsolete/impossible ACTIVE value found.

    Only ACTIVE values are checked. Superseded readings preserved inside
    `initial_claims` or `open_contradictions` are evidence history and are
    deliberately NOT flagged - preserving them is required, reactivating them
    is what this guards against.
    """
    bad: list[str] = []

    section = _at(payload, "product.input_billet.cross_section_mm")
    if isinstance(section, dict):
        w, h = section.get("width"), section.get("height")
        if w == 220 and h == 220:
            bad.append("billet cross-section 220x220 is the superseded 2026-09-14 estimate")
        for axis, val in (("width", w), ("height", h)):
            if _positive_number(val):
                lo, hi = PLAUSIBLE_MM["billet_section"]
                if not lo <= float(val) <= hi:
                    bad.append(f"billet {axis} {val}mm outside plausible band {lo}-{hi}mm")

    length = _at(payload, "product.input_billet.length_mm")
    if length == 3000:
        bad.append("billet length 3000mm is the superseded 2026-09-14 estimate")
    if _positive_number(length):
        lo, hi = PLAUSIBLE_MM["billet_length"]
        if not lo <= float(length) <= hi:
            bad.append(f"billet length {length}mm outside plausible band {lo}-{hi}mm")

    dia = _at(payload, "mill.rolls.reported_diameter_around")
    if isinstance(dia, dict):
        mm = to_mm(dia.get("value"), dia.get("unit"))
        if mm is None:
            bad.append("roll barrel diameter has no readable value+metric unit")
        else:
            lo, hi = PLAUSIBLE_MM["roll_barrel_diameter"]
            if not lo <= mm <= hi:
                bad.append(
                    f"roll barrel diameter normalises to {mm:.0f}mm "
                    f"({dia.get('value')} {dia.get('unit')}), outside plausible band "
                    f"{lo:.0f}-{hi:.0f}mm - suspected cm/mm transcription error"
                )

    barrel = _at(payload, "mill.rolls.barrel_length")
    if isinstance(barrel, dict):
        mm = to_mm(barrel.get("value"), barrel.get("unit"))
        if mm is None:
            bad.append("roll barrel length has no readable value+metric unit")
        else:
            lo, hi = PLAUSIBLE_MM["roll_barrel_length"]
            if not lo <= mm <= hi:
                bad.append(
                    f"roll barrel length normalises to {mm:.0f}mm "
                    f"({barrel.get('value')} {barrel.get('unit')}), outside plausible band "
                    f"{lo:.0f}-{hi:.0f}mm - suspected cm/mm transcription error"
                )

    if _at(payload, "drive.motor.rated_power_kw") is None:
        bad.append("motor rated_power_kw is null - the pre-engineer intake had no drive data")

    ratio = _at(payload, "drive.gearbox.ratio")
    if isinstance(ratio, dict) and ratio.get("input") == 10 and ratio.get("output") == 1:
        bad.append("gearbox ratio 10:1 is the superseded 2026-09-14 estimate (engineer stated 1:9.8)")

    return tuple(dict.fromkeys(bad))


# --------------------------------------------------------------------------
# Gate definitions
# --------------------------------------------------------------------------
CONCEPT_REQUIRED = (
    "product.input_billet.cross_section_mm",
    "product.input_billet.length_mm",
    "product.input_billet.steel_grade",
    "mill.layout",
    "mill.rolls.reported_diameter_around",
    "mill.rolls.barrel_length",
    "drive.motor.rated_power_kw",
    "drive.motor.rated_speed_rpm",
    "drive.gearbox.ratio",
)

FABRICATION_EXTRA_REQUIRED = (
    "limits.maximum_roll_force_n",
    "limits.maximum_spindle_torque_nm",
    "limits.maximum_motor_current_a",
    "drive.gearbox.rated_output_torque_nm",
    "process.reheating_temperature_degC",
    "process.historical_successful_run_locator",
    "mill.rolls.roll_material",
    "independent_engineering_review.verdict",
)

FABRICATION_SAFETY_TRUE = (
    "safety.guards_verified",
    "safety.emergency_stops_verified",
)


@dataclass(frozen=True)
class SteelActionGates:
    concept_calculation_allowed: bool
    fabrication_release_allowed: bool
    concept_blockers: tuple[str, ...]
    fabrication_blockers: tuple[str, ...]
    obsolete_values: tuple[str, ...]
    next_gate: str

    def require_concept(self) -> None:
        """Raise unless concept calculation is permitted. Fail-closed helper."""
        if not self.concept_calculation_allowed:
            raise PermissionError(
                "concept calculation not permitted: " + "; ".join(self.concept_blockers)
            )


def evaluate(payload: dict) -> SteelActionGates:
    obsolete = detect_obsolete_values(payload)

    concept_blockers: list[str] = []
    for path in CONCEPT_REQUIRED:
        value = _at(payload, path)
        if value is None or (isinstance(value, (list, dict, str)) and not value):
            concept_blockers.append(f"missing: {path}")
    section = _at(payload, "product.input_billet.cross_section_mm")
    if isinstance(section, dict) and not all(_positive_number(section.get(a)) for a in ("width", "height")):
        concept_blockers.append("product.input_billet.cross_section_mm needs positive width and height")
    ratio = _at(payload, "drive.gearbox.ratio")
    if isinstance(ratio, dict) and not all(_positive_number(ratio.get(s)) for s in ("input", "output")):
        concept_blockers.append("drive.gearbox.ratio needs positive input and output")
    for path in ("drive.motor.rated_power_kw", "drive.motor.rated_speed_rpm"):
        if not _positive_number(_at(payload, path)):
            concept_blockers.append(f"{path} must be a positive number")
    # An obsolete active value blocks concept calculation outright: computing on a
    # known-wrong machine is worse than not computing.
    concept_blockers.extend(f"obsolete/implausible active value -> {v}" for v in obsolete)

    fabrication_blockers = list(concept_blockers)
    for path in FABRICATION_EXTRA_REQUIRED:
        value = _at(payload, path)
        if value is None or (isinstance(value, (list, dict, str)) and not value):
            fabrication_blockers.append(f"missing: {path}")
    for path in FABRICATION_SAFETY_TRUE:
        if _at(payload, path) is not True:
            fabrication_blockers.append(f"{path} must be explicitly true")
    loto = _at(payload, "safety.loto_procedure_locator")
    if not (isinstance(loto, str) and loto.strip()):
        fabrication_blockers.append("missing: safety.loto_procedure_locator")

    concept_ok = not concept_blockers
    fabrication_ok = not fabrication_blockers

    if not concept_ok:
        nxt = "resolve the concept blockers above; do not compute on obsolete or implausible values"
    elif not fabrication_ok:
        nxt = ("concept calculation and pre-engineering may proceed with explicit assumptions; "
               "fabrication, purchase, machine change, installation and hot commissioning remain "
               "gated on the items listed in fabrication_blockers plus the owner's explicit approval")
    else:
        nxt = ("all recorded prerequisites are met; fabrication release still requires the owner's "
               "explicit approval and a qualified engineer's sign-off - this gate does not grant it")

    return SteelActionGates(
        concept_calculation_allowed=concept_ok,
        fabrication_release_allowed=fabrication_ok,
        concept_blockers=tuple(concept_blockers),
        fabrication_blockers=tuple(dict.fromkeys(fabrication_blockers)),
        obsolete_values=obsolete,
        next_gate=nxt,
    )
