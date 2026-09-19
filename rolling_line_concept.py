"""PRJ-STEEL-ROLLING-LINE-01 - concept / pre-engineering calculation model.

SCOPE AND STATUS
================
This module performs CONCEPT DESIGN and PRE-ENGINEERING calculations for an
existing billet-to-flat hot rolling line. Every number it produces is a
computed estimate from a stated model with stated assumptions, NOT a
validated operating setpoint.

Owner (Reza) has authorised concept design and pre-engineering. The remaining
qualified-engineer gates, per the owner's own directive, are:
  - release of fabrication drawings
  - final material selection for critical parts
  - stress / fatigue / structural / foundation sign-off
  - power electrical design and protection sign-off
  - any physical change to the machine
  - binding purchase orders
  - installation, hot commissioning and real production

Nothing in this module clears those gates. Pass schedules produced here are
CONCEPT pass schedules for capability and capacity assessment; they are not
authorised mill practice.

EVIDENCE CLASSES used in field comments: FACT / MEASUREMENT / CLAIM /
ESTIMATE / ASSUMPTION / HYPOTHESIS / UNKNOWN
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

STEEL_DENSITY_KG_MM3 = 7.85e-6  # FACT - carbon steel ~7850 kg/m3


# ---------------------------------------------------------------------------
# Input data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RollScenario:
    """One self-consistent reading of the contradictory roll geometry data."""
    name: str
    barrel_diameter_mm: float
    barrel_length_mm: float
    neck_diameter_mm: float
    evidence: str


# The 518 / 520 / 550 contradiction is preserved, not resolved.
SCENARIO_A = RollScenario(
    name="A (CAD-measured)",
    barrel_diameter_mm=518.0,   # MEASUREMENT - read directly off CAD section D-D, appears 3x
    barrel_length_mm=1280.0,    # CLAIM - engineer verbal, consistent with CAD
    neck_diameter_mm=260.0,     # CLAIM - engineer verbal
    evidence="CAD drawing raffing-rollers-w250-section-cc-dd.pdf shows dia 518 three times",
)
SCENARIO_B = RollScenario(
    name="B (second verbal recollection)",
    barrel_diameter_mm=550.0,   # CLAIM - engineer verbal, second telling
    barrel_length_mm=1350.0,    # CLAIM - engineer verbal, second telling
    neck_diameter_mm=260.0,
    evidence="Engineer verbal recollection, alternative reading. Not reconciled with CAD.",
)


@dataclass(frozen=True)
class Stand:
    stand_id: str
    motor_kw: float | None
    motor_rpm: float | None
    gearbox_ratio: float          # input:output, e.g. 9.8 means 1:9.8 reduction
    roll_diameter_mm: float | None
    evidence: str = ""

    @property
    def roll_rpm(self) -> float | None:
        if self.motor_rpm is None:
            return None
        return self.motor_rpm / self.gearbox_ratio

    @property
    def surface_speed_m_min(self) -> float | None:
        if self.roll_rpm is None or self.roll_diameter_mm is None:
            return None
        return math.pi * (self.roll_diameter_mm / 1000.0) * self.roll_rpm

    @property
    def rated_motor_torque_nm(self) -> float | None:
        if self.motor_kw is None or self.motor_rpm is None:
            return None
        return self.motor_kw * 1000.0 / (self.motor_rpm * 2 * math.pi / 60.0)

    def rated_roll_torque_nm(self, gearbox_efficiency: float = 0.96) -> float | None:
        t = self.rated_motor_torque_nm
        if t is None:
            return None
        return t * self.gearbox_ratio * gearbox_efficiency


@dataclass(frozen=True)
class Billet:
    thickness_mm: float = 150.0   # FACT - engineer stated 150x150
    width_mm: float = 150.0
    length_mm: float = 3150.0     # FACT - engineer stated max ~3m15

    @property
    def area_mm2(self) -> float:
        return self.thickness_mm * self.width_mm

    @property
    def volume_mm3(self) -> float:
        return self.area_mm2 * self.length_mm

    @property
    def mass_kg(self) -> float:
        return self.volume_mm3 * STEEL_DENSITY_KG_MM3


@dataclass(frozen=True)
class Case:
    """Conservative / base / optimistic parameter set."""
    name: str
    friction_coefficient: float      # ASSUMPTION - hot steel on steel, descaled, unlubricated
    entry_temperature_c: float       # ASSUMPTION - no pyrometer data exists
    temperature_drop_per_pass_c: float
    scale_loss_fraction: float
    crop_loss_fraction: float
    cycle_time_s: float              # ESTIMATE - manual/semi-auto three-high handling
    gearbox_efficiency: float

    @property
    def yield_fraction(self) -> float:
        return (1.0 - self.scale_loss_fraction) * (1.0 - self.crop_loss_fraction)


CONSERVATIVE = Case("conservative", 0.25, 1100.0, 22.0, 0.030, 0.050, 140.0, 0.93)
BASE = Case("base", 0.30, 1150.0, 18.0, 0.020, 0.030, 100.0, 0.96)
OPTIMISTIC = Case("optimistic", 0.35, 1200.0, 14.0, 0.012, 0.020, 70.0, 0.97)
CASES = (CONSERVATIVE, BASE, OPTIMISTIC)


# ---------------------------------------------------------------------------
# Physics
# ---------------------------------------------------------------------------

def flow_stress_mpa(temperature_c: float, strain_rate_s: float, strain: float = 0.3) -> float:
    """Hot flow stress of low-carbon steel (ST37 / S235JR class).

    ESTIMATE. Simple exponential-temperature form, calibrated against published
    hot-working data for 0.15-0.20%C steel at strain rate 10/s:
        1200C -> ~65 MPa,  1100C -> ~88 MPa,  1000C -> ~120 MPa,  900C -> ~163 MPa
    Strain-rate sensitivity m=0.13 and strain hardening n=0.15 are literature-
    typical for this class in the austenitic hot-working range.

    This is NOT a calibrated constitutive model for the customer's actual steel.
    A single hot compression test series would replace it with a real one.
    """
    if temperature_c <= 0 or strain_rate_s <= 0 or strain <= 0:
        raise ValueError("temperature, strain rate and strain must be positive")
    a_const = 2586.0
    beta = 0.00307
    m = 0.13
    n = 0.15
    base = a_const * math.exp(-beta * temperature_c)
    return base * (strain_rate_s / 10.0) ** m * (strain / 0.3) ** n


def max_draft_for_bite_mm(friction_coefficient: float, roll_radius_mm: float) -> float:
    """Friction-limited maximum draft: dh_max = mu^2 * R. Standard bite condition."""
    if friction_coefficient <= 0 or roll_radius_mm <= 0:
        raise ValueError("friction and radius must be positive")
    return friction_coefficient ** 2 * roll_radius_mm


def contact_length_mm(roll_radius_mm: float, draft_mm: float) -> float:
    if roll_radius_mm <= 0 or draft_mm < 0:
        raise ValueError("invalid contact-length inputs")
    return math.sqrt(roll_radius_mm * draft_mm)


def wusatowski_spread(entry_h: float, exit_h: float, entry_b: float, roll_diameter_mm: float) -> float:
    """Wusatowski natural-spread model. Returns exit width in mm.

    b1/b0 = (h0/h1)^w,  w = 10^(-1.269 * (b0/h0) * (h0/D)^0.556)

    ESTIMATE. Valid for flat (non-grooved) passes only. If the mill uses
    machined caliber grooves, groove design governs width and this UNDERSTATES
    achievable width - see the note in analyse_width_capability().
    """
    if min(entry_h, exit_h, entry_b, roll_diameter_mm) <= 0:
        raise ValueError("spread inputs must be positive")
    if exit_h > entry_h:
        raise ValueError("exit thickness cannot exceed entry thickness")
    w_exp = 10 ** (-1.269 * (entry_b / entry_h) * (entry_h / roll_diameter_mm) ** 0.556)
    return entry_b * (entry_h / exit_h) ** w_exp


def geometry_factor(contact_len_mm: float, mean_thickness_mm: float, friction: float) -> float:
    """Q_p, the combined friction-hill / redundant-work multiplier on mean flow stress.

    ESTIMATE, piecewise:
      L/h < 1  -> thick-stock regime, inhomogeneous deformation, Q_p rises from 0.8
      L/h >= 1 -> friction-hill regime, Q_p = 1 + mu*L/(2h)
    """
    ratio = contact_len_mm / mean_thickness_mm
    if ratio < 1.0:
        return 0.8 + 0.2 * ratio
    return 1.0 + friction * ratio / 2.0


@dataclass(frozen=True)
class PassResult:
    index: int
    entry_h: float
    exit_h: float
    entry_b: float
    exit_b: float
    draft: float
    contact_len: float
    temperature_c: float
    strain_rate: float
    flow_stress: float
    geometry_q: float
    force_n: float
    torque_nm: float
    power_kw: float
    bite_ok: bool
    bite_angle_deg: float


def analyse_pass(index, entry_h, exit_h, entry_b, scenario, case, roll_surface_speed_m_min, temperature_c):
    r = scenario.barrel_diameter_mm / 2.0
    draft = entry_h - exit_h
    if draft <= 0:
        raise ValueError("pass must reduce thickness")
    lc = contact_length_mm(r, draft)
    exit_b = wusatowski_spread(entry_h, exit_h, entry_b, scenario.barrel_diameter_mm)
    mean_b = (entry_b + exit_b) / 2.0
    mean_h = (entry_h + exit_h) / 2.0
    v_mm_s = roll_surface_speed_m_min * 1000.0 / 60.0
    true_strain = math.log(entry_h / exit_h)
    strain_rate = v_mm_s / lc * true_strain
    kf = flow_stress_mpa(temperature_c, strain_rate, max(true_strain, 0.05))
    q = geometry_factor(lc, mean_h, case.friction_coefficient)
    force_n = q * kf * mean_b * lc          # MPa * mm * mm = N
    moment_arm_mm = 0.5 * lc                # ASSUMPTION lambda=0.5, standard hot rolling
    torque_nm = 2.0 * force_n * moment_arm_mm / 1000.0
    omega = roll_surface_speed_m_min / 60.0 / (r / 1000.0)
    power_kw = torque_nm * omega / 1000.0
    dh_max = max_draft_for_bite_mm(case.friction_coefficient, r)
    cos_alpha = 1.0 - draft / (2.0 * r)
    bite_angle = math.degrees(math.acos(max(-1.0, min(1.0, cos_alpha))))
    return PassResult(index, entry_h, exit_h, entry_b, exit_b, draft, lc, temperature_c,
                      strain_rate, kf, q, force_n, torque_nm, power_kw, draft <= dh_max, bite_angle)


def build_concept_pass_schedule(billet, target_thickness, scenario, case, roll_surface_speed_m_min,
                                max_passes=20, draft_utilisation=0.85):
    """CONCEPT pass schedule - capability/capacity study only, NOT mill practice."""
    r = scenario.barrel_diameter_mm / 2.0
    dh_max = max_draft_for_bite_mm(case.friction_coefficient, r) * draft_utilisation
    passes, h, b, temp = [], billet.thickness_mm, billet.width_mm, case.entry_temperature_c
    idx = 0
    while h > target_thickness + 1e-9 and idx < max_passes:
        idx += 1
        draft = min(dh_max, h - target_thickness, 0.45 * h)
        exit_h = h - draft
        p = analyse_pass(idx, h, exit_h, b, scenario, case, roll_surface_speed_m_min, temp)
        passes.append(p)
        h, b = p.exit_h, p.exit_b
        temp -= case.temperature_drop_per_pass_c
    return passes


# ---------------------------------------------------------------------------
# Mechanical capability checks
# ---------------------------------------------------------------------------

def roll_neck_bending_stress_mpa(force_n, neck_diameter_mm, moment_arm_mm=200.0):
    """Bending stress in the roll neck. ASSUMPTION on moment arm (bearing centre
    to barrel end) - 200mm is typical for this roll size; needs measurement."""
    if neck_diameter_mm <= 0:
        raise ValueError("neck diameter must be positive")
    load = force_n / 2.0
    moment = load * moment_arm_mm
    section_modulus = math.pi * neck_diameter_mm ** 3 / 32.0
    return moment / section_modulus


def roll_barrel_deflection_mm(force_n, scenario, strip_width_mm, youngs_modulus_mpa=200000.0):
    span = scenario.barrel_length_mm + 400.0   # ASSUMPTION bearing span
    d = scenario.barrel_diameter_mm
    inertia = math.pi * d ** 4 / 64.0
    a = (span - strip_width_mm) / 2.0
    return force_n * a * (3 * span ** 2 - 4 * a ** 2) / (48.0 * youngs_modulus_mpa * inertia)


def mass_flow_thickness_chain(stands, exit_thickness_mm, width_mm):
    """Given fixed stand speeds, back-calculate the thickness each stand must
    deliver for continuous (tandem) mass-flow continuity."""
    known = [s for s in stands if s.surface_speed_m_min is not None]
    if not known:
        raise ValueError("no stand has a known speed")
    last = known[-1]
    flow = last.surface_speed_m_min * exit_thickness_mm * width_mm
    out = {}
    for s in known:
        out[s.stand_id] = flow / (s.surface_speed_m_min * width_mm)
    return out


def power_limited_draft_mm(entry_h, entry_b, scenario, case, roll_surface_speed_m_min,
                           temperature_c, power_limit_kw, torque_limit_nm,
                           bite_limit_mm, tol=0.01):
    """Largest draft this pass can take without exceeding motor power OR drive torque.

    The mill is limited by whichever binds first - friction bite, motor power, or
    gearbox/spindle torque. Binary search on draft. Returns 0.0 if even a minimal
    draft exceeds the limits (i.e. the pass is not feasible at this temperature).
    """
    lo, hi = 0.0, min(bite_limit_mm, 0.45 * entry_h, entry_h - 0.5)
    if hi <= 0:
        return 0.0

    def feasible(draft):
        if draft <= 0:
            return True
        p = analyse_pass(0, entry_h, entry_h - draft, entry_b, scenario, case,
                         roll_surface_speed_m_min, temperature_c)
        return p.power_kw <= power_limit_kw and p.torque_nm <= torque_limit_nm

    if feasible(hi):
        return hi
    while hi - lo > tol:
        mid = (lo + hi) / 2.0
        if feasible(mid):
            lo = mid
        else:
            hi = mid
    return lo


def build_constrained_pass_schedule(billet, target_thickness, scenario, case,
                                    roll_surface_speed_m_min, power_limit_kw,
                                    torque_limit_nm, max_passes=40,
                                    draft_utilisation=0.85):
    """CONCEPT pass schedule respecting bite AND drive limits simultaneously.

    Returns (passes, limiting_reason_per_pass). Capability/capacity study only -
    this is NOT authorised mill practice.
    """
    r = scenario.barrel_diameter_mm / 2.0
    bite_cap = max_draft_for_bite_mm(case.friction_coefficient, r) * draft_utilisation
    passes, reasons = [], []
    h, b, temp = billet.thickness_mm, billet.width_mm, case.entry_temperature_c
    idx = 0
    while h > target_thickness + 1e-6 and idx < max_passes:
        idx += 1
        geom_cap = min(bite_cap, h - target_thickness, 0.45 * h)
        drive_cap = power_limited_draft_mm(h, b, scenario, case, roll_surface_speed_m_min,
                                           temp, power_limit_kw, torque_limit_nm, geom_cap)
        draft = min(geom_cap, drive_cap)
        if draft < 0.05:
            reasons.append("STALLED - no feasible draft")
            break
        reasons.append("bite/geometry" if drive_cap >= geom_cap - 1e-6 else "drive power/torque")
        p = analyse_pass(idx, h, h - draft, b, scenario, case, roll_surface_speed_m_min, temp)
        passes.append(p)
        h, b = p.exit_h, p.exit_b
        temp -= case.temperature_drop_per_pass_c
    return passes, reasons


def deformation_energy_kwh_per_tonne(passes, mill_efficiency=0.40):
    """Specific deformation energy. ESTIMATE - 40% overall efficiency assumption
    covers redundant work, friction, drive and idle losses."""
    if not passes:
        raise ValueError("no passes")
    total = 0.0
    for p in passes:
        total += p.flow_stress * 1e6 * math.log(p.entry_h / p.exit_h)   # J/m3
    j_per_kg = total / 7850.0
    return j_per_kg * 1000.0 / 3.6e6 / mill_efficiency


# ---------------------------------------------------------------------------
# Grade-dependent hot deformation resistance
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Grade:
    """Hot flow-stress multiplier relative to ST37/S235JR at the same T and strain rate.

    ESTIMATE. Basis: in the austenitic hot-working range, deformation resistance
    rises mainly with Mn and alloy content; ~6% per 1% Mn is a literature-typical
    slope, with smaller contributions from C and Si. These multipliers must be
    replaced by a hot compression test series before any fabrication decision.
    """
    name: str
    flow_stress_multiplier: float
    nominal_carbon: float
    nominal_manganese: float
    basis: str


ST37 = Grade("ST37 / S235JR", 1.00, 0.17, 0.60, "baseline - the mill's current grade")
ST52 = Grade("ST52 / S355J2", 1.15, 0.20, 1.50,
             "Mn +0.9% over ST37 at ~6%/%Mn => ~+5.4%, plus C and Si; range 1.08-1.25")
A283C = Grade("A283 Gr C", 1.08, 0.24, 0.90, "pressure-vessel carbon, modest Mn increase")
CK45 = Grade("CK45 / 1.1191", 1.25, 0.45, 0.65, "medium carbon, markedly higher hot strength")
GRADES = (ST37, ST52, A283C, CK45)


def analyse_pass_for_grade(index, entry_h, exit_h, entry_b, scenario, case,
                           roll_surface_speed_m_min, temperature_c, grade):
    """Same physics as analyse_pass, scaled by the grade's flow-stress multiplier."""
    p = analyse_pass(index, entry_h, exit_h, entry_b, scenario, case,
                     roll_surface_speed_m_min, temperature_c)
    k = grade.flow_stress_multiplier
    return PassResult(p.index, p.entry_h, p.exit_h, p.entry_b, p.exit_b, p.draft,
                      p.contact_len, p.temperature_c, p.strain_rate,
                      p.flow_stress * k, p.geometry_q, p.force_n * k,
                      p.torque_nm * k, p.power_kw * k, p.bite_ok, p.bite_angle_deg)


