"""Preliminary engineering model - 400 mm wide flat from a 125 mm slab, two-high mill.

REFERENCE DATA RULE (owner instruction 2026-09-21):
All earlier project data and calculations are SUPERSEDED and are NOT used here.
This module imports nothing from the earlier billet-line modules. The only
inputs are the ones the owner declared:

    slab 400 x 125 x 3000 mm     furnace 20 t/h      slab exit 1250 C
    product 400 mm wide, 6-30 mm thick
    two-high roughing stand, work roll D 600 mm, barrel 600 mm
    declared maximum line speed 3 m/s

EVIDENCE CLASSES used in the docstrings and in COEFFICIENTS:
  FACT        - given by the owner as a definite input
  ESTIMATE    - derived from literature with a stated anchor
  ASSUMPTION  - engineering default, stated, with the sensitivity shown
  UNKNOWN     - not available; carried as a range or a Hold Point

Nothing here is released for manufacture or purchase. See HOLD_POINTS.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# DECLARED INPUTS  (FACT - owner, 2026-09-21)
# ---------------------------------------------------------------------------
SLAB_WIDTH_MM = 400.0
SLAB_THICKNESS_MM = 125.0
SLAB_LENGTH_MM = 3000.0
PRODUCT_WIDTH_MM = 400.0
FURNACE_RATE_TPH = 20.0
SLAB_EXIT_TEMP_C = 1250.0
ROLL_DIAMETER_MM = 600.0
BARREL_LENGTH_MM = 600.0
MAX_LINE_SPEED_M_S = 3.0
RHO = 7850.0                    # FACT for the mass balance (owner-specified)

THICKNESS_TARGETS_MM = (30.0, 25.0, 20.0, 15.0, 12.0, 10.0, 8.0, 6.0)

# ---------------------------------------------------------------------------
# COEFFICIENTS - every one labelled, every one with its sensitivity shown later
# ---------------------------------------------------------------------------
MU = {"conservative": 0.25, "balanced": 0.30, "aggressive": 0.35}
# ASSUMPTION. Hot steel on steel, descaled, unlubricated rough rolls.
# Literature range for hot flat rolling 0.25-0.40 (Roberts, "Hot Rolling of
# Steel"). The bite condition is tan(alpha_max) = mu, so this single number
# sets the maximum draft and is the most consequential assumption here.

LAMBDA_ARM = 0.48       # ASSUMPTION torque-arm factor for hot flat rolling (0.42-0.50)
MU_BEARING = 0.004      # ASSUMPTION neck bearing friction coefficient
E_STEEL_MPA = 200000.0  # ESTIMATE Young's modulus of a hot-running roll
EMISSIVITY = 0.80       # ASSUMPTION oxidised steel, 0.75-0.85
CP = 700.0              # ASSUMPTION J/kg.K, austenite above 800 C
K_STEEL = 28.0          # ASSUMPTION W/m.K at ~1100 C
SIGMA_SB = 5.670e-8     # FACT Stefan-Boltzmann
T_AMB_K = 303.0         # ASSUMPTION 30 C mill bay
H_CONV = 15.0           # ASSUMPTION W/m2.K forced convection in the bay

NECK_DIAMETER_RATIO = 0.55   # ASSUMPTION d_neck/D for a two-high mill (0.5-0.6)
BEARING_OFFSET_MM = 250.0    # ASSUMPTION bearing centre to barrel end
ROLL_CONTACT_CHILL_C = 8.0   # ASSUMPTION mean stock temperature drop per roll contact

YIELD_FRACTION = 0.96        # ASSUMPTION scale + crop losses

# Flow stress: sigma = A exp(-beta T) (edot/10)^m (eps/0.3)^n
# ESTIMATE. Anchored to published hot-working data for 0.15-0.20 %C steel at
# 10/s: 1200 C -> 65 MPa, 1100 -> 88, 1000 -> 120, 900 -> 163 MPa.
FS_A, FS_BETA, FS_M, FS_N = 2586.0, 0.00307, 0.13, 0.15

GRADES = {
    # name: (flow stress multiplier, basis)
    "S235JR": (1.00, "ESTIMATE - baseline low-carbon, the calibration grade"),
    "S355JR": (1.15, "ESTIMATE - higher C and Mn (EN 10025-2: C 0.24, Mn 1.60 max "
                     "vs C 0.17, Mn 1.40). Multiplier from the ~6 %/%Mn rule of "
                     "thumb for hot flow stress. NOT measured."),
}

HOLD_POINTS = (
    "roll neck diameter, bearing type and dynamic capacity - UNKNOWN, blocks any "
    "force-increase decision and any final stand selection",
    "stand frame (housing) section and screw-down capacity - UNKNOWN, blocks the "
    "maximum permissible roll separating force",
    "whether the stand is reversing or one-way - UNKNOWN, changes the pass "
    "schedule, the drive duty and the roller-table length",
    "existing motor, spindle, coupling and flywheel - UNKNOWN",
    "steel grade - UNKNOWN, carried as S235JR base and S355JR hard case",
    "mill bay length available on each side of the stand - UNKNOWN, and it is the "
    "binding constraint on the thin end of the product range",
)


# ---------------------------------------------------------------------------
# 1. MASS BALANCE
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MassBalance:
    slab_mass_kg: float
    slab_volume_m3: float
    slabs_per_hour: float
    cycle_time_s: float


def mass_balance(rate_tph: float = FURNACE_RATE_TPH) -> MassBalance:
    v = (SLAB_WIDTH_MM / 1000) * (SLAB_THICKNESS_MM / 1000) * (SLAB_LENGTH_MM / 1000)
    m = v * RHO
    per_h = rate_tph * 1000.0 / m
    return MassBalance(m, v, per_h, 3600.0 / per_h)


def product_length_m(thickness_mm: float, width_mm: float = PRODUCT_WIDTH_MM,
                     yield_fraction: float = YIELD_FRACTION) -> float:
    """Volume conservation. Pure geometry - no material assumption."""
    if thickness_mm <= 0 or width_mm <= 0:
        raise ValueError("thickness and width must be positive")
    v = mass_balance().slab_volume_m3 * yield_fraction
    return v / ((thickness_mm / 1000) * (width_mm / 1000))


# ---------------------------------------------------------------------------
# 2. GEOMETRY AND BITE
# ---------------------------------------------------------------------------
def max_draft_bite_mm(mu: float, roll_diameter_mm: float = ROLL_DIAMETER_MM) -> float:
    """Friction-limited draft. dh_max = mu^2 * R, from tan(alpha_max) = mu."""
    if mu <= 0 or roll_diameter_mm <= 0:
        raise ValueError("mu and diameter must be positive")
    return mu ** 2 * (roll_diameter_mm / 2.0)


def max_draft_bite_exact_mm(mu: float, roll_diameter_mm: float = ROLL_DIAMETER_MM) -> float:
    """Exact bite limit: alpha_max = arctan(mu), dh = D (1 - cos alpha_max).

    The classical dh = mu^2 R is the small-angle form of this and OVERSTATES the
    limit by about 4 % at mu = 0.25, 6.7 % at 0.30 and 9.1 % at 0.35. The bite_utilisation
    factor in SCENARIOS (0.80-0.95) already absorbs that, but the two are
    reported separately so the margin is visible rather than accidental.
    """
    if mu <= 0 or roll_diameter_mm <= 0:
        raise ValueError("mu and diameter must be positive")
    alpha = math.atan(mu)
    return roll_diameter_mm * (1.0 - math.cos(alpha))


def bite_angle_deg(draft_mm: float, roll_diameter_mm: float = ROLL_DIAMETER_MM) -> float:
    """cos(alpha) = 1 - dh/D."""
    c = 1.0 - draft_mm / roll_diameter_mm
    if not -1.0 <= c <= 1.0:
        raise ValueError("draft exceeds the roll diameter")
    return math.degrees(math.acos(c))


def contact_length_mm(draft_mm: float, roll_diameter_mm: float = ROLL_DIAMETER_MM) -> float:
    if draft_mm < 0:
        raise ValueError("draft must be non-negative")
    return math.sqrt(roll_diameter_mm / 2.0 * draft_mm)


def roll_rpm(linear_speed_m_s: float, diameter_mm: float = ROLL_DIAMETER_MM) -> float:
    """n = 60 v / (pi D)."""
    if diameter_mm <= 0:
        raise ValueError("diameter must be positive")
    return 60.0 * linear_speed_m_s / (math.pi * diameter_mm / 1000.0)


def wusatowski_exit_width_mm(entry_h: float, exit_h: float, entry_b: float,
                             roll_diameter_mm: float = ROLL_DIAMETER_MM) -> float:
    """Natural spread. b1/b0 = (h0/h1)^w, w = 10^(-1.269 (b0/h0) (h0/D)^0.556).

    ESTIMATE. Wusatowski's empirical fit carries +-10-20 % scatter of its own.
    For a WIDE stock (b0/h0 = 3.2 here) the exponent collapses and spread is
    small - which is the whole advantage of starting from a slab.
    """
    if min(entry_h, exit_h, entry_b, roll_diameter_mm) <= 0:
        raise ValueError("spread inputs must be positive")
    if exit_h > entry_h:
        raise ValueError("exit thickness cannot exceed entry thickness")
    w = 10 ** (-1.269 * (entry_b / entry_h) * (entry_h / roll_diameter_mm) ** 0.556)
    return entry_b * (entry_h / exit_h) ** w


# ---------------------------------------------------------------------------
# 3. FLOW STRESS AND FORCE
# ---------------------------------------------------------------------------
def flow_stress_mpa(temperature_c: float, strain_rate_s: float, strain: float,
                    grade: str = "S235JR") -> float:
    if temperature_c <= 0 or strain_rate_s <= 0 or strain <= 0:
        raise ValueError("temperature, strain rate and strain must be positive")
    if grade not in GRADES:
        raise ValueError(f"unknown grade {grade!r}; known: {sorted(GRADES)}")
    base = FS_A * math.exp(-FS_BETA * temperature_c)
    return (base * (strain_rate_s / 10.0) ** FS_M
            * (strain / 0.3) ** FS_N * GRADES[grade][0])


def geometry_factor(contact_len_mm: float, mean_thickness_mm: float, mu: float) -> float:
    """Q_p, the friction-hill / redundant-work multiplier on mean flow stress.

    ESTIMATE, piecewise:
      L/h < 1  thick-stock regime, inhomogeneous deformation, Q_p from 0.8
      L/h >= 1 friction-hill regime, Q_p = 1 + mu L/(2h)
    """
    ratio = contact_len_mm / mean_thickness_mm
    return 0.8 + 0.2 * ratio if ratio < 1.0 else 1.0 + mu * ratio / 2.0


# ---------------------------------------------------------------------------
# 4. ROLL MECHANICS
# ---------------------------------------------------------------------------
def neck_bending_stress_mpa(force_n: float,
                            neck_diameter_mm: float | None = None,
                            offset_mm: float = BEARING_OFFSET_MM) -> float:
    """sigma = M/Z at the barrel-to-neck fillet, M = (F/2) * offset."""
    d = neck_diameter_mm if neck_diameter_mm else NECK_DIAMETER_RATIO * ROLL_DIAMETER_MM
    if d <= 0:
        raise ValueError("neck diameter must be positive")
    return (force_n / 2.0) * offset_mm / (math.pi * d ** 3 / 32.0)


def barrel_deflection_mm(force_n: float, strip_width_mm: float = PRODUCT_WIDTH_MM,
                         barrel_mm: float = BARREL_LENGTH_MM,
                         diameter_mm: float = ROLL_DIAMETER_MM,
                         offset_mm: float = BEARING_OFFSET_MM) -> float:
    """Two symmetric point loads P = F/2 at distance a from each support.
    delta = P a (3S^2 - 4a^2) / (24 E I). ESTIMATE - ignores neck compliance,
    Hertzian flattening and thermal crown."""
    span = barrel_mm + 2.0 * offset_mm
    a = (span - strip_width_mm) / 2.0
    inertia = math.pi * diameter_mm ** 4 / 64.0
    return (force_n / 2.0) * a * (3 * span ** 2 - 4 * a ** 2) / (24.0 * E_STEEL_MPA * inertia)


def lateral_margin_mm(strip_width_mm: float = PRODUCT_WIDTH_MM,
                      barrel_mm: float = BARREL_LENGTH_MM) -> float:
    return (barrel_mm - strip_width_mm) / 2.0


# ---------------------------------------------------------------------------
# 5. THERMAL
# ---------------------------------------------------------------------------
def cooling_rate_c_per_s(thickness_mm: float, width_mm: float, temperature_c: float,
                         emissivity: float = EMISSIVITY) -> float:
    """Lumped radiative + convective loss rate of a rectangular section."""
    t, b = thickness_mm / 1000.0, width_mm / 1000.0
    area_per_len = 2.0 * (t + b)
    mass_per_len = t * b * RHO
    T = temperature_c + 273.15
    q = emissivity * SIGMA_SB * (T ** 4 - T_AMB_K ** 4) + H_CONV * (T - T_AMB_K)
    return q * area_per_len / (mass_per_len * CP)


def biot_number(thickness_mm: float, width_mm: float, temperature_c: float,
                emissivity: float = EMISSIVITY) -> float:
    t, b = thickness_mm / 1000.0, width_mm / 1000.0
    lc = (t * b) / (2.0 * (t + b))
    T = temperature_c + 273.15
    h_rad = emissivity * SIGMA_SB * (T ** 4 - T_AMB_K ** 4) / max(T - T_AMB_K, 1.0)
    return (h_rad + H_CONV) * lc / K_STEEL


# ---------------------------------------------------------------------------
# 6. PASS SCHEDULE
# ---------------------------------------------------------------------------
PLANE_STRAIN_BHRATIO = 5.0
# When the stock is wide relative to its thickness, lateral flow is suppressed
# and the material yields in PLANE STRAIN. The constrained yield stress is then
# k = 2/sqrt(3) * sigma_uniaxial = 1.1547 sigma. The flow-stress fit above is
# calibrated against uniaxial hot-compression data, so this factor must be
# applied for wide flat rolling. b/h here runs from 3.2 (first pass) to 67
# (6 mm), so all but the first pass are firmly plane strain.
PLANE_STRAIN_FACTOR = 2.0 / math.sqrt(3.0)


def constrained_factor(width_mm: float, thickness_mm: float) -> float:
    """Blend from uniaxial to plane strain across b/h = 1 .. 5. ESTIMATE."""
    r = width_mm / thickness_mm
    if r >= PLANE_STRAIN_BHRATIO:
        return PLANE_STRAIN_FACTOR
    if r <= 1.0:
        return 1.0
    f = (r - 1.0) / (PLANE_STRAIN_BHRATIO - 1.0)
    return 1.0 + f * (PLANE_STRAIN_FACTOR - 1.0)


@dataclass(frozen=True)
class Pass:
    index: int
    direction: str
    entry_h: float
    exit_h: float
    draft: float
    reduction_pct: float
    entry_b: float
    exit_b: float
    entry_temp_c: float
    exit_temp_c: float
    speed_m_s: float
    roll_rpm: float
    contact_len: float
    bite_angle: float
    bite_ok: bool
    strain: float
    strain_rate: float
    flow_stress: float
    geometry_q: float
    constrained: float
    force_n: float
    torque_roll_nm: float
    power_kw: float
    piece_length_m: float
    rolling_time_s: float
    neck_stress_mpa: float
    deflection_mm: float


SCENARIOS = {
    "conservative": dict(mu=0.25, max_reduction=0.18, bite_utilisation=0.80,
                         basis="lowest friction in the literature range, shallow "
                               "draft, 80 % of the bite limit - the schedule that "
                               "still works if the rolls are smooth or the stock "
                               "is over-descaled"),
    "balanced":     dict(mu=0.30, max_reduction=0.25, bite_utilisation=0.90,
                         basis="mid-range friction, conventional hot-mill draft "
                               "limit, 90 % of the bite limit"),
    "aggressive":   dict(mu=0.35, max_reduction=0.32, bite_utilisation=0.95,
                         basis="upper friction, deep draft - only defensible if "
                               "bite, torque and force are all demonstrated"),
}


def pass_speed_m_s(index: int, n_passes: int, v_max: float = MAX_LINE_SPEED_M_S,
                   v_first: float = 0.8) -> float:
    """Speed ramp across the schedule. The declared 3 m/s is a CEILING, not the
    speed of every pass: a thick slab is bitten slowly and the mill accelerates
    as the section thins. ASSUMPTION - linear ramp in the first two thirds."""
    if n_passes <= 1:
        return v_first
    f = min((index - 1) / max(n_passes * 0.7 - 1, 1), 1.0)
    return v_first + f * (v_max - v_first)


def build_schedule(target_thickness_mm: float, scenario: str = "balanced",
                   grade: str = "S235JR", reversing: bool = True,
                   interpass_seconds: float = 8.0,
                   entry_temp_c: float = SLAB_EXIT_TEMP_C,
                   emissivity: float = EMISSIVITY,
                   max_passes: int = 40) -> list[Pass]:
    """Geometry-first schedule: each draft is the smallest of the bite limit,
    the fractional reduction limit and the remaining thickness. Force, torque
    and power are consequences, not inputs."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}; known: {sorted(SCENARIOS)}")
    if target_thickness_mm <= 0 or target_thickness_mm >= SLAB_THICKNESS_MM:
        raise ValueError("target thickness must be between 0 and the slab thickness")
    cfg = SCENARIOS[scenario]
    mu = cfg["mu"]
    bite_cap = max_draft_bite_mm(mu) * cfg["bite_utilisation"]

    # first sweep to learn the pass count, so the speed ramp has a denominator
    def drafts_for():
        h, out = SLAB_THICKNESS_MM, []
        while h > target_thickness_mm + 1e-9 and len(out) < max_passes:
            d = min(bite_cap, h * cfg["max_reduction"], h - target_thickness_mm)
            if d <= 1e-6:
                raise ValueError("schedule cannot converge")
            out.append(d)
            h -= d
        return out

    drafts = drafts_for()
    n = len(drafts)

    passes: list[Pass] = []
    h, b, T = SLAB_THICKNESS_MM, SLAB_WIDTH_MM, entry_temp_c
    vol = mass_balance().slab_volume_m3 * YIELD_FRACTION
    for i, d in enumerate(drafts, start=1):
        h1 = h - d
        b1 = wusatowski_exit_width_mm(h, h1, b)
        v = pass_speed_m_s(i, n)
        rpm = roll_rpm(v)
        Lc = contact_length_mm(d)
        alpha = bite_angle_deg(d)
        eps = math.log(h / h1)
        edot = v * 1000.0 / Lc * eps
        b_mean = (b + b1) / 2.0
        cf = constrained_factor(b_mean, (h + h1) / 2.0)
        sigma = flow_stress_mpa(T, max(edot, 0.01), max(eps, 0.01), grade) * cf
        Q = geometry_factor(Lc, (h + h1) / 2.0, mu)
        F = Q * sigma * b_mean * Lc                                # N
        T_roll = 2.0 * F * LAMBDA_ARM * Lc / 1000.0                # N.m both rolls
        # N.mm -> N.m: the neck radius is in mm, so this MUST be divided by 1000
        # before it is added to T_roll. (Caught by a dimensional check; see
        # test_bearing_torque_is_a_small_fraction_of_rolling_torque.)
        T_bear = MU_BEARING * F * (NECK_DIAMETER_RATIO * ROLL_DIAMETER_MM / 2.0) * 2.0 / 1000.0
        T_total = T_roll + T_bear
        P = T_total * 2 * math.pi * rpm / 60.0 / 1000.0            # kW
        piece_len = vol / ((h1 / 1000.0) * (b1 / 1000.0))
        t_roll = piece_len / v
        # temperature after this pass: roll chill + radiation during roll + interpass
        T_exit = T - ROLL_CONTACT_CHILL_C - cooling_rate_c_per_s(h1, b1, T, emissivity) * t_roll
        passes.append(Pass(
            i, "forward" if (not reversing or i % 2 == 1) else "reverse",
            h, h1, d, 100.0 * d / h, b, b1, T, T_exit, v, rpm, Lc, alpha,
            d <= max_draft_bite_mm(mu), eps, edot, sigma, Q, cf, F, T_total, P,
            piece_len, t_roll, neck_bending_stress_mpa(F), barrel_deflection_mm(F, b1)))
        h, b = h1, b1
        T = T_exit - cooling_rate_c_per_s(h, b, T_exit, emissivity) * interpass_seconds
    return passes


