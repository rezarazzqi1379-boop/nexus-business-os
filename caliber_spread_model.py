"""IC-02 - inter-pass width forensics for PRJ-STEEL-ROLLING-LINE-01.

WHAT THIS IS FOR
================
The independent engineering review of 2026-09-19 returned REJECT, and its single
most important finding was that the width mechanism of this mill is unknown:

    natural (flat-rolling) spread from a 150mm square billet predicts ~183mm
    final width, but the mill actually produces 250mm.

That 67mm gap is not a modelling error to be tuned away. It means width is being
produced by something the flat-rolling model does not contain - almost certainly
machined caliber grooves, possibly edging or broadside passes. Until that is
settled, every force, torque, power and capacity number computed from a
flat-rolling model is built on the wrong deformation mode.

This module is the instrument that settles it. It takes width and thickness
measured after each pass on the real mill and answers three questions:

    1. Is this mill rolling flat, grooved, or edging? (diagnose_width_mechanism)
    2. How much width is the groove set actually generating, pass by pass?
       (the caliber spread factor, kappa)
    3. Given that, what does a different pass schedule plausibly reach?
       (CaliberModel.predict_final_width - a BOUND, not a design)

WHAT THIS IS NOT
================
It is not a caliber design tool. kappa is measured on the EXISTING groove set;
carrying it to an unbuilt groove is an explicit assumption, and
predict_final_width refuses to hide that - it returns a band and a warning, never
a single design number.

It performs no operational recommendation. It proposes no gap, speed,
temperature or schedule. It reads what the mill already did.

EVIDENCE DISCIPLINE
===================
Every PassMeasurement must carry a non-empty `source` locator. Measurements whose
source begins with "SYNTHETIC:" are accepted so the algorithm can be tested and
demonstrated before real data exists, but any diagnosis touching synthetic data
is stamped ILLUSTRATIVE_ONLY and can never be reported as a finding about the
real mill.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

from rolling_line_concept import wusatowski_spread

SYNTHETIC_PREFIX = "SYNTHETIC:"

# Classification thresholds. ASSUMPTION - chosen to separate the three
# deformation modes robustly, not calibrated against this mill.
WIDTH_NOISE_MM = 0.5        # below this, a width change is measurement noise
GROOVE_ASSIST_KAPPA = 1.3   # above this, the pass is generating width beyond free spread
MIN_DRAFT_MM = 0.2          # below this, the pass did not meaningfully reduce thickness


class PassMode(str, Enum):
    FREE_SPREAD = "free_spread"              # behaves like flat rolling
    GROOVE_ASSISTED = "groove_assisted"      # width gain well above natural spread
    GROOVE_CONSTRAINED = "groove_constrained"  # thickness fell, width held - side walls
    EDGING = "edging"                        # width deliberately reduced
    INDETERMINATE = "indeterminate"


class WidthMechanism(str, Enum):
    FLAT_ROLLING = "flat_rolling"
    GROOVED = "grooved"
    EDGING_SEQUENCE = "edging_sequence"
    MIXED = "mixed"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True)
class PassMeasurement:
    """One measured pass. All four dimensions measured on the real piece."""
    pass_index: int
    entry_thickness_mm: float
    exit_thickness_mm: float
    entry_width_mm: float
    exit_width_mm: float
    roll_diameter_mm: float
    source: str
    temperature_c: float | None = None

    def validate(self) -> None:
        if not isinstance(self.pass_index, int) or isinstance(self.pass_index, bool) or self.pass_index < 1:
            raise ValueError("pass_index must be a positive integer")
        for name in ("entry_thickness_mm", "exit_thickness_mm", "entry_width_mm",
                     "exit_width_mm", "roll_diameter_mm"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"{name} must be a positive number")
        if self.exit_thickness_mm > self.entry_thickness_mm:
            raise ValueError("a pass cannot increase thickness")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("every measurement needs a source locator - no anonymous data")
        if self.temperature_c is not None and (
            isinstance(self.temperature_c, bool)
            or not isinstance(self.temperature_c, (int, float))
            or self.temperature_c <= 0
        ):
            raise ValueError("temperature_c must be a positive number when supplied")

    @property
    def is_synthetic(self) -> bool:
        return self.source.strip().upper().startswith(SYNTHETIC_PREFIX)

    @property
    def draft_mm(self) -> float:
        return self.entry_thickness_mm - self.exit_thickness_mm

    @property
    def actual_width_gain_mm(self) -> float:
        return self.exit_width_mm - self.entry_width_mm


@dataclass(frozen=True)
class PassDiagnosis:
    pass_index: int
    mode: PassMode
    actual_width_gain_mm: float
    natural_width_gain_mm: float
    kappa: float | None       # actual gain / natural gain; None when undefined
    note: str


def analyse_pass_width(measurement: PassMeasurement) -> PassDiagnosis:
    """Classify one pass by comparing measured width gain against free spread."""
    measurement.validate()
    natural_exit = wusatowski_spread(
        measurement.entry_thickness_mm,
        measurement.exit_thickness_mm,
        measurement.entry_width_mm,
        measurement.roll_diameter_mm,
    )
    natural_gain = natural_exit - measurement.entry_width_mm
    actual_gain = measurement.actual_width_gain_mm

    if actual_gain < -WIDTH_NOISE_MM:
        return PassDiagnosis(measurement.pass_index, PassMode.EDGING, actual_gain, natural_gain,
                             None, "width was reduced - edging or broadside pass")

    if abs(actual_gain) <= WIDTH_NOISE_MM and measurement.draft_mm >= MIN_DRAFT_MM and natural_gain > WIDTH_NOISE_MM:
        return PassDiagnosis(measurement.pass_index, PassMode.GROOVE_CONSTRAINED, actual_gain, natural_gain,
                             0.0, "thickness fell but width held - groove side walls are containing spread")

    if natural_gain <= 1e-9:
        mode = PassMode.GROOVE_ASSISTED if actual_gain > WIDTH_NOISE_MM else PassMode.INDETERMINATE
        note = ("width grew where free spread predicts none" if mode is PassMode.GROOVE_ASSISTED
                else "no meaningful width change and no predicted spread")
        return PassDiagnosis(measurement.pass_index, mode, actual_gain, natural_gain, None, note)

    kappa = actual_gain / natural_gain
    if kappa > GROOVE_ASSIST_KAPPA:
        return PassDiagnosis(measurement.pass_index, PassMode.GROOVE_ASSISTED, actual_gain, natural_gain,
                             kappa, f"width gain is {kappa:.2f}x free spread - groove is generating width")
    return PassDiagnosis(measurement.pass_index, PassMode.FREE_SPREAD, actual_gain, natural_gain,
                         kappa, f"width gain is {kappa:.2f}x free spread - consistent with flat rolling")


@dataclass(frozen=True)
class CaliberModel:
    """Fitted description of how THIS groove set produces width."""
    mechanism: WidthMechanism
    pass_diagnoses: tuple[PassDiagnosis, ...]
    mean_kappa: float | None
    kappa_range: tuple[float, float] | None
    measured_final_width_mm: float
    flat_model_final_width_mm: float
    flat_model_error_pct: float
    illustrative_only: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def predict_final_width(self, start_width_mm: float, thickness_sequence,
                            roll_diameter_mm: float, kappa: float | None = None) -> dict:
        """Forward-project final width for a proposed thickness sequence.

        `thickness_sequence` is [(entry_h, exit_h), ...] starting from the billet.
        Returns a BAND, never a single number: kappa was measured on the EXISTING
        groove set, and carrying it to an unbuilt caliber is an assumption, not a
        design.
        """
        if isinstance(start_width_mm, bool) or not isinstance(start_width_mm, (int, float)) or start_width_mm <= 0:
            raise ValueError("start_width_mm must be a positive number")
        seq = [tuple(p) for p in thickness_sequence]
        if not seq:
            raise ValueError("thickness_sequence must contain at least one pass")
        if kappa is None and self.kappa_range is None:
            raise ValueError("no kappa available from the fit - cannot project width")
        lo_k, hi_k = (kappa, kappa) if kappa is not None else self.kappa_range

        band = []
        for k in (lo_k, hi_k):
            b = float(start_width_mm)
            for entry_h, exit_h in seq:
                natural_exit = wusatowski_spread(entry_h, exit_h, b, roll_diameter_mm)
                b += (natural_exit - b) * k
            band.append(b)

        return {
            "width_band_mm": (round(min(band), 1), round(max(band), 1)),
            "kappa_band_used": (round(lo_k, 3), round(hi_k, 3)),
            "basis": "kappa measured on the EXISTING groove set of this mill",
            "warning": (
                "This is a BOUND, not a caliber design. A different groove geometry will "
                "have a different kappa. Neither end of this band is an achievable width "
                "until a caliber has actually been designed and reviewed by a qualified "
                "engineer, and it authorises no equipment change."
            ),
            "illustrative_only": self.illustrative_only,
        }


def fit_caliber_model(measurements, roll_diameter_mm: float | None = None) -> CaliberModel:
    items = tuple(measurements)
    if len(items) < 2:
        raise ValueError("need at least two measured passes to characterise a width mechanism")

    diagnoses = tuple(analyse_pass_width(m) for m in items)
    for prev, nxt in zip(items, items[1:]):
        if nxt.pass_index <= prev.pass_index:
            raise ValueError("measurements must be in ascending pass order")

    illustrative = any(m.is_synthetic for m in items)
    warnings: list[str] = []
    if illustrative:
        warnings.append(
            "ILLUSTRATIVE_ONLY - at least one measurement is synthetic. This result "
            "describes the algorithm, not the real mill, and must not be reported as a finding."
        )
    if any(m.temperature_c is None for m in items):
        warnings.append(
            "No temperature recorded on at least one pass. Spread is temperature dependent, "
            "so kappa carries an unquantified temperature confound."
        )

    modes = {d.mode for d in diagnoses}
    if PassMode.EDGING in modes:
        mechanism = WidthMechanism.EDGING_SEQUENCE if modes <= {PassMode.EDGING, PassMode.FREE_SPREAD, PassMode.INDETERMINATE} else WidthMechanism.MIXED
    elif modes & {PassMode.GROOVE_ASSISTED, PassMode.GROOVE_CONSTRAINED}:
        mechanism = WidthMechanism.GROOVED if not (modes - {PassMode.GROOVE_ASSISTED, PassMode.GROOVE_CONSTRAINED, PassMode.FREE_SPREAD, PassMode.INDETERMINATE}) else WidthMechanism.MIXED
    elif modes <= {PassMode.FREE_SPREAD, PassMode.INDETERMINATE}:
        mechanism = WidthMechanism.FLAT_ROLLING if PassMode.FREE_SPREAD in modes else WidthMechanism.UNDETERMINED
    else:
        mechanism = WidthMechanism.MIXED

    kappas = [d.kappa for d in diagnoses if d.kappa is not None and d.mode is not PassMode.GROOVE_CONSTRAINED]
    mean_kappa = sum(kappas) / len(kappas) if kappas else None
    kappa_range = (min(kappas), max(kappas)) if kappas else None

    # What the pure flat-rolling model would have predicted, cascaded from the
    # first measured entry state through the same thickness sequence.
    d = roll_diameter_mm if roll_diameter_mm is not None else items[0].roll_diameter_mm
    b = items[0].entry_width_mm
    for m in items:
        b = wusatowski_spread(m.entry_thickness_mm, m.exit_thickness_mm, b, d)
    flat_final = b
    measured_final = items[-1].exit_width_mm
    error_pct = 100.0 * (flat_final - measured_final) / measured_final

    return CaliberModel(
        mechanism=mechanism,
        pass_diagnoses=diagnoses,
        mean_kappa=mean_kappa,
        kappa_range=kappa_range,
        measured_final_width_mm=measured_final,
        flat_model_final_width_mm=flat_final,
        flat_model_error_pct=error_pct,
        illustrative_only=illustrative,
        warnings=tuple(warnings),
    )


def diagnose_width_mechanism(measurements, roll_diameter_mm: float | None = None) -> dict:
    """Top-level answer to the independent reviewer's question one."""
    model = fit_caliber_model(measurements, roll_diameter_mm)
    verdict = {
        WidthMechanism.FLAT_ROLLING: "Flat rolling with free spread. The existing concept model's deformation mode is correct.",
        WidthMechanism.GROOVED: "Grooved/caliber rolling. The flat-rolling concept model is the WRONG deformation mode and its force, torque and power results must be rebuilt.",
        WidthMechanism.EDGING_SEQUENCE: "Edging or broadside passes are present. Width is manipulated deliberately, not produced by spread.",
        WidthMechanism.MIXED: "Mixed mode - both groove-driven and width-reducing passes are present.",
        WidthMechanism.UNDETERMINED: "Could not be determined from these measurements.",
    }[model.mechanism]
    return {
        "mechanism": model.mechanism.value,
        "verdict": verdict,
        "measured_final_width_mm": model.measured_final_width_mm,
        "flat_model_final_width_mm": round(model.flat_model_final_width_mm, 1),
        "flat_model_error_pct": round(model.flat_model_error_pct, 1),
        "mean_kappa": round(model.mean_kappa, 3) if model.mean_kappa is not None else None,
        "kappa_range": model.kappa_range,
        "per_pass": [
            {"pass": d.pass_index, "mode": d.mode.value,
             "actual_gain_mm": round(d.actual_width_gain_mm, 2),
             "natural_gain_mm": round(d.natural_width_gain_mm, 2),
             "kappa": round(d.kappa, 2) if d.kappa is not None else None,
             "note": d.note}
            for d in model.pass_diagnoses
        ],
        "illustrative_only": model.illustrative_only,
        "warnings": list(model.warnings),
    }


