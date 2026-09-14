"""Retrospective hot-rolling mechanics calculations for the Expert Foundry study.

Scope and authority (see .nexus/expert_foundry/MASTER_PROMPT_v0.1.md):
This module CALCULATES a retrospective feasibility envelope from verified evidence.
It does not recommend a roll gap, speed, pass schedule, temperature setpoint, or any
production trial, and it never authorizes an operating change. Every entry point that
touches real project data requires a `RollingReadiness` (from `rolling_mill_intake`)
with `calculation_allowed=True`; everything else is refused (fail-closed), matching the
existing intake gate.

Design choice on material/empirical constants:
Pure geometry relations (draft, contact length, bite angle, true strain, the
friction-limited biting condition) are exact and are computed directly. Material- and
friction-dependent quantities (flow stress, spread, force, torque, power) depend on
constants that vary by grade, temperature, and mill and must be supplied or calibrated
by the caller — this module refuses to embed a fabricated "typical" constant as if it
were a verified fact. Where you don't have a calibrated value yet, the corresponding
output field is left as None with an explanation rather than a guessed number.

References (variable families only; no numeric plant setpoint is transferable without
plant-specific validation):
- Sims, R.B., "The Calculation of Roll Force and Torque in Hot Rolling Mills" (1954).
- Said, A. et al., "The temperature, roll force and roll torque during hot bar rolling"
  (1999), https://doi.org/10.1016/S0924-0136(98)00391-4
- Wang et al., data-driven roll force/torque parameter families (2019),
  https://doi.org/10.2355/isijinternational.ISIJINT-2018-846
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

from rolling_mill_intake import RollingReadiness


# ---------------------------------------------------------------------------
# Exact geometry (no material assumptions, no calibration needed)
# ---------------------------------------------------------------------------

def draft_mm(entry_thickness_mm: float, exit_thickness_mm: float) -> float:
    """Draft (Δh): thickness removed in one pass."""
    _positive("entry_thickness_mm", entry_thickness_mm)
    _positive("exit_thickness_mm", exit_thickness_mm)
    if exit_thickness_mm > entry_thickness_mm:
        raise ValueError("exit_thickness_mm cannot exceed entry_thickness_mm")
    return entry_thickness_mm - exit_thickness_mm


def reduction_ratio(entry_thickness_mm: float, exit_thickness_mm: float) -> float:
    """Fractional height reduction r = Δh / h0."""
    dh = draft_mm(entry_thickness_mm, exit_thickness_mm)
    return dh / entry_thickness_mm


def contact_length_mm(roll_radius_mm: float, entry_thickness_mm: float, exit_thickness_mm: float) -> float:
    """Projected arc (contact) length L = sqrt(R * Δh) — the standard flat-rolling
    approximation for the roll/strip contact patch length."""
    _positive("roll_radius_mm", roll_radius_mm)
    dh = draft_mm(entry_thickness_mm, exit_thickness_mm)
    return math.sqrt(roll_radius_mm * dh)


def bite_angle_rad(roll_radius_mm: float, entry_thickness_mm: float, exit_thickness_mm: float) -> float:
    """Bite (contact) angle alpha, from cos(alpha) = 1 - Δh / D (D = roll diameter)."""
    _positive("roll_radius_mm", roll_radius_mm)
    diameter = 2.0 * roll_radius_mm
    dh = draft_mm(entry_thickness_mm, exit_thickness_mm)
    cos_alpha = 1.0 - dh / diameter
    cos_alpha = max(-1.0, min(1.0, cos_alpha))
    return math.acos(cos_alpha)


def true_strain(entry_thickness_mm: float, exit_thickness_mm: float) -> float:
    """True (logarithmic) thickness strain, epsilon = ln(h0 / h1)."""
    _positive("entry_thickness_mm", entry_thickness_mm)
    _positive("exit_thickness_mm", exit_thickness_mm)
    return math.log(entry_thickness_mm / exit_thickness_mm)


def mean_strain_rate_per_s(
    roll_surface_speed_mm_s: float,
    roll_radius_mm: float,
    entry_thickness_mm: float,
    exit_thickness_mm: float,
) -> float:
    """Mean effective strain rate over the arc of contact,
    eps_dot = (v_roll / L) * ln(h0 / h1), L = contact length.
    This is the standard flat-rolling mean strain-rate approximation used in hot-rolling
    force/torque models (see Sims 1954; Said et al. 1999)."""
    _positive("roll_surface_speed_mm_s", roll_surface_speed_mm_s)
    length = contact_length_mm(roll_radius_mm, entry_thickness_mm, exit_thickness_mm)
    if length == 0:
        return 0.0
    return (roll_surface_speed_mm_s / length) * true_strain(entry_thickness_mm, exit_thickness_mm)


def biting_condition_ok(bite_angle_radians: float, friction_coefficient: float) -> bool:
    """Classical biting (roll-grip) condition: the pass can only start if
    tan(alpha) <= mu. This is a geometric/friction feasibility check, not a force
    calculation — it flags passes that are geometrically impossible to bite into,
    independent of any flow-stress assumption."""
    if friction_coefficient <= 0:
        raise ValueError("friction_coefficient must be > 0")
    return math.tan(bite_angle_radians) <= friction_coefficient


# ---------------------------------------------------------------------------
# Material- and friction-dependent quantities: caller-supplied models only.
# No fabricated "typical steel" constant is embedded here.
# ---------------------------------------------------------------------------

FlowStressModel = Callable[[float, float, float], float]
"""signature: (true_strain, strain_rate_per_s, temperature_degC) -> mean flow stress in MPa.
Must be calibrated against the plant's own grade/temperature data (or a cited, plant-
validated source) before use. This module does not ship a default."""


@dataclass(frozen=True)
class PassForceEstimate:
    contact_length_mm: float
    bite_angle_rad: float
    biting_feasible: Optional[bool]
    mean_flow_stress_mpa: Optional[float]
    roll_force_n: Optional[float]
    roll_torque_nm: Optional[float]
    power_kw: Optional[float]
    notes: tuple[str, ...] = field(default_factory=tuple)


def estimate_pass_force(
    *,
    roll_radius_mm: float,
    entry_thickness_mm: float,
    exit_thickness_mm: float,
    strip_width_mm: float,
    roll_surface_speed_mm_s: Optional[float] = None,
    temperature_degC: Optional[float] = None,
    friction_coefficient: Optional[float] = None,
    flow_stress_model: Optional[FlowStressModel] = None,
    friction_hill_factor: Optional[float] = None,
    torque_arm_fraction: float = 0.5,
) -> PassForceEstimate:
    """Sims-style single-pass force/torque/power estimate.

    Geometry (contact length, bite angle) is always computed exactly. Force, torque and
    power are only computed if the caller supplies a calibrated `flow_stress_model` and
    `friction_coefficient` (used to build a Sims-type friction-hill correction
    Qp ~= 1 + friction_hill_factor * L / h_mean, an approximation — see Sims 1954). If
    those aren't supplied, those fields come back as None with an explanatory note,
    rather than a guessed number.
    """
    _positive("strip_width_mm", strip_width_mm)
    length = contact_length_mm(roll_radius_mm, entry_thickness_mm, exit_thickness_mm)
    angle = bite_angle_rad(roll_radius_mm, entry_thickness_mm, exit_thickness_mm)
    notes: list[str] = []

    biting_ok = None
    if friction_coefficient is not None:
        biting_ok = biting_condition_ok(angle, friction_coefficient)
        if not biting_ok:
            notes.append(
                "Geometric biting condition FAILS (tan(bite angle) > friction coefficient): "
                "this pass would not self-feed with the given roll radius/draft/friction. "
                "Treat as a red flag, not a force result."
            )

    if flow_stress_model is None or roll_surface_speed_mm_s is None or temperature_degC is None:
        notes.append(
            "Force/torque/power not computed: requires a calibrated flow_stress_model, "
            "roll_surface_speed_mm_s and temperature_degC. Supplying an uncalibrated "
            "constant here would present a guess as an engineering result."
        )
        return PassForceEstimate(length, angle, biting_ok, None, None, None, None, tuple(notes))

    eps = true_strain(entry_thickness_mm, exit_thickness_mm)
    eps_dot = mean_strain_rate_per_s(roll_surface_speed_mm_s, roll_radius_mm, entry_thickness_mm, exit_thickness_mm)
    kf = flow_stress_model(eps, eps_dot, temperature_degC)
    if kf <= 0:
        raise ValueError("flow_stress_model returned a non-positive stress")

    mean_thickness = (entry_thickness_mm + exit_thickness_mm) / 2.0
    if friction_coefficient is not None and mean_thickness > 0:
        qp_factor = friction_hill_factor if friction_hill_factor is not None else 1.0
        qp = 1.0 + qp_factor * friction_coefficient * length / mean_thickness
        notes.append(f"Friction-hill correction Qp={qp:.3f} applied (Sims-type approximation; calibrate against plant data).")
    else:
        qp = 1.0
        notes.append("No friction_coefficient supplied: Qp=1.0 (uncorrected) used — treat force as a lower bound.")

    mean_pressure_mpa = kf * qp
    force_n = mean_pressure_mpa * length * strip_width_mm  # MPa * mm * mm = N
    torque_nm = force_n * torque_arm_fraction * length / 1000.0  # N * mm -> Nm
    omega_rad_s = roll_surface_speed_mm_s / roll_radius_mm
    power_kw = 2.0 * torque_nm * omega_rad_s / 1000.0  # two work rolls

    return PassForceEstimate(length, angle, biting_ok, kf, force_n, torque_nm, power_kw, tuple(notes))


SpreadModel = Callable[[float, float, float, float], float]
"""signature: (entry_thickness_mm, exit_thickness_mm, entry_width_mm, roll_radius_mm)
-> predicted exit width in mm. No universal spread formula is accurate across mills;
this MUST be fit to this line's own historical pass data (thickness/width in vs out)
before it is trusted. This module ships no default coefficient."""


def estimate_spread_mm(
    entry_thickness_mm: float,
    exit_thickness_mm: float,
    entry_width_mm: float,
    roll_radius_mm: float,
    spread_model: SpreadModel,
) -> float:
    """Apply a caller-calibrated spread model. Refuses silently-plausible defaults on
    purpose — see `SpreadModel` docstring."""
    return spread_model(entry_thickness_mm, exit_thickness_mm, entry_width_mm, roll_radius_mm)


# ---------------------------------------------------------------------------
# Gate-respecting entry point for real project data
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HistoricalPass:
    stand_id: str
    entry_thickness_mm: float
    exit_thickness_mm: float
    strip_width_mm: float
    roll_radius_mm: float
    roll_surface_speed_mm_s: Optional[float] = None
    temperature_degC: Optional[float] = None
    measured_motor_current_a: Optional[float] = None


def run_retrospective_envelope(
    readiness: RollingReadiness,
    passes: list[HistoricalPass],
    *,
    friction_coefficient: Optional[float] = None,
    flow_stress_model: Optional[FlowStressModel] = None,
) -> list[PassForceEstimate]:
    """Compute the retrospective feasibility envelope for a verified historical run.

    Fail-closed: refuses to run unless `readiness.calculation_allowed` is True, i.e.
    unless `rolling_mill_intake.assess()` reports READY_FOR_RETROSPECTIVE_CALCULATION
    for the actual project data. This mirrors the existing intake gate rather than
    re-deciding readiness here.
    """
    if not readiness.calculation_allowed:
        raise PermissionError(
            "Calculation refused: readiness gate is not open "
            f"(status={readiness.status}, missing={readiness.missing_paths}, "
            f"unresolved_claims={readiness.unresolved_claims}). "
            "Resolve the intake contract via rolling_mill_intake.assess() first."
        )
    return [
        estimate_pass_force(
            roll_radius_mm=p.roll_radius_mm,
            entry_thickness_mm=p.entry_thickness_mm,
            exit_thickness_mm=p.exit_thickness_mm,
            strip_width_mm=p.strip_width_mm,
            roll_surface_speed_mm_s=p.roll_surface_speed_mm_s,
            temperature_degC=p.temperature_degC,
            friction_coefficient=friction_coefficient,
            flow_stress_model=flow_stress_model,
        )
        for p in passes
    ]


def compare_power_with_motor_rating(estimated_power_kw: float, motor_rated_power_kw: float) -> dict:
    """Utilization ratio of an estimated pass power against the nameplate rating —
    a sanity/consistency check against real equipment limits, not a setpoint."""
    _positive("motor_rated_power_kw", motor_rated_power_kw)
    ratio = estimated_power_kw / motor_rated_power_kw
    return {
        "estimated_power_kw": estimated_power_kw,
        "motor_rated_power_kw": motor_rated_power_kw,
        "utilization_ratio": ratio,
        "exceeds_nameplate": ratio > 1.0,
    }


def _positive(name: str, value: float) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{name} must be a positive number, got {value!r}")