def worst_cases(passes: list[Pass]) -> dict:
    """The worst pass is NOT the same pass for every quantity. That is the point."""
    return {
        "max_force": max(passes, key=lambda p: p.force_n),
        "max_torque": max(passes, key=lambda p: p.torque_roll_nm),
        "max_power": max(passes, key=lambda p: p.power_kw),
        "max_length": max(passes, key=lambda p: p.piece_length_m),
        "max_neck_stress": max(passes, key=lambda p: p.neck_stress_mpa),
        "max_deflection": max(passes, key=lambda p: p.deflection_mm),
        "lowest_temp": min(passes, key=lambda p: p.exit_temp_c),
    }


def cycle_summary(passes: list[Pass], interpass_seconds: float = 8.0,
                  handling_seconds: float = 30.0) -> dict:
    rolling = sum(p.rolling_time_s for p in passes)
    interpass = interpass_seconds * (len(passes) - 1)
    total = rolling + interpass + handling_seconds
    mb = mass_balance()
    return {
        "passes": len(passes),
        "rolling_s": rolling,
        "interpass_s": interpass,
        "handling_s": handling_seconds,
        "cycle_s": total,
        "tph": mb.slab_mass_kg / 1000.0 / (total / 3600.0),
        "furnace_cycle_s": mb.cycle_time_s,
        "mill_is_bottleneck": total > mb.cycle_time_s,
    }