# ---------------------------------------------------------------------------
# ACCEPTANCE TEST
# ---------------------------------------------------------------------------

ACCEPTANCE_TOLERANCE_PCT = 5.0


def acceptance_check(measurements, roll_diameter_mm: float | None = None) -> dict:
    """IC-02's acceptance criterion.

    The instrument passes only if it BOTH reproduces the measured final width
    within tolerance using the fitted kappa, AND correctly identifies that the
    pure flat-rolling model does not. An instrument that cannot tell the two
    apart has no diagnostic value.
    """
    model = fit_caliber_model(measurements, roll_diameter_mm)
    items = tuple(measurements)
    d = roll_diameter_mm if roll_diameter_mm is not None else items[0].roll_diameter_mm

    b = items[0].entry_width_mm
    for m in items:
        natural_exit = wusatowski_spread(m.entry_thickness_mm, m.exit_thickness_mm, b, d)
        natural_gain = natural_exit - b
        k = model.mean_kappa if model.mean_kappa is not None else 1.0
        diag = next(x for x in model.pass_diagnoses if x.pass_index == m.pass_index)
        if diag.mode is PassMode.GROOVE_CONSTRAINED:
            b = b  # groove holds width
        elif diag.mode is PassMode.EDGING:
            b = b + diag.actual_width_gain_mm
        else:
            b = b + natural_gain * k
    fitted_final = b
    measured_final = items[-1].exit_width_mm
    fitted_error = abs(100.0 * (fitted_final - measured_final) / measured_final)
    flat_error = abs(model.flat_model_error_pct)

    reproduces = fitted_error <= ACCEPTANCE_TOLERANCE_PCT
    discriminates = flat_error > ACCEPTANCE_TOLERANCE_PCT
    return {
        "passed": bool(reproduces and discriminates),
        "fitted_model_final_width_mm": round(fitted_final, 1),
        "fitted_model_error_pct": round(fitted_error, 2),
        "flat_model_error_pct": round(flat_error, 2),
        "tolerance_pct": ACCEPTANCE_TOLERANCE_PCT,
        "reproduces_measurement": reproduces,
        "discriminates_against_flat_model": discriminates,
        "illustrative_only": model.illustrative_only,
        "note": (
            "passed=True means the instrument works on this data set. It does NOT mean "
            "the mill is understood, and it authorises no operating or design change."
        ),
    }


