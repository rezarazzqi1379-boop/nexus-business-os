"""Drive-train sizing for PRJ-STEEL-ROLLING-LINE-01 - parametric, chain-derived.

THE RULE THIS MODULE EXISTS TO ENFORCE
======================================
No gear ratio and no motor power is proposed by analogy with another mill.
Every number here starts at the ROLLING PROCESS REQUIREMENT and is carried
forward:

    capacity + thermal budget  ->  required linear speed
    linear speed + diameter    ->  roll rpm
    roll rpm + motor rpm       ->  gear ratio
    pass force + contact arc   ->  rolling torque
    rolling torque + losses + acceleration + shock -> drive torque
    duty cycle                 ->  RMS torque
    RMS + service factors      ->  gearbox rated torque
    torque x speed + losses    ->  motor power

STATUS: ESTIMATE / PRELIMINARY CONCEPT. Every coefficient below is labelled.
Nothing here is released for purchase. See RELEASE_BLOCKERS at the bottom.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from rolling_line_concept import (
    flow_stress_mpa, max_draft_for_bite_mm, contact_length_mm, geometry_factor,
    roll_neck_bending_stress_mpa, roll_barrel_deflection_mm, RollScenario,
)
from thermal_and_route_model import Section, billet_section, cool_transit, RHO

# ---------------------------------------------------------------------------
# COEFFICIENTS - every one labelled with its evidence class and what would
# replace it with a real number.
# ---------------------------------------------------------------------------
MU_BITE = 0.30              # ASSUMPTION hot steel on steel, descaled, unlubricated
LAMBDA_ARM = 0.50           # ASSUMPTION torque-arm fraction of contact length (flat pass)
MU_BEARING = 0.004          # ASSUMPTION oil-film/roller neck bearing friction coefficient
ETA_GEARBOX = 0.97          # ASSUMPTION single reduction stage, 0.97 per stage
ETA_PINION = 0.98           # ASSUMPTION pinion stand
ETA_MOTOR = 0.95            # ASSUMPTION large induction machine at rated load

# Service-factor build-up for a REVERSING STEEL MILL MAIN DRIVE.
# Each term is separate and justified, rather than one opaque "SF = 2".
SERVICE_FACTORS = {
    "application_factor":  (1.75, "ISO 6336 / AGMA class: steel mill main drive, "
                                  "uniform driver, heavy shock driven machine. "
                                  "ASSUMPTION - needs the gearbox maker's own table."),
    "reversing_factor":    (1.15, "ASSUMPTION - load reversal fatigues the non-working "
                                  "tooth flank; a unidirectional rating does not apply."),
    "bite_shock_factor":   (1.00, "Counted separately as peak torque, NOT doubled here."),
    "thermal_factor":      (1.00, "ASSUMPTION - assumes adequate cooling is provided. "
                                  "If cooling is marginal this rises and the gearbox "
                                  "must be de-rated."),
    "design_margin":       (1.10, "ASSUMPTION - owner's margin for unmeasured duty."),
}
BITE_SHOCK_MULTIPLIER = (2.0, 3.0)   # ASSUMPTION range - impact at entry vs steady torque
BREAKAWAY_MULTIPLIER = 1.8           # ASSUMPTION - static breakaway vs rated

# Mechanical speed ceilings
PERIPHERAL_SPEED_MAX = {             # m/s, ASSUMPTION by stand duty
    "roughing": 4.0, "intermediate": 6.0, "finishing": 8.0,
}
GEARBOX_INPUT_RPM_MAX = 1500.0       # ASSUMPTION - typical mill gearbox input limit

# Standard gear ratios that are actually manufacturable (R20-ish series).
STANDARD_RATIOS = (4.0, 4.5, 5.0, 5.6, 6.3, 7.1, 8.0, 9.0, 9.8, 10.0, 11.2,
                   12.5, 14.0, 16.0, 18.0, 20.0, 22.4, 25.0, 28.0, 31.5, 35.5)

ROLL_WEAR_FRACTION = 0.92            # ASSUMPTION - min working dia / new dia after regrinds


@dataclass(frozen=True)
class Product:
    width_mm: float
    thickness_mm: float

    @property
    def area_mm2(self) -> float:
        return self.width_mm * self.thickness_mm

    def __str__(self) -> str:
        return f"{self.width_mm:.0f}x{self.thickness_mm:.0f}"


@dataclass(frozen=True)
class Pass:
    index: int
    entry_h: float
    exit_h: float
    width: float
    temperature_c: float
    draft: float
    contact_len: float
    strain: float
    strain_rate: float
    flow_stress: float
    geometry_q: float
    force_n: float
    torque_roll_nm: float          # useful rolling torque, both rolls
    torque_bearing_nm: float
    torque_drive_nm: float         # at the roll shaft, incl. bearing loss
    power_kw: float
    bite_ok: bool
    roll_rpm: float
    piece_length_m: float
    rolling_time_s: float


# ---------------------------------------------------------------------------
# 1. PASS SCHEDULE - geometry first
# ---------------------------------------------------------------------------
DECLARED_PROFILE = ((0.00, 1200.0), (0.50, 1050.0), (0.85, 950.0), (1.00, 800.0))


def temperature_at_fraction(frac: float, profile=DECLARED_PROFILE) -> float:
    """Interpolate the engineer's DECLARED profile across the pass sequence.
    CLAIM-grade input: these are targets, not pyrometer readings."""
    pts = list(profile)
    if frac <= pts[0][0]:
        return pts[0][1]
    for (f0, t0), (f1, t1) in zip(pts, pts[1:]):
        if frac <= f1:
            return t0 + (t1 - t0) * (frac - f0) / (f1 - f0)
    return pts[-1][1]


def width_at_fraction(frac: float, b0: float, b_target: float,
                      width_done_at: float = 0.60) -> float:
    """ASSUMPTION, and a load-bearing one.

    The mill demonstrably produces 250 mm from a 150 mm billet - a width ratio
    of 1.67 - while free spread caps at 1.24. Width therefore comes from a
    mechanism we have NOT measured (`groove_geometry` is an open unknown).
    This function assumes that mechanism delivers the target width smoothly
    over the first `width_done_at` of the schedule, in log space.

    If the real mechanism cannot reach the target ratio, every force number
    downstream of this is wrong. That is stated, not hidden.
    """
    if b_target <= b0:
        return b_target
    x = min(frac / width_done_at, 1.0)
    return b0 * (b_target / b0) ** x


def build_schedule(product: Product, roll_diameter_mm: float,
                   linear_speed_m_s: float, billet_t=150.0, billet_b=150.0,
                   billet_len_mm=3150.0, max_reduction_fraction=0.30,
                   mu=MU_BITE) -> list[Pass]:
    """Thickness schedule limited by the friction bite condition. Geometry only -
    no material constant enters until the force is computed."""
    R = roll_diameter_mm / 2.0
    bite_max = max_draft_for_bite_mm(mu, R)
    volume_m3 = (billet_t / 1000) * (billet_b / 1000) * (billet_len_mm / 1000)

    # first pass: how many passes does the geometry need?
    h, drafts = billet_t, []
    while h > product.thickness_mm + 1e-9:
        d = min(bite_max, h * max_reduction_fraction, h - product.thickness_mm)
        if d <= 1e-6:
            raise ValueError("pass schedule cannot converge")
        drafts.append(d)
        h -= d
        if len(drafts) > 60:
            raise ValueError("pass schedule did not converge in 60 passes")
    n = len(drafts)

    passes, h = [], billet_t
    rpm = 60.0 * linear_speed_m_s / (math.pi * roll_diameter_mm / 1000.0)
    for i, d in enumerate(drafts, start=1):
        frac = i / n
        h1 = h - d
        b = width_at_fraction(frac, billet_b, product.width_mm)
        T = temperature_at_fraction(frac)
        Lc = contact_length_mm(R, d)
        eps = math.log(h / h1)
        edot = linear_speed_m_s * 1000.0 / Lc * eps
        sigma = flow_stress_mpa(T, max(edot, 0.01), max(eps, 0.01))
        Q = geometry_factor(Lc, (h + h1) / 2.0, mu)
        F = Q * sigma * b * Lc                                  # N
        T_roll = 2.0 * F * LAMBDA_ARM * Lc / 1000.0             # N.m, both rolls
        # neck bearing friction, both necks of both rolls
        T_bear = MU_BEARING * F * (0.260 / 2.0) * 2.0           # N.m  (neck dia 260 mm)
        T_drive = T_roll + T_bear
        P = T_drive * 2 * math.pi * rpm / 60.0 / 1000.0
        piece_len = volume_m3 / ((h1 / 1000.0) * (b / 1000.0))
        passes.append(Pass(i, h, h1, b, T, d, Lc, eps, edot, sigma, Q, F,
                           T_roll, T_bear, T_drive, P, d <= bite_max, rpm,
                           piece_len, piece_len / linear_speed_m_s))
        h = h1
    return passes


# ---------------------------------------------------------------------------
# 2. SPEED ENVELOPE - the heart of the study
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SpeedEnvelope:
    product: str
    v_capacity_min: float      # to hit the target tonnage
    v_thermal_min: float       # to finish before the steel is too cold
    v_mech_max: float          # peripheral speed / gearbox input limit
    v_process_max: float       # strain rate, guiding, stopping a long bar
    v_recommended: float
    feasible: bool
    binding_low: str
    binding_high: str
    note: str


def capacity_limited_speed(product: Product, n_passes: int, piece_mass_kg: float,
                           target_t_per_h: float, handling_s_per_pass: float,
                           mean_piece_len_m: float) -> float:
    """Instantaneous rolling speed needed so that the BATCH cycle delivers the
    target tonnage. This is a floor, not a design point."""
    cycle_budget_s = piece_mass_kg / 1000.0 / (target_t_per_h / 3600.0)
    rolling_budget = cycle_budget_s - n_passes * handling_s_per_pass
    if rolling_budget <= 0:
        return float("inf")
    return n_passes * mean_piece_len_m / rolling_budget


def thermal_limited_speed(product: Product, passes: list[Pass],
                          t_start_c: float, t_floor_c: float,
                          handling_s_per_pass: float, volume_m3: float,
                          finishing_fraction: float = 0.40) -> tuple[float, float]:
    """Minimum speed so the FINISHING group completes above t_floor.

    Returns (v_min, available_budget_s). The budget is computed on the actual
    finishing section, which is what makes thin product hard: surface-to-mass
    ratio rises ~10x from billet to 8 mm.
    """
    fin = passes[int(len(passes) * (1 - finishing_fraction)):]
    if not fin:
        return 0.0, float("inf")
    sec = Section(product.thickness_mm, product.width_mm, volume_m3)
    T, t = t_start_c, 0.0
    while T > t_floor_c and t < 3000:
        r = cool_transit(sec, T, 1.0, 1.0, dt=0.05)
        T -= r["mean_drop_c"] / r["transit_s"]
        t += 1.0
    budget = t
    rolling_budget = budget - len(fin) * handling_s_per_pass
    if rolling_budget <= 0:
        return float("inf"), budget
    total_len = sum(p.piece_length_m for p in fin)
    return total_len / rolling_budget, budget


def mechanical_speed_ceiling(roll_diameter_mm: float, duty: str,
                             motor_rpm_max: float, gear_ratio: float) -> float:
    v_peripheral = PERIPHERAL_SPEED_MAX[duty]
    n_roll_max = motor_rpm_max / gear_ratio
    v_from_drive = math.pi * roll_diameter_mm / 1000.0 * n_roll_max / 60.0
    return min(v_peripheral, v_from_drive)


def process_speed_ceiling(product: Product, piece_length_m: float,
                          bay_length_m: float = 21.0, decel_m_s2: float = 1.0,
                          reversing: bool = True) -> tuple[float, str]:
    """Upper bound on speed from things other than the drive.

    Two mechanisms, both of which tighten as the bar gets longer and thinner:

    1. RUN-OUT. On a reversing pass the piece must come fully out of the stand
       and stop before it reverses. The run-out available is the bay length
       minus the piece length. v_max = sqrt(2 a s). When the piece is longer
       than the bay there is no run-out at all and reversing is geometrically
       impossible - reported as such rather than as a small number.
    2. SLENDERNESS. A long thin bar buckles, skews and snakes into the guides.
       Cap falls with length/thickness. ASSUMPTION-grade, parametrised.
    """
    if not reversing:
        return 12.0, "continuous line - no reversal constraint"
    run_out = bay_length_m - piece_length_m
    if run_out <= 0.0:
        return 0.0, (f"REVERSING GEOMETRICALLY IMPOSSIBLE: piece is {piece_length_m:.1f} m "
                     f"in a {bay_length_m:.0f} m bay")
    v_runout = math.sqrt(2.0 * decel_m_s2 * run_out)
    slenderness = piece_length_m * 1000.0 / product.thickness_mm
    v_slender = 12.0 if slenderness < 1000 else max(1.0, 12.0 * 1000.0 / slenderness)
    if v_slender <= v_runout:
        return v_slender, f"slenderness {slenderness:.0f}:1 - guiding and buckling of a long thin bar"
    return v_runout, f"run-out only {run_out:.1f} m before reversal must begin"


# ---------------------------------------------------------------------------
# 3. KINEMATICS AND GEAR RATIO
# ---------------------------------------------------------------------------
def roll_rpm(linear_speed_m_s: float, diameter_mm: float) -> float:
    """n = 60 v / (pi D)."""
    if diameter_mm <= 0:
        raise ValueError("diameter must be positive")
    return 60.0 * linear_speed_m_s / (math.pi * diameter_mm / 1000.0)


def worn_diameter(new_diameter_mm: float, fraction=ROLL_WEAR_FRACTION) -> float:
    return new_diameter_mm * fraction


@dataclass(frozen=True)
class GearOption:
    label: str
    ratio: float
    standard_ratio: float
    roll_rpm_at_motor_base: float
    linear_speed_m_s: float
    output_torque_capacity_nm: float
    note: str


def gear_options(motor_rpm_base: float, motor_kw: float, target_roll_rpm: float,
                 diameter_mm: float) -> list[GearOption]:
    """Three ratios - torque-biased, balanced, speed-biased - snapped onto
    manufacturable standard ratios, then evaluated for what they actually give."""
    ideal = motor_rpm_base / target_roll_rpm
    out = []
    for label, mult, note in (
        ("torque-biased", 1.25, "higher reduction: more output torque, lower top speed"),
        ("balanced", 1.00, "ratio that meets the target speed exactly"),
        ("speed-biased", 0.80, "lower reduction: more speed headroom, less torque"),
    ):
        want = ideal * mult
        std = min(STANDARD_RATIOS, key=lambda r: abs(r - want))
        n_roll = motor_rpm_base / std
        v = math.pi * diameter_mm / 1000.0 * n_roll / 60.0
        t_out = motor_kw * 1000.0 / (2 * math.pi * motor_rpm_base / 60.0) * std * ETA_GEARBOX
        out.append(GearOption(label, want, std, n_roll, v, t_out, note))
    return out


# ---------------------------------------------------------------------------
# 4. TORQUE CHAIN AND DUTY CYCLE
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TorqueChain:
    continuous_nm: float          # mean of the loaded passes
    rms_nm: float                 # over the WHOLE cycle, idle included
    peak_rolling_nm: float
    bite_shock_low_nm: float
    bite_shock_high_nm: float
    breakaway_nm: float
    acceleration_nm: float
    emergency_nm: float
    gearbox_output_required_nm: float
    service_factor_total: float
    motor_shaft_peak_nm: float
    gear_ratio: float


def inertia_referred_to_motor(diameter_mm: float, barrel_len_mm: float,
                              n_rolls: int, gear_ratio: float,
                              motor_rotor_j: float = 60.0) -> float:
    """J_total at the motor shaft. motor_rotor_j is an ASSUMPTION (kg.m2) for a
    ~1250 kW / 1000 rpm machine - the nameplate GD^2 would replace it."""
    r = diameter_mm / 2000.0
    mass = math.pi * r ** 2 * (barrel_len_mm / 1000.0) * RHO
    j_roll = 0.5 * mass * r ** 2
    return motor_rotor_j + n_rolls * j_roll / gear_ratio ** 2


def torque_chain(passes: list[Pass], gear_ratio: float, cycle_time_s: float,
                 diameter_mm: float, barrel_len_mm: float, n_rolls: int = 2,
                 accel_time_s: float = 1.5, motor_rpm: float = 999.0,
                 motor_rotor_j: float = 60.0) -> TorqueChain:
    """Full torque chain at the ROLL SHAFT, plus the referred motor-shaft peak."""
    if not passes:
        raise ValueError("no passes")
    loaded = [p.torque_drive_nm for p in passes]
    times = [p.rolling_time_s for p in passes]
    total_loaded = sum(times)
    idle = max(cycle_time_s - total_loaded, 0.0)

    continuous = sum(loaded) / len(loaded)
    # RMS over the whole cycle: loaded segments contribute T^2*t, idle contributes 0
    rms = math.sqrt(sum(t ** 2 * dt for t, dt in zip(loaded, times))
                    / (total_loaded + idle))
    peak = max(loaded)

    j = inertia_referred_to_motor(diameter_mm, barrel_len_mm, n_rolls, gear_ratio,
                                  motor_rotor_j)
    alpha = (2 * math.pi * motor_rpm / 60.0) / max(accel_time_s, 1e-6)
    t_acc_motor = j * alpha
    t_acc_roll = t_acc_motor * gear_ratio * ETA_GEARBOX

    sf = 1.0
    for _, (v, _n) in SERVICE_FACTORS.items():
        sf *= v
    shock_lo = peak * BITE_SHOCK_MULTIPLIER[0]
    shock_hi = peak * BITE_SHOCK_MULTIPLIER[1]
    breakaway = continuous * BREAKAWAY_MULTIPLIER
    emergency = max(shock_hi, peak + t_acc_roll)

    # Gearbox rating: the governing of (RMS x SF) and (peak with its own allowance).
    # A gearbox catalogue peak allowance is typically 2x rated for short duration.
    required = max(rms * sf, shock_hi / 2.0)

    return TorqueChain(continuous, rms, peak, shock_lo, shock_hi, breakaway,
                       t_acc_roll, emergency, required, sf,
                       (peak + t_acc_roll) / (gear_ratio * ETA_GEARBOX), gear_ratio)


# ---------------------------------------------------------------------------
# 5. MOTOR SIZING AND THE ELECTRICAL CONSISTENCY CHECK
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MotorSizing:
    deformation_kw: float
    losses_kw: float
    rms_kw: float
    peak_kw: float
    recommended_rated_kw: float
    base_rpm: float
    peak_torque_nm: float
    note: str


def motor_sizing(chain: TorqueChain, motor_rpm: float,
                 overload_capability: float = 2.0) -> MotorSizing:
    w = 2 * math.pi * motor_rpm / 60.0
    p_rms = chain.rms_nm / (chain.gear_ratio * ETA_GEARBOX) * w / 1000.0
    p_peak = chain.motor_shaft_peak_nm * w / 1000.0
    p_def = chain.continuous_nm / (chain.gear_ratio * ETA_GEARBOX) * w / 1000.0
    losses = p_def * (1 / (ETA_GEARBOX * ETA_PINION) - 1)
    rated = max(p_rms, p_peak / overload_capability)
    return MotorSizing(p_def, losses, p_rms, p_peak, rated, motor_rpm,
                       chain.motor_shaft_peak_nm,
                       f"rated from max(RMS, peak/{overload_capability:g})")


def electrical_consistency(voltage_v: float, current_a: float, phases: int,
                           rated_kw: float, efficiency: float = 0.95) -> dict:
    """The check that was previously run single-phase and gave a false verdict.

    Run it BOTH ways and report both, so the reader sees which assumption
    drives the conclusion.
    """
    s_1ph = voltage_v * current_a
    s_3ph = math.sqrt(3.0) * voltage_v * current_a
    p_in_needed = rated_kw * 1000.0 / efficiency
    return {
        "apparent_power_1ph_mva": s_1ph / 1e6,
        "apparent_power_3ph_mva": s_3ph / 1e6,
        "input_power_needed_kw": p_in_needed / 1000.0,
        "implied_pf_1ph": p_in_needed / s_1ph if s_1ph else float("inf"),
        "implied_pf_3ph": p_in_needed / s_3ph if s_3ph else float("inf"),
        "consistent_1ph": 0.5 <= p_in_needed / s_1ph <= 1.0 if s_1ph else False,
        "consistent_3ph": 0.5 <= p_in_needed / s_3ph <= 1.0 if s_3ph else False,
    }


def synchronous_speed_rpm(poles: int, frequency_hz: float = 50.0) -> float:
    return 120.0 * frequency_hz / poles


# ---------------------------------------------------------------------------
# 6. MASS-FLOW SPEED SCHEDULE FOR A CONTINUOUS TRAIN
# ---------------------------------------------------------------------------
def mass_flow_speed_schedule(sections: list[tuple[float, float]],
                             exit_speed_m_s: float) -> list[float]:
    """b1 h1 v1 = b2 h2 v2 ... given (thickness, width) per stand, back out the
    speed each stand must run at. Returns speeds in the same order."""
    if not sections:
        raise ValueError("no sections")
    h_e, b_e = sections[-1]
    flow = h_e * b_e * exit_speed_m_s
    return [flow / (h * b) for h, b in sections]


RELEASE_BLOCKERS = (
    "stand rated force - no rating on file",
    "gearbox rated torque - no nameplate on file",
    "bearing type and dynamic capacity - no data",
    "roll material and allowable bending stress - unknown",
    "motor nameplate stator values - internally unresolved",
    "ST2 motor rpm - unknown, tandem hypothesis untested",
    "groove geometry - the width mechanism is unmeasured",
    "process temperature - never measured, profile is a declared target",
    "handling time per pass - never measured",
    "measured pass schedule (P1-P10 table meaning) - unknown",
    "motor rotor inertia (GD^2) - assumed",
    "neck bearing friction coefficient - assumed",
)


# ---------------------------------------------------------------------------
# 7. DRIVE-LIMITED SCHEDULE - the schedule the mill can actually pull
# ---------------------------------------------------------------------------
def available_roll_torque_nm(motor_kw: float, motor_rpm: float,
                             gear_ratio: float, eta: float = ETA_GEARBOX) -> float:
    return motor_kw * 1000.0 / (2 * math.pi * motor_rpm / 60.0) * gear_ratio * eta


def build_drive_limited_schedule(product: Product, roll_diameter_mm: float,
                                 linear_speed_m_s: float, torque_limit_nm: float,
                                 billet_t=150.0, billet_b=150.0, billet_len_mm=3150.0,
                                 mu=MU_BITE, max_passes=40) -> list[Pass]:
    """Same geometry chain, but each draft is additionally capped so the drive
    torque stays inside `torque_limit_nm`. This is what separates a schedule the
    mill can pull from a schedule that only satisfies the bite condition.

    Bisection on the draft, because torque is monotone in draft for a fixed
    entry state.
    """
    R = roll_diameter_mm / 2.0
    bite_max = max_draft_for_bite_mm(mu, R)
    volume_m3 = (billet_t / 1000) * (billet_b / 1000) * (billet_len_mm / 1000)
    rpm = roll_rpm(linear_speed_m_s, roll_diameter_mm)

    # First sweep at the geometric limit to learn the pass count, so the width
    # and temperature ramps have a denominator. Then re-run with that count.
    def sweep(n_expected):
        passes, h, i = [], billet_t, 0
        while h > product.thickness_mm + 1e-9 and i < max_passes:
            i += 1
            frac = min(i / max(n_expected, 1), 1.0)
            b = width_at_fraction(frac, billet_b, product.width_mm)
            T = temperature_at_fraction(frac)

            def torque_for(d):
                h1 = h - d
                Lc = contact_length_mm(R, d)
                eps = math.log(h / h1)
                edot = linear_speed_m_s * 1000.0 / Lc * eps
                sigma = flow_stress_mpa(T, max(edot, 0.01), max(eps, 0.01))
                Q = geometry_factor(Lc, (h + h1) / 2.0, mu)
                F = Q * sigma * b * Lc
                return F, Lc, eps, edot, sigma, Q, \
                    2.0 * F * LAMBDA_ARM * Lc / 1000.0 + MU_BEARING * F * 0.130 * 2.0

            d_hi = min(bite_max, h * 0.30, h - product.thickness_mm)
            if d_hi <= 1e-6:
                break
            if torque_for(d_hi)[-1] <= torque_limit_nm:
                d = d_hi
            else:
                lo, hi = 1e-4, d_hi
                for _ in range(40):
                    mid = (lo + hi) / 2
                    if torque_for(mid)[-1] <= torque_limit_nm:
                        lo = mid
                    else:
                        hi = mid
                d = lo
                if d < 0.05:
                    raise ValueError(
                        f"drive cannot pull any useful draft at h={h:.1f} mm, "
                        f"b={b:.0f} mm, T={T:.0f} C with {torque_limit_nm/1000:.0f} kN.m")
            h1 = h - d
            F, Lc, eps, edot, sigma, Q, T_drive = torque_for(d)
            T_roll = 2.0 * F * LAMBDA_ARM * Lc / 1000.0
            P = T_drive * 2 * math.pi * rpm / 60.0 / 1000.0
            piece_len = volume_m3 / ((h1 / 1000.0) * (b / 1000.0))
            passes.append(Pass(i, h, h1, b, T, d, Lc, eps, edot, sigma, Q, F,
                               T_roll, T_drive - T_roll, T_drive, P,
                               d <= bite_max, rpm, piece_len,
                               piece_len / linear_speed_m_s))
            h = h1
        return passes

    first = sweep(8)
    second = sweep(len(first))
    return second