def roller_table_requirement_m(passes: list[Pass], reversing: bool = True) -> dict:
    """On a reversing stand the piece must come fully out and stop before it can
    go back. The table each side must therefore be at least as long as the piece
    leaving that pass, plus a stopping allowance."""
    longest = max(p.piece_length_m for p in passes)
    return {
        "longest_piece_m": longest,
        "table_each_side_m": longest * 1.15 if reversing else longest * 1.15,
        "total_bay_m": (2 * longest * 1.15 + 5.0) if reversing else (longest * 1.15 + 10.0),
        "basis": "15 % allowance for stopping and positioning. ASSUMPTION.",
    }


# ---------------------------------------------------------------------------
# 7. DRIVE TRAIN - gearbox and DC motor
# ---------------------------------------------------------------------------
ETA_GEARBOX = 0.97      # ASSUMPTION per reduction stage
ETA_PINION = 0.98       # ASSUMPTION pinion stand
ETA_SPINDLE = 0.99      # ASSUMPTION universal spindles

# Service-factor build-up for a reversing steel-mill main drive. Kept as named
# terms rather than one opaque number so each can be argued separately.
SERVICE_FACTORS = {
    "application_factor": (1.75, "heavy-shock driven machine, uniform driver "
                                 "(ISO 6336 / AGMA class for a mill main drive). "
                                 "ASSUMPTION - the gearbox maker's own table governs."),
    "reversing_factor":   (1.15, "ASSUMPTION - load reversal fatigues the non-working "
                                 "flank; a unidirectional rating does not apply."),
    "thermal_factor":     (1.00, "ASSUMPTION - assumes forced-circulation oil cooling "
                                 "is provided. If cooling is marginal this rises."),
    "design_margin":      (1.10, "ASSUMPTION - owner's margin for unmeasured duty."),
}
BITE_SHOCK_RANGE = (2.0, 3.0)   # ASSUMPTION multiplier on steady rolling torque
GEARBOX_PEAK_ALLOWANCE = 2.0    # ASSUMPTION catalogue short-duration peak vs rated