# ---------------------------------------------------------------------------
# SYNTHETIC DEMONSTRATION DATA
#
# This exists so the algorithm can be tested and demonstrated BEFORE the real
# mill is instrumented. Every row is stamped SYNTHETIC:, which forces any
# diagnosis built on it to be marked ILLUSTRATIVE_ONLY. It is not data about
# the real mill and must never be quoted as such.
# ---------------------------------------------------------------------------

def synthetic_grooved_run(roll_diameter_mm: float = 518.0) -> tuple[PassMeasurement, ...]:
    """A plausible grooved sequence 150x150 -> 25x250, for algorithm testing only.

    Constructed so that width reaches 250mm, which free spread alone cannot do -
    exactly the situation the real mill presents.
    """
    thicknesses = [150.0, 128.0, 108.0, 90.0, 74.0, 60.0, 47.0, 36.0, 30.0, 25.0]
    widths = [150.0, 168.0, 186.0, 202.0, 216.0, 228.0, 238.0, 245.0, 248.0, 250.0]
    out = []
    for i in range(len(thicknesses) - 1):
        out.append(PassMeasurement(
            pass_index=i + 1,
            entry_thickness_mm=thicknesses[i], exit_thickness_mm=thicknesses[i + 1],
            entry_width_mm=widths[i], exit_width_mm=widths[i + 1],
            roll_diameter_mm=roll_diameter_mm,
            source=f"{SYNTHETIC_PREFIX}illustrative grooved sequence, pass {i + 1}",
            temperature_c=1150.0 - 18.0 * i,
        ))
    return tuple(out)