def build_grade_pass_schedule(billet, target_thickness, scenario, case,
                              roll_surface_speed_m_min, power_limit_kw,
                              torque_limit_nm, grade, max_passes=60,
                              draft_utilisation=0.85):
    """Concept pass schedule for a specific steel grade, respecting bite and drive limits."""
    r = scenario.barrel_diameter_mm / 2.0
    bite_cap = max_draft_for_bite_mm(case.friction_coefficient, r) * draft_utilisation
    passes, reasons = [], []
    h, b, temp = billet.thickness_mm, billet.width_mm, case.entry_temperature_c
    idx = 0
    while h > target_thickness + 1e-6 and idx < max_passes:
        idx += 1
        geom_cap = min(bite_cap, h - target_thickness, 0.45 * h)

        def feasible(draft):
            if draft <= 0:
                return True
            p = analyse_pass_for_grade(0, h, h - draft, b, scenario, case,
                                       roll_surface_speed_m_min, temp, grade)
            return p.power_kw <= power_limit_kw and p.torque_nm <= torque_limit_nm

        lo, hi = 0.0, geom_cap
        if not feasible(hi):
            while hi - lo > 0.01:
                mid = (lo + hi) / 2.0
                if feasible(mid):
                    lo = mid
                else:
                    hi = mid
            draft = lo
            reason = "drive power/torque"
        else:
            draft = geom_cap
            reason = "bite/geometry"
        if draft < 0.05:
            reasons.append("STALLED")
            break
        reasons.append(reason)
        p = analyse_pass_for_grade(idx, h, h - draft, b, scenario, case,
                                   roll_surface_speed_m_min, temp, grade)
        passes.append(p)
        h, b = p.exit_h, p.exit_b
        temp -= case.temperature_drop_per_pass_c
    return passes, reasons