STANDARD_RATIOS = (3.15, 3.55, 4.0, 4.5, 5.0, 5.6, 6.3, 7.1, 8.0, 9.0, 10.0,
                   11.2, 12.5, 14.0, 16.0, 18.0, 20.0, 22.4, 25.0)


def total_service_factor() -> float:
    f = 1.0
    for v, _ in SERVICE_FACTORS.values():
        f *= v
    return f


@dataclass(frozen=True)
class TorqueChain:
    peak_rolling_roll_nm: float
    rms_roll_nm: float
    continuous_roll_nm: float
    bite_shock_low_nm: float
    bite_shock_high_nm: float
    gearbox_output_required_nm: float
    gearbox_input_nm: float
    motor_shaft_nm: float
    service_factor: float
    gear_ratio: float


def torque_chain(passes: list[Pass], gear_ratio: float, cycle_seconds: float) -> TorqueChain:
    """Torque reported at four stations: rolls, gearbox output, gearbox input,
    motor shaft. Losses are applied station by station, not lumped."""
    if not passes:
        raise ValueError("no passes")
    if gear_ratio <= 0:
        raise ValueError("gear ratio must be positive")
    loads = [p.torque_roll_nm for p in passes]
    times = [p.rolling_time_s for p in passes]
    loaded = sum(times)
    idle = max(cycle_seconds - loaded, 0.0)
    peak = max(loads)
    cont = sum(loads) / len(loads)
    rms = math.sqrt(sum(t ** 2 * dt for t, dt in zip(loads, times)) / (loaded + idle))
    sf = total_service_factor()
    shock_lo, shock_hi = peak * BITE_SHOCK_RANGE[0], peak * BITE_SHOCK_RANGE[1]
    # The gearbox rating is the governing of a fatigue criterion and a peak criterion
    required = max(rms * sf, shock_hi / GEARBOX_PEAK_ALLOWANCE)
    gb_out = peak / ETA_PINION / ETA_SPINDLE
    gb_in = gb_out / (gear_ratio * ETA_GEARBOX)
    return TorqueChain(peak, rms, cont, shock_lo, shock_hi, required,
                       gb_in, gb_in, sf, gear_ratio)