def synthetic_flat_run(roll_diameter_mm: float = 518.0) -> tuple[PassMeasurement, ...]:
    """A genuinely flat-rolled sequence: widths follow free spread exactly."""
    thicknesses = [150.0, 128.0, 108.0, 90.0, 74.0, 60.0, 47.0, 36.0, 30.0, 25.0]
    out, b = [], 150.0
    for i in range(len(thicknesses) - 1):
        nb = wusatowski_spread(thicknesses[i], thicknesses[i + 1], b, roll_diameter_mm)
        out.append(PassMeasurement(
            pass_index=i + 1,
            entry_thickness_mm=thicknesses[i], exit_thickness_mm=thicknesses[i + 1],
            entry_width_mm=b, exit_width_mm=nb,
            roll_diameter_mm=roll_diameter_mm,
            source=f"{SYNTHETIC_PREFIX}illustrative flat sequence, pass {i + 1}",
            temperature_c=1150.0 - 18.0 * i,
        ))
        b = nb
    return tuple(out)


def synthetic_edging_run(roll_diameter_mm: float = 518.0) -> tuple[PassMeasurement, ...]:
    """A sequence containing a deliberate width-reducing (edging) pass."""
    rows = [
        (150.0, 128.0, 150.0, 166.0),
        (128.0, 108.0, 166.0, 182.0),
        (108.0, 104.0, 182.0, 168.0),   # edging: width deliberately reduced
        (104.0, 88.0, 168.0, 184.0),
    ]
    return tuple(
        PassMeasurement(
            pass_index=i + 1, entry_thickness_mm=r[0], exit_thickness_mm=r[1],
            entry_width_mm=r[2], exit_width_mm=r[3], roll_diameter_mm=roll_diameter_mm,
            source=f"{SYNTHETIC_PREFIX}illustrative edging sequence, pass {i + 1}",
            temperature_c=1150.0 - 18.0 * i,
        )
        for i, r in enumerate(rows)
    )