@dataclass(frozen=True)
class DcMotorOption:
    label: str
    rated_kw: float
    base_rpm: float
    max_rpm: float
    field_weakening: float
    gear_ratio: float
    base_torque_nm: float
    roll_rpm_at_base: float
    roll_speed_at_base_m_s: float
    max_roll_speed_m_s: float
    feasible: bool
    worst_margin_pct: float
    limiting_pass: int
    note: str


def dc_motor_feasibility(passes: list[Pass], rated_kw: float, base_rpm: float,
                         field_weakening: float, gear_ratio: float,
                         overload: float = 2.0) -> tuple[bool, float, int]:
    """A DC motor gives CONSTANT TORQUE below base speed and CONSTANT POWER above.

    For every pass, check that the torque the motor can deliver at that pass's
    motor speed, referred through the train, covers the pass torque.
    """
    w_base = 2 * math.pi * base_rpm / 60.0
    t_base = rated_kw * 1000.0 / w_base
    eta = ETA_GEARBOX * ETA_PINION * ETA_SPINDLE
    worst, worst_i, ok = 1e9, 0, True
    for p in passes:
        n_motor = p.roll_rpm * gear_ratio
        if n_motor > base_rpm * field_weakening * 1.001:
            return False, -100.0, p.index          # cannot reach this speed at all
        t_avail = t_base if n_motor <= base_rpm else t_base * base_rpm / n_motor
        t_needed = p.torque_roll_nm / (gear_ratio * eta)
        margin = (t_avail * overload / t_needed - 1.0) * 100.0
        if margin < worst:
            worst, worst_i = margin, p.index
        if t_avail * overload < t_needed:
            ok = False
    return ok, worst, worst_i


def build_dc_option(label: str, passes: list[Pass], rated_kw: float, base_rpm: float,
                    field_weakening: float, note: str,
                    max_line_speed: float = MAX_LINE_SPEED_M_S) -> DcMotorOption:
    """Ratio is set so the motor's TOP speed delivers the declared line speed."""
    n_roll_max = roll_rpm(max_line_speed)
    ratio_ideal = base_rpm * field_weakening / n_roll_max
    # Snap DOWN, never up: a standard ratio above the ideal would put the
    # declared 3 m/s out of reach at the motor's top speed. Reaching the
    # declared line speed is a requirement; a little spare speed is not a fault.
    feasible_ratios = [r for r in STANDARD_RATIOS if r <= ratio_ideal]
    if not feasible_ratios:
        raise ValueError(
            f"no standard ratio reaches {max_line_speed} m/s with a {base_rpm:.0f} rpm "
            f"motor at {field_weakening:.1f}:1 field weakening (need <= {ratio_ideal:.2f})")
    ratio = max(feasible_ratios)
    ok, margin, idx = dc_motor_feasibility(passes, rated_kw, base_rpm,
                                           field_weakening, ratio)
    w_base = 2 * math.pi * base_rpm / 60.0
    n_roll_base = base_rpm / ratio
    return DcMotorOption(
        label, rated_kw, base_rpm, base_rpm * field_weakening, field_weakening,
        ratio, rated_kw * 1000.0 / w_base, n_roll_base,
        math.pi * ROLL_DIAMETER_MM / 1000.0 * n_roll_base / 60.0,
        math.pi * ROLL_DIAMETER_MM / 1000.0 * (base_rpm * field_weakening / ratio) / 60.0,
        ok, margin, idx, note)


# ---------------------------------------------------------------------------
# 8. THE "SENTER HAM-DOWR" QUESTION
# ---------------------------------------------------------------------------
def pinion_centre_distance_mm(roll_gap_mm: float,
                              diameter_mm: float = ROLL_DIAMETER_MM) -> float:
    """Reading (c): a pinion stand's two output shafts run at the SAME SPEED
    ('ham-dowr') and their centre distance must track the ROLL centre distance,
    which is D + gap."""
    if roll_gap_mm < 0:
        raise ValueError("roll gap must be non-negative")
    return diameter_mm + roll_gap_mm


def spindle_angle_deg(pinion_centres_mm: float, roll_centres_mm: float,
                      spindle_length_mm: float) -> float:
    """Half the centre mismatch is taken by each spindle."""
    if spindle_length_mm <= 0:
        raise ValueError("spindle length must be positive")
    offset = abs(roll_centres_mm - pinion_centres_mm) / 2.0
    return math.degrees(math.atan(offset / spindle_length_mm))


def gearbox_centre_distance_mm(ratio: float, module_mm: float, pinion_teeth: int) -> float:
    """Reading (a): a = m (z1 + z2)/2 for a single external helical stage."""
    if ratio <= 0 or module_mm <= 0 or pinion_teeth <= 0:
        raise ValueError("ratio, module and tooth count must be positive")
    z2 = ratio * pinion_teeth
    return module_mm * (pinion_teeth + z2) / 2.0


# ---------------------------------------------------------------------------
# 9. CORRECTIONS ADDED 2026-09-21 AFTER EXTERNAL REVIEW
# ---------------------------------------------------------------------------
# Three of the review's points were reproduced against the model and confirmed
# as errors in the first issue of this study. They are fixed here rather than
# patched in prose, and each carries a regression test.

MILL_MODULUS_MN_PER_MM = (3.0, 8.0)
# ASSUMPTION - plausible range for a two-high stand of this size. The mill
# modulus is the WHOLE stand: housing stretch, screws and nuts, chock
# clearance, bearing oil film and Hertzian flattening at the roll contact.
# It is measured by closing the rolls on themselves and reading the screw
# position against load - a half-day test. Until it is measured it is UNKNOWN.


def stand_stretch_mm(force_n: float, mill_modulus_mn_per_mm: float) -> float:
    """Total stand deflection under roll separating force. This is the number
    that governs thickness control, NOT the barrel bending."""
    if mill_modulus_mn_per_mm <= 0:
        raise ValueError("mill modulus must be positive")
    return force_n / 1e6 / mill_modulus_mn_per_mm


def roll_centre_distance_mm(exit_thickness_mm: float,
                            diameter_mm: float = ROLL_DIAMETER_MM) -> float:
    """Centre distance of the two work rolls during a pass = D + gap, and the
    gap is that pass's EXIT thickness."""
    if exit_thickness_mm < 0:
        raise ValueError("thickness must be non-negative")
    return diameter_mm + exit_thickness_mm


def roll_centre_range_mm(passes: list[Pass], diameter_mm: float = ROLL_DIAMETER_MM,
                         include_entry: bool = True) -> tuple[float, float]:
    """The FULL range across a schedule, first pass included.

    The first issue of this study tabulated only the finishing gaps (6-30 mm)
    and concluded the spindle angle stayed under 1 degree. The roughing passes,
    where the gap is 80-125 mm, were omitted, and there the angle reaches 1.6-2
    degrees. Caught by external review.
    """
    gaps = [p.exit_h for p in passes]
    if include_entry:
        gaps.append(passes[0].entry_h)
    return diameter_mm + min(gaps), diameter_mm + max(gaps)


def optimal_pinion_centre_mm(passes: list[Pass], diameter_new_mm: float = ROLL_DIAMETER_MM,
                             diameter_worn_mm: float | None = None) -> dict:
    """Minimise the WORST spindle offset across the whole operating range.

    For a symmetric penalty the optimum is the midpoint of the range, because
    the offset is |centre - pinion_centre| and the max of that over an interval
    is minimised at its midpoint.
    """
    lo, hi = roll_centre_range_mm(passes, diameter_new_mm)
    if diameter_worn_mm:
        lo2, hi2 = roll_centre_range_mm(passes, diameter_worn_mm)
        lo, hi = min(lo, lo2), max(hi, hi2)
    mid = (lo + hi) / 2.0
    return {"range_low_mm": lo, "range_high_mm": hi,
            "optimal_centre_mm": mid, "max_offset_mm": (hi - lo) / 2.0}


def inertia_at_motor_kgm2(gear_ratio: float, n_rolls: int = 2,
                          motor_rotor_j: float = 400.0,
                          drivetrain_j: float = 50.0,
                          diameter_mm: float = ROLL_DIAMETER_MM,
                          barrel_mm: float = BARREL_LENGTH_MM,
                          neck_allowance: float = 1.20) -> float:
    """J referred to the motor shaft. motor_rotor_j is an ASSUMPTION for a
    ~1600 kW / 400 rpm DC mill machine (GD^2/4); the nameplate replaces it."""
    r = diameter_mm / 2000.0
    mass = math.pi * r ** 2 * (barrel_mm / 1000.0) * RHO * neck_allowance
    j_roll = 0.5 * mass * r ** 2
    return motor_rotor_j + drivetrain_j + n_rolls * j_roll / gear_ratio ** 2


@dataclass(frozen=True)
class MotorDuty:
    rolling_rms_nm: float
    accel_torque_nm: float
    worst_simultaneous_nm: float
    thermal_rms_nm: float
    base_torque_nm: float
    thermal_utilisation: float
    peak_utilisation: float
    reversals_per_hour: float
    verdict: str


def motor_duty(passes: list[Pass], rated_kw: float, base_rpm: float,
               gear_ratio: float, cycle_seconds: float,
               slabs_per_hour: float, accel_time_s: float = 2.0,
               max_rpm: float | None = None,
               motor_rotor_j: float = 400.0) -> MotorDuty:
    """The check the first issue of this study did NOT do.

    Feasibility was tested pass by pass on torque alone. A reversing mill also
    has to be checked THERMALLY over the whole cycle, and the acceleration of
    the rotating masses has to be counted - at 100-190 reversals an hour it is
    not a rounding error.
    """
    eta = ETA_GEARBOX * ETA_PINION * ETA_SPINDLE
    w_base = 2 * math.pi * base_rpm / 60.0
    t_base = rated_kw * 1000.0 / w_base
    n_max = max_rpm or base_rpm * 3.0

    motor_torques = [p.torque_roll_nm / (gear_ratio * eta) for p in passes]
    times = [p.rolling_time_s for p in passes]

    j = inertia_at_motor_kgm2(gear_ratio, motor_rotor_j=motor_rotor_j)
    alpha = (2 * math.pi * n_max / 60.0) / accel_time_s
    t_acc = j * alpha

    # every pass is preceded by an acceleration and followed by a deceleration
    n_events = 2 * len(passes)
    accel_time_total = n_events * accel_time_s

    sum_sq = sum(t ** 2 * dt for t, dt in zip(motor_torques, times))
    sum_sq += t_acc ** 2 * accel_time_total
    idle = max(cycle_seconds - sum(times) - accel_time_total, 0.0)
    thermal_rms = math.sqrt(sum_sq / (sum(times) + accel_time_total + idle))

    rolling_rms = math.sqrt(sum_sq_r / sum(times)) if (sum_sq_r := sum(
        t ** 2 * dt for t, dt in zip(motor_torques, times))) else 0.0
    worst_sim = max(motor_torques) + t_acc

    util_th = thermal_rms / t_base
    util_pk = worst_sim / t_base
    if util_th > 1.0:
        verdict = "THERMALLY OVERLOADED - the machine will overheat"
    elif util_pk > 2.0:
        verdict = "PEAK EXCEEDS 200 % OVERLOAD - commutation limit likely breached"
    elif util_th > 0.85:
        verdict = "thermally tight - confirm duty class with the maker"
    else:
        verdict = "acceptable on both thermal and peak criteria"
    return MotorDuty(rolling_rms, t_acc, worst_sim, thermal_rms, t_base,
                     util_th, util_pk, slabs_per_hour * n_events, verdict)


# ---------------------------------------------------------------------------
# 10. DRIVE-TRAIN DETAIL FOR THE VENDOR PACKAGE (2026-09-21)
# ---------------------------------------------------------------------------
ETA_COUPLING = 0.995        # ASSUMPTION gear coupling, per coupling
SPINDLE_SPLIT = 0.50        # two spindles, nominally equal share
SPINDLE_SPLIT_IMBALANCE = 0.10
# ASSUMPTION. In a two-high stand the top and bottom rolls do NOT take exactly
# half the torque each: the strip is not symmetric about the pass line, the
# rolls wear differently and the spindle angles differ. A 10 % imbalance is a
# conventional design allowance, so each spindle is rated for 0.55 of the total.


def torque_per_roll_nm(total_torque_nm: float,
                       imbalance: float = SPINDLE_SPLIT_IMBALANCE) -> dict:
    """Split of the total rolling torque between the two rolls/spindles."""
    if total_torque_nm < 0 or not 0.0 <= imbalance < 1.0:
        raise ValueError("invalid torque or imbalance")
    nominal = total_torque_nm * SPINDLE_SPLIT
    return {"nominal_per_roll_nm": nominal,
            "design_per_spindle_nm": nominal * (1.0 + imbalance),
            "imbalance_allowance": imbalance}


def loss_chain(roll_torque_nm: float, gear_ratio: float, stages: int = 2) -> dict:
    """Torque referred back station by station, with each loss shown separately
    rather than lumped into one efficiency."""
    eta_gb = ETA_GEARBOX ** stages
    spindles = roll_torque_nm / ETA_SPINDLE
    pinion_out = spindles / ETA_COUPLING
    pinion_in = pinion_out / ETA_PINION
    gb_out = pinion_in / ETA_COUPLING
    gb_in = gb_out / (gear_ratio * eta_gb)
    motor = gb_in / ETA_COUPLING
    return {
        "at_rolls_nm": roll_torque_nm,
        "after_spindles_nm": spindles,
        "pinion_output_nm": pinion_out,
        "pinion_input_nm": pinion_in,
        "gearbox_output_nm": gb_out,
        "gearbox_input_nm": gb_in,
        "motor_shaft_nm": motor,
        "eta_gearbox_total": eta_gb,
        "eta_overall": roll_torque_nm / (motor * gear_ratio),
        "stages": stages,
    }


def split_ratio(total_ratio: float, stages: int = 2) -> list[tuple[float, ...]]:
    """Candidate stage splits that multiply to the target, snapped to standard
    ratios. For a two-stage box the first stage normally carries the larger
    share so the slow-speed wheel stays small."""
    if stages != 2:
        raise ValueError("only two-stage splits are generated here")
    out = []
    for r1 in STANDARD_RATIOS:
        if not 2.5 <= r1 <= 5.6:
            continue
        r2 = total_ratio / r1
        near = min(STANDARD_RATIOS, key=lambda r: abs(r - r2))
        if abs(near - r2) / r2 < 0.06 and 2.5 <= near <= 5.6:
            out.append((r1, near, r1 * near))
    return out


def reverse_time_s(speed_m_s: float, accel_time_s: float, dwell_s: float = 1.0,
                   max_line_speed: float = MAX_LINE_SPEED_M_S) -> float:
    """Decelerate to zero, dwell for the screw-down move, accelerate the other
    way. Ramp times scale with the fraction of top speed actually used."""
    if accel_time_s <= 0 or speed_m_s < 0:
        raise ValueError("invalid ramp inputs")
    f = speed_m_s / max_line_speed
    return 2.0 * accel_time_s * f + dwell_s


def braking_energy_j(inertia_kgm2: float, motor_rpm: float) -> float:
    """Rotational kinetic energy that must go somewhere on every reversal."""
    w = 2 * math.pi * motor_rpm / 60.0
    return 0.5 * inertia_kgm2 * w ** 2


def braking_power_kw(inertia_kgm2: float, motor_rpm: float, decel_s: float) -> float:
    if decel_s <= 0:
        raise ValueError("deceleration time must be positive")
    return braking_energy_j(inertia_kgm2, motor_rpm) / decel_s / 1000.0


def commutation_overload_limit(motor_rpm: float, base_rpm: float,
                               limit_at_base: float = 2.0,
                               limit_at_3x: float = 1.2) -> float:
    """DC machines cannot hold their base-speed overload factor up into the
    field-weakened range: commutation, not heating, is the ceiling there.

    ASSUMPTION - a linear fall from `limit_at_base` at n_base to `limit_at_3x`
    at 3x base. The real envelope is a vendor curve and must replace this.
    """
    if base_rpm <= 0:
        raise ValueError("base speed must be positive")
    if motor_rpm <= base_rpm:
        return limit_at_base
    f = min((motor_rpm / base_rpm - 1.0) / 2.0, 1.0)
    return limit_at_base + f * (limit_at_3x - limit_at_base)


def commutation_check(passes: list[Pass], rated_kw: float, base_rpm: float,
                      gear_ratio: float, accel_torque_nm: float) -> dict:
    """Check every pass against the speed-dependent overload envelope, not
    against a flat 200 %."""
    eta = ETA_GEARBOX ** 2 * ETA_PINION * ETA_SPINDLE * ETA_COUPLING ** 2
    t_base = rated_kw * 1000.0 / (2 * math.pi * base_rpm / 60.0)
    worst, worst_pass, ok = 0.0, 0, True
    for p in passes:
        n_motor = p.roll_rpm * gear_ratio
        t_needed = p.torque_roll_nm / (gear_ratio * eta)
        t_avail_cont = t_base if n_motor <= base_rpm else t_base * base_rpm / n_motor
        allowed = t_avail_cont * commutation_overload_limit(n_motor, base_rpm)
        util = t_needed / allowed
        if util > worst:
            worst, worst_pass = util, p.index
        if util > 1.0:
            ok = False
    # the reversal itself happens at top speed, where the envelope is tightest
    n_top = max(p.roll_rpm for p in passes) * gear_ratio
    t_cont_top = t_base * base_rpm / n_top if n_top > base_rpm else t_base
    accel_util = accel_torque_nm / (t_cont_top * commutation_overload_limit(n_top, base_rpm))
    return {"worst_rolling_utilisation": worst, "worst_pass": worst_pass,
            "reversal_utilisation": accel_util,
            "rolling_ok": ok, "reversal_ok": accel_util <= 1.0,
            "envelope_at_top_speed": commutation_overload_limit(n_top, base_rpm)}


# ---------------------------------------------------------------------------
# 11. TRACEABILITY AND UNIT DISCIPLINE (added 2026-09-21 after owner review)
# ---------------------------------------------------------------------------
def braking_per_stop(inertia_kgm2: float, motor_rpm: float, decel_s: float) -> dict:
    """ENERGY and POWER reported separately and in their own units.

    A previous issue of this package wrote "each reversal returns 284-945 kW of
    energy". kW is power, not energy. The two are reported here as distinct
    quantities with distinct units, plus the hourly AVERAGE power, which is a
    third quantity again.
    """
    e_j = braking_energy_j(inertia_kgm2, motor_rpm)
    return {
        "energy_per_stop_mj": e_j / 1e6,
        "energy_per_stop_kwh": e_j / 3.6e6,
        "instantaneous_power_kw": e_j / decel_s / 1000.0,
        "decel_s": decel_s,
    }


def braking_hourly_average_kw(inertia_kgm2: float, motor_rpm: float,
                              reversals_per_hour: float) -> float:
    """Average regenerated power over an hour - a different number again from
    the instantaneous peak, and the one the substation sees as a load."""
    if reversals_per_hour < 0:
        raise ValueError("reversals per hour must be non-negative")
    return braking_energy_j(inertia_kgm2, motor_rpm) * reversals_per_hour / 3.6e6


def reversals_per_slab(passes: list[Pass]) -> int:
    """One reversal between consecutive passes. NOT a single number shared by
    every thickness - it runs 5 at 30 mm to 10 at 6 mm."""
    return max(len(passes) - 1, 0)


def gearbox_rating_trace(passes: list[Pass], gear_ratio: float,
                         cycle_seconds: float,
                         peak_allowance: float = GEARBOX_PEAK_ALLOWANCE,
                         headroom: float = 1.23) -> dict:
    """Every gearbox number traced back to the computed rolling torque.

    Returns each step so the reader can see which figure is a REQUIREMENT
    (derived from a computed load plus a stated factor), which is a
    RECOMMENDATION (a requirement plus headroom) and which is an EXPANSION
    OPTION (priced separately, not needed for phase one).
    """
    ch = torque_chain(passes, gear_ratio, cycle_seconds)
    crit_a = ch.rms_roll_nm * ch.service_factor
    crit_b = ch.bite_shock_high_nm / peak_allowance
    governing = max(crit_a, crit_b)
    return {
        "computed_peak_roll_nm": ch.peak_rolling_roll_nm,
        "at_gearbox_output_nm": ch.peak_rolling_roll_nm / (
            ETA_SPINDLE * ETA_COUPLING * ETA_PINION * ETA_COUPLING),
        "rms_roll_nm": ch.rms_roll_nm,
        "service_factor": ch.service_factor,
        "criterion_a_fatigue_nm": crit_a,
        "bite_shock_2x_nm": ch.bite_shock_low_nm,
        "bite_shock_3x_nm": ch.bite_shock_high_nm,
        "criterion_b_peak_nm": crit_b,
        "governing_criterion": "B (bite shock)" if crit_b > crit_a else "A (fatigue)",
        "rated_requirement_nm": governing,
        "rated_recommendation_nm": governing * headroom,
        "guaranteed_peak_requirement_nm": ch.bite_shock_high_nm,
        "expansion_option_peak_nm": ch.bite_shock_high_nm * headroom,
        "headroom_factor": headroom,
    }


def motor_at_operating_point(pass_: Pass, rated_kw: float, base_rpm: float,
                             gear_ratio: float, eta_overall: float = 0.899) -> dict:
    """Is this motor adequate at THIS pass on its continuous rating, or only
    with short-time overload? The package must state which."""
    n_motor = pass_.roll_rpm * gear_ratio
    w_base = 2 * math.pi * base_rpm / 60.0
    t_base = rated_kw * 1000.0 / w_base
    t_continuous = t_base if n_motor <= base_rpm else t_base * base_rpm / n_motor
    t_needed = pass_.torque_roll_nm / gear_ratio / eta_overall
    envelope = commutation_overload_limit(n_motor, base_rpm)
    return {
        "motor_rpm": n_motor,
        "roll_power_kw": pass_.power_kw,
        "motor_shaft_power_kw": pass_.power_kw / eta_overall,
        "torque_needed_nm": t_needed,
        "torque_continuous_nm": t_continuous,
        "fraction_of_continuous": t_needed / t_continuous,
        "commutation_envelope": envelope,
        "fraction_of_envelope": t_needed / (t_continuous * envelope),
        "needs_overload": t_needed > t_continuous,
        "duration_s": pass_.rolling_time_s,
    }
