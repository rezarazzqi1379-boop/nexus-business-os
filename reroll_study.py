"""PRJ-STEEL-REROLL-01 - concept engineering calculations for re-rolling thick
low-carbon steel pieces (12 / 15 / 20 mm) to 6 / 8 / 10 mm.

STATUS: FEASIBILITY STUDY. Every number produced here is a CONCEPT FIGURE.
Nothing in this module is an operating setpoint, a pass recipe or a release for
manufacture or purchase. Figures carry one of three labels:

    [PC]   preliminary concept        - a model output at stated assumptions
    [RDR]  recommended design range   - a range to carry into an enquiry, not a spec
    [SM]   requires site measurement  - the model cannot settle it

Evidence classes (brief s14): FACT, MEASUREMENT, SUPPLIER CLAIM, ESTIMATE,
ASSUMPTION, HYPOTHESIS, UNKNOWN. Every input and constant is registered in
INPUT_REGISTER with its class, source and sensitivity.

ISOLATION: this project uses only the GENERIC physics functions of
slab_line_design.py (flow stress, contact length, bite, Wusatowski spread,
cooling rate, Biot number, plane-strain factor, roll stresses and deflection,
stand stretch). Every project input (roll diameter, width, temperature, speed,
bearing offset, neck diameter) is passed EXPLICITLY. That module's slab-line
defaults (400 mm width, 600 mm roll, 1250 C) are never relied on. The only
place the other project's data appears is option C (scenario S2), which is
evaluated with the recorded status: NOT operational, possibly not owned.

Units: mm, degC, N, N.m, kW, s, kg unless a name says otherwise.
stdlib only.
"""
from __future__ import annotations

import argparse
import csv
import io
import math
from dataclasses import asdict, dataclass, field
from functools import lru_cache

import slab_line_design as sld
from slab_line_design import (
    BITE_SHOCK_RANGE,
    CP,
    E_STEEL_MPA,
    ETA_GEARBOX,
    ETA_PINION,
    ETA_SPINDLE,
    GEARBOX_PEAK_ALLOWANCE,
    H_CONV,
    LAMBDA_ARM,
    MU_BEARING,
    SIGMA_SB,
    T_AMB_K,
    barrel_deflection_mm,
    bite_angle_deg,
    biot_number,
    constrained_factor,
    contact_length_mm,
    cooling_rate_c_per_s,
    flow_stress_mpa,
    geometry_factor,
    max_draft_bite_exact_mm,
    neck_bending_stress_mpa,
    roll_rpm,
    stand_stretch_mm,
    total_service_factor,
    wusatowski_exit_width_mm,
)

PROJECT_ID = "PRJ-STEEL-REROLL-01"
STUDY_DATE = "2026-09-28"

# ---------------------------------------------------------------------------
# 0. PROJECT INPUTS
# ---------------------------------------------------------------------------
RHO = 7850.0   # kg/m3 - ASSUMPTION (brief s2 "computational density")
# cooling_rate_c_per_s() uses the imported module's own RHO internally. The
# two must agree or the thermal model silently uses a different density.
assert RHO == sld.RHO, "density mismatch with the imported thermal function"


@dataclass(frozen=True)
class Piece:
    key: str
    length_mm: float   # rolling direction
    width_mm: float
    thickness_mm: float

    @property
    def volume_mm3(self) -> float:
        return self.length_mm * self.width_mm * self.thickness_mm

    @property
    def mass_kg(self) -> float:
        return self.volume_mm3 * 1e-9 * RHO


# ASSUMPTION (brief s2): lengths/widths declared in cm, thickness in mm.
PIECES = {
    "A": Piece("A", 500.0, 250.0, 12.0),
    "B": Piece("B", 400.0, 300.0, 20.0),
    "C": Piece("C", 700.0, 200.0, 15.0),
}
TARGETS_MM = (10.0, 8.0, 6.0)
CONVERSIONS = tuple((k, t) for k in ("A", "C", "B") for t in TARGETS_MM)

# Brief s4 table (CLAIM - the owner's ChatGPT screening numbers, rounded).
BRIEF_S4_LENGTH_MM = {
    ("A", 10.0): 600, ("A", 8.0): 750, ("A", 6.0): 1000,
    ("B", 10.0): 800, ("B", 8.0): 1000, ("B", 6.0): 1333,
    ("C", 10.0): 1050, ("C", 8.0): 1313, ("C", 6.0): 1750,
}
BRIEF_S4_MASS_KG = {"A": 11.78, "B": 18.84, "C": 16.49}
BRIEF_S4_REDUCTION = {  # (h0, hf): (reduction %, length factor)
    (12, 10): (16.7, 1.20), (12, 8): (33.3, 1.50), (12, 6): (50.0, 2.00),
    (15, 10): (33.3, 1.50), (15, 8): (46.7, 1.875), (15, 6): (60.0, 2.50),
    (20, 10): (50.0, 2.00), (20, 8): (60.0, 2.50), (20, 6): (70.0, 3.333),
}

# Brief s5 screening schedules (CLAIM - "starting point only").
BRIEF_S5_SCHEDULES = {
    ("A", 10.0): (12, 10),
    ("A", 8.0): (12, 10, 8),
    ("A", 6.0): (12, 9.5, 7.5, 6),
    ("C", 10.0): (15, 12.5, 10),
    ("C", 8.0): (15, 12, 10, 8),
    ("C", 6.0): (15, 11.5, 9, 7.5, 6),
    ("B", 10.0): (20, 16, 13, 10),
    ("B", 8.0): (20, 16, 12.5, 10, 8),
    ("B", 6.0): (20, 16, 12.5, 9.5, 7.5, 6),
}

GRADES = ("S235JR", "S355JR")    # S235 nominal, S355 the conservative bound
MU_RANGE = (0.25, 0.35)          # ASSUMPTION hot friction (validation memo: CONSISTENT)
MU_NOMINAL = 0.30

# ---------------------------------------------------------------------------
# 1. THERMAL / METALLURGICAL CONSTANTS
# ---------------------------------------------------------------------------
REHEAT_RANGE_C = (1150.0, 1250.0)   # ESTIMATE low-carbon hot-working window
OVERHEATING_ONSET_C = 1300.0        # ESTIMATE (see THERMAL_SOURCE_NOTE)
BURNING_ONSET_C = 1400.0            # ESTIMATE (see THERMAL_SOURCE_NOTE)
THERMAL_SOURCE_NOTE = (
    "Reheat window 1150-1250 C for plain low-carbon steel and the overheating "
    "(~1300 C, grain coarsening and sulphide re-precipitation at grain boundaries) "
    "and burning (~1400 C and above, grain-boundary incipient melting/oxidation, "
    "irreversible) limits are ESTIMATES recalled from standard hot-working references "
    "(ASM Handbook Vol. 14A 'Forging of Carbon and Alloy Steels', maximum forging "
    "temperature ~1260-1290 C for 0.1-0.3 %C plain carbon steel; general metallurgy "
    "texts on overheating/burning). NOT re-fetched in this session. The actual limit "
    "depends on C and S content, which is UNKNOWN (HP-02)."
)
FINISH_TEMPS_C = (800.0, 850.0, 880.0)   # evaluated as a parameter: Ar3 is EDGE
FINISH_NOMINAL_C = 850.0
EMISSIVITY_NOMINAL = 0.85                 # ESTIMATE oxidised steel/scale 0.85-0.89
EMISSIVITY_RANGE = (0.75, 0.90)
H_GAP_NOMINAL = 15000.0                   # W/m2K roll-gap heat transfer, ASSUMPTION
H_GAP_RANGE = (10000.0, 30000.0)
ROLL_SURFACE_C = 150.0                    # ASSUMPTION uncooled small-mill roll surface
ETA_DEFORMATION_HEAT = 0.90               # ESTIMATE Taylor-Quinney fraction
K_ROLL, CP_ROLL = 45.0, 480.0             # ASSUMPTION roll steel near 150 C
K_STOCK = 28.0                            # ASSUMPTION (same as imported K_STEEL)
EPS_FURNACE_EFF = 0.70                    # ASSUMPTION furnace-to-piece effective emissivity
FURNACE_MARGIN_C = 40.0                   # ASSUMPTION furnace set above piece target
FIRST_SOAK_S = 600.0                      # [RDR] 5-15 min equalisation after reaching target
FIRST_SOAK_RANGE_S = (300.0, 900.0)
AMBIENT_C = T_AMB_K - 273.15

# Scale: parabolic oxidation, Paidassi constant for iron in air (oxygen uptake).
# ESTIMATE - literature constant as quoted by Chen & Yuen, Oxidation of Metals 59
# (2003) review, valid ~700-1250 C. Recalled, not re-fetched. kp_factor spans
# furnace atmosphere and steel chemistry (Si, Cr slow it; water vapour speeds it).
KP_A_G2_CM4_S = 0.37
KP_Q_J_MOL = 138000.0
KP_FACTOR = {"low": 0.5, "nominal": 0.8, "high": 1.2}   # ASSUMPTION band
FE_PER_O_IN_FEO = 55.845 / 15.999

# ---------------------------------------------------------------------------
# 2. YIELD CONSTANTS (all ASSUMPTION unless stated; low / nominal / high LOSS)
# ---------------------------------------------------------------------------
YIELD_CASES = {
    # irregular original end length per end, at the ORIGINAL section (mm) [SM].
    # Averaged over all ends: the photo description (CLAIM) says SOME ends are
    # rounded, conical or irregular, not all.
    "irregular_end_mm": {"low": 5.0, "nominal": 15.0, "high": 30.0},
    # tongue / fishtail allowance per end at the FINAL section (mm), reached at
    # >= 50 % total reduction and scaled down linearly below that.
    "tongue_mm": {"low": 10.0, "nominal": 25.0, "high": 40.0},
    # edge trim per side at final dimensions (mm); 0 = sold with mill edge
    "edge_trim_mm": {"low": 0.0, "nominal": 5.0, "high": 12.0},
    # out-of-tolerance fraction of the trimmed mass
    "out_of_tol": {"low": 0.02, "nominal": 0.05, "high": 0.10},
}

# ---------------------------------------------------------------------------
# 3. SCENARIOS AS DATA
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Scenario:
    key: str
    label: str
    hot: bool
    roll_d_mm: float
    roll_d_range: tuple
    barrel_mm: float
    barrel_range: tuple
    speed_m_s: float
    speed_range: tuple
    reversing: bool | None
    interpass_s: float
    interpass_range: tuple
    transfer_s: float           # furnace discharge -> first bite, incl. descale
    return_s: float             # mill -> furnace for a reheat
    reheat_policy: str
    bearing_offset_mm: float    # bearing centre to barrel end
    neck_ratio: float
    mill_modulus_mn_mm: tuple
    force_rating_n: float | None
    torque_rating_nm: float | None
    rating_basis: str
    max_reduction: float
    last_pass_max_reduction: float
    bite_utilisation: float
    status: str
    handling: str


def _slab_line_design_duty() -> tuple[float, float]:
    """Option C proxy, recomputed from the other project's model on ITS stated basis:
    peak separating force and peak roll torque over its whole product envelope
    (balanced scenario, S355JR, all THICKNESS_TARGETS_MM 6-30 mm). This is the design
    DUTY the stand RFI quotes (5.12 MN, 218.3 kN.m), not a rating - the real stand
    rating is UNKNOWN. Computed, never hard-coded (FM-010: a value at one thickness
    must not stand in for the envelope)."""
    f_max = t_max = 0.0
    for t in sld.THICKNESS_TARGETS_MM:
        w = sld.worst_cases(sld.build_schedule(t, "balanced", grade="S355JR"))
        f_max = max(f_max, w["max_force"].force_n)
        t_max = max(t_max, w["max_torque"].torque_roll_nm)
    return f_max, t_max


_SLD_FORCE_N, _SLD_TORQUE_NM = _slab_line_design_duty()

SCENARIOS = {
    "S1": Scenario(
        key="S1", label="Small two-high reversing hot mill (new or stock)", hot=True,
        roll_d_mm=400.0, roll_d_range=(350.0, 450.0),
        barrel_mm=550.0, barrel_range=(500.0, 600.0),
        speed_m_s=0.6, speed_range=(0.3, 1.0), reversing=True,
        interpass_s=8.0, interpass_range=(5.0, 12.0),
        transfer_s=20.0, return_s=15.0,
        reheat_policy="return to a small batch furnace when the next pass would "
                      "finish below the finishing limit",
        bearing_offset_mm=150.0, neck_ratio=0.55,
        mill_modulus_mn_mm=(0.5, 1.5), force_rating_n=None, torque_rating_nm=None,
        rating_basis="S1 is the equipment being SIZED here; its rating is an output",
        max_reduction=0.30, last_pass_max_reduction=0.20, bite_utilisation=0.85,
        status="concept - to be sourced (new or stock)",
        handling="manual tongs or semi-automatic tilting table"),
    "S2": Scenario(
        key="S2", label="Option C: the D600 x 600 two-high stand of PRJ-STEEL-ROLLING-LINE-01",
        hot=True, roll_d_mm=600.0, roll_d_range=(600.0, 600.0),
        barrel_mm=600.0, barrel_range=(600.0, 600.0),
        speed_m_s=0.8, speed_range=(0.8, 3.0), reversing=None,
        interpass_s=8.0, interpass_range=(6.0, 12.0),
        transfer_s=40.0, return_s=40.0,
        reheat_policy="no practical reheat loop: a 20 t/h walking-beam furnace does "
                      "not take back 12-19 kg pieces; any reheat needs a separate furnace",
        bearing_offset_mm=250.0, neck_ratio=0.55,
        mill_modulus_mn_mm=(3.0, 8.0),
        force_rating_n=_SLD_FORCE_N, torque_rating_nm=_SLD_TORQUE_NM,
        rating_basis="PROXY, not a rating: the slab-line model's computed design duty "
                     "over its 6-30 mm envelope (balanced, S355JR), the figure its stand "
                     "RFI quotes. The real stand rating is UNKNOWN (that project's PRC-01).",
        max_reduction=0.30, last_pass_max_reduction=0.20, bite_utilisation=0.85,
        status="NOT operational; no equipment recorded as owned or purchased "
               "(control doc, 2026-09-28); stand status open under PRC-01",
        handling="designed for 1.2 t, 3 m slabs on powered roller tables"),
    "S3": Scenario(
        key="S3", label="Toll rolling at a plate/strip-mill-size plant (parameter range)",
        hot=True, roll_d_mm=750.0, roll_d_range=(500.0, 1000.0),
        barrel_mm=1500.0, barrel_range=(800.0, 2500.0),
        speed_m_s=1.5, speed_range=(0.5, 3.0), reversing=True,
        interpass_s=10.0, interpass_range=(6.0, 15.0),
        transfer_s=30.0, return_s=30.0,
        reheat_policy="host-dependent; assumed possible in a host batch furnace",
        bearing_offset_mm=300.0, neck_ratio=0.55,
        mill_modulus_mn_mm=(3.0, 6.0), force_rating_n=5.0e6, torque_rating_nm=None,
        rating_basis="ASSUMPTION: a plate/strip-mill stand of this class is rated at "
                     "5 MN or more; the host's real rating is UNKNOWN",
        max_reduction=0.30, last_pass_max_reduction=0.20, bite_utilisation=0.85,
        status="market option - no host identified, no contact made",
        handling="host-dependent; short pieces are the acceptance risk"),
    "S4": Scenario(
        key="S4", label="Cold-rolling check (two-high D400 or four-high D180 work roll)",
        hot=False, roll_d_mm=400.0, roll_d_range=(180.0, 400.0),
        barrel_mm=550.0, barrel_range=(500.0, 600.0),
        speed_m_s=0.3, speed_range=(0.1, 0.5), reversing=True,
        interpass_s=10.0, interpass_range=(8.0, 20.0),
        transfer_s=0.0, return_s=0.0,
        reheat_policy="not applicable; intermediate/final anneal instead",
        bearing_offset_mm=150.0, neck_ratio=0.55,
        mill_modulus_mn_mm=(1.0, 3.0), force_rating_n=None, torque_rating_nm=None,
        rating_basis="feasibility and force check only",
        max_reduction=0.25, last_pass_max_reduction=0.15, bite_utilisation=0.85,
        status="check only",
        handling="manual"),
}

# ---------------------------------------------------------------------------
# 4. GEOMETRY, BITE, FORCE - thin project wrappers over the imported physics
# ---------------------------------------------------------------------------
def reduction_pct(h0: float, h1: float) -> float:
    return 100.0 * (h0 - h1) / h0


def theoretical_length_mm(piece: Piece, hf: float) -> float:
    """Brief s4: L_f = L_0 h_0 / h_f (width constant, no spread, no losses)."""
    if hf <= 0:
        raise ValueError("final thickness must be positive")
    return piece.length_mm * piece.thickness_mm / hf


def bite_limit_mm(mu: float, roll_d_mm: float, utilisation: float = 1.0) -> float:
    """Exact self-acting bite limit dh = D (1 - cos(arctan mu)), times a utilisation."""
    return max_draft_bite_exact_mm(mu, roll_diameter_mm=roll_d_mm) * utilisation


def bite_ok(draft_mm: float, roll_d_mm: float, mu: float = MU_RANGE[0],
            utilisation: float = 1.0) -> bool:
    """True when the draft can be bitten unaided at friction mu. Uses the EXACT
    limit (the mu^2 R form overstates it by 4.7-9 %)."""
    if draft_mm < 0:
        raise ValueError("draft must be non-negative")
    if draft_mm >= roll_d_mm:
        return False
    return draft_mm <= bite_limit_mm(mu, roll_d_mm, utilisation) + 1e-9


def mu_required(draft_mm: float, roll_d_mm: float) -> float:
    """Friction needed to bite: tan(alpha), cos(alpha) = 1 - dh/D."""
    return math.tan(math.radians(bite_angle_deg(draft_mm, roll_diameter_mm=roll_d_mm)))


def roll_force_n(constrained_flow_stress_mpa: float, mean_width_mm: float,
                 contact_len_mm: float, mean_h_mm: float, mu: float) -> tuple[float, float]:
    """F = Q_p * k * b_m * L. Returns (force N, Q_p). Q_p from the imported
    geometry_factor (Ekelund/Sims friction-hill form, ESTIMATE)."""
    q = geometry_factor(contact_len_mm, mean_h_mm, mu)
    return q * constrained_flow_stress_mpa * mean_width_mm * contact_len_mm, q


# ---------------------------------------------------------------------------
# 5. ROLL CROWN (bending + shear under a load distributed over the strip width)
# ---------------------------------------------------------------------------
G_ROLL_MPA = 80000.0     # ESTIMATE shear modulus of roll steel
KAPPA_ROUND = 0.9        # ESTIMATE Timoshenko shear coefficient, solid round


def roll_crown_mm(force_n: float, strip_width_mm: float, barrel_mm: float,
                  roll_d_mm: float, bearing_offset_mm: float) -> float:
    """Deflection of ONE roll at the strip centre relative to the strip edge.

    Simply supported at the bearing centres (span = barrel + 2 offset), load F
    spread uniformly over the strip width. Bending by numerical double
    integration of M/EI from the centre line, plus Timoshenko shear.
    ESTIMATE - ignores roll flattening, thermal crown, wear, ground camber and
    chock/neck compliance, all of which are [SM]."""
    if force_n < 0 or min(strip_width_mm, barrel_mm, roll_d_mm) <= 0:
        raise ValueError("invalid crown inputs")
    b = min(strip_width_mm, barrel_mm)
    span = barrel_mm + 2.0 * bearing_offset_mm
    w = force_n / b
    r = force_n / 2.0
    ei = E_STEEL_MPA * math.pi * roll_d_mm ** 4 / 64.0
    n = 200
    dx = (b / 2.0) / n
    theta = y = 0.0
    m_prev = r * span / 2.0 - w * (b / 2.0) ** 2 / 2.0
    for i in range(1, n + 1):
        x = i * dx
        m = r * (span / 2.0 - x) - w * (b / 2.0 - x) ** 2 / 2.0
        theta_new = theta + (m_prev + m) / 2.0 * dx / ei
        y += (theta + theta_new) / 2.0 * dx
        theta, m_prev = theta_new, m
    area = math.pi * roll_d_mm ** 2 / 4.0
    shear = w * b ** 2 / (8.0 * KAPPA_ROUND * G_ROLL_MPA * area)
    return y + shear


# ---------------------------------------------------------------------------
# 6. THERMAL MODEL (lumped; valid because Bi << 0.1 for 6-20 mm, checked)
# ---------------------------------------------------------------------------
def piece_area_m2(h: float, b: float, length: float) -> float:
    return 2.0 * (h * b + h * length + b * length) * 1e-6


def piece_cooling_rate_c_per_s(h: float, b: float, length: float, temp_c: float,
                               emissivity: float) -> float:
    """Imported cooling_rate_c_per_s (faces + side edges per unit length),
    corrected for the two END faces, which matter for 0.4-1.75 m pieces."""
    base = cooling_rate_c_per_s(h, b, temp_c, emissivity=emissivity)
    end_correction = 1.0 + (h * b) / ((h + b) * length)
    return base * end_correction


def cool_piece(temp_c: float, h: float, b: float, length: float, seconds: float,
               emissivity: float = EMISSIVITY_NOMINAL, dt: float = 0.25) -> float:
    """Air cooling over `seconds` (radiation + convection), explicit integration."""
    if seconds < 0:
        raise ValueError("time must be non-negative")
    t, temp = 0.0, temp_c
    while t < seconds - 1e-12:
        step = min(dt, seconds - t)
        temp -= piece_cooling_rate_c_per_s(h, b, length, temp, emissivity) * step
        t += step
    return temp


def roll_chill_c(temp_c: float, mean_h_mm: float, contact_time_s: float,
                 h_gap: float = H_GAP_NOMINAL, roll_surface_c: float = ROLL_SURFACE_C) -> float:
    """Mean-temperature drop from conduction into BOTH rolls during one bite.

    Per face Q = h_gap dT t_c, capped by two semi-infinite bodies in contact
    Q <= 2 e_eff dT sqrt(t_c/pi), e_eff = e_s e_r/(e_s + e_r).
    dT_mean = 2 Q / (rho cp h). Replaces the imported fixed 8 C/contact, which was
    set for a 125 mm slab and is NOT valid for 6-20 mm stock (the mean-temperature
    drop scales with 1/h)."""
    if contact_time_s <= 0:
        return 0.0
    dtemp = max(temp_c - roll_surface_c, 0.0)
    e_s = math.sqrt(K_STOCK * RHO * CP)
    e_r = math.sqrt(K_ROLL * RHO * CP_ROLL)
    e_eff = e_s * e_r / (e_s + e_r)
    q_htc = h_gap * dtemp * contact_time_s
    q_cap = 2.0 * e_eff * dtemp * math.sqrt(contact_time_s / math.pi)
    q = min(q_htc, q_cap)
    return 2.0 * q / (RHO * CP * mean_h_mm / 1000.0)


def deformation_heating_c(mean_pressure_mpa: float, strain: float,
                          eta: float = ETA_DEFORMATION_HEAT) -> float:
    """Adiabatic temperature rise from plastic work ~ p_mean * eps per unit volume."""
    return eta * mean_pressure_mpa * 1e6 * strain / (RHO * CP)


def kp_paidassi(temp_c: float) -> float:
    """Parabolic rate constant, g^2 O / cm^4 / s. ESTIMATE (see header)."""
    if temp_c < 600.0:
        return 0.0
    return KP_A_G2_CM4_S * math.exp(-KP_Q_J_MOL / (8.314 * (temp_c + 273.15)))


def scale_metal_loss_kg(area_m2: float, w2_integral: float, kp_factor: float) -> float:
    """Metal lost to scale in one heat (scale removed at descaling, growth restarts)."""
    o_gain_g_cm2 = math.sqrt(max(w2_integral, 0.0) * kp_factor)
    return area_m2 * o_gain_g_cm2 * FE_PER_O_IN_FEO * 10.0   # g/cm2 -> kg/m2


@lru_cache(maxsize=4096)
def heat_up(start_c: float, target_c: float, h: float, b: float, length: float,
            furnace_c: float, eps_eff: float = EPS_FURNACE_EFF,
            dt: float = 1.0) -> tuple[float, float]:
    """Lumped radiative heating in a furnace at furnace_c until target_c.
    Returns (seconds, integral of kp dt for scale). ESTIMATE; ignores shading of
    stacked pieces (x1.5-2 on time if pieces touch) and the insulating rust layer."""
    if target_c >= furnace_c:
        raise ValueError("target must be below the furnace temperature")
    area = piece_area_m2(h, b, length)
    mass = h * b * length * 1e-9 * RHO
    temp, t, w2 = start_c, 0.0, 0.0
    tf4 = (furnace_c + 273.15) ** 4
    while temp < target_c and t < 36000.0:
        q = eps_eff * SIGMA_SB * (tf4 - (temp + 273.15) ** 4) + H_CONV * (furnace_c - temp)
        temp += q * area / (mass * CP) * dt
        w2 += kp_paidassi(temp) * dt
        t += dt
    return t, w2


# ---------------------------------------------------------------------------
# 7. THERMAL PARAMETERS BUNDLE
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Thermal:
    first_heat_c: float = 1200.0
    reheat_c: float = 1150.0
    finish_min_c: float = FINISH_NOMINAL_C
    emissivity: float = EMISSIVITY_NOMINAL
    h_gap: float = H_GAP_NOMINAL
    roll_surface_c: float = ROLL_SURFACE_C
    soak_s: float = FIRST_SOAK_S
    transfer_s: float | None = None     # None -> scenario value
    interpass_s: float | None = None    # None -> scenario value
    kp_factor: float = KP_FACTOR["nominal"]


# ---------------------------------------------------------------------------
# 8. PASS SCHEDULE DESIGN
# ---------------------------------------------------------------------------
def design_schedule(h0: float, hf: float, sc: Scenario, mu_bite: float = MU_RANGE[0],
                    roll_d_mm: float | None = None, max_passes: int = 40) -> tuple:
    """Fewest passes such that: every draft <= bite_utilisation x exact bite limit
    at mu_bite (the LOW end of the friction range); every reduction <=
    sc.max_reduction; the last pass <= sc.last_pass_max_reduction (gauge/flatness
    control). Equal reduction on the other passes. Intermediate gauges rounded to
    0.1 mm and re-checked. Fewer, heavier passes is deliberate: for 12-19 kg
    pieces heat loss between passes, not force, is the binding constraint."""
    if not 0 < hf < h0:
        raise ValueError("need 0 < hf < h0")
    d = roll_d_mm or sc.roll_d_mm
    cap = bite_limit_mm(mu_bite, d, sc.bite_utilisation)
    for n in range(1, max_passes + 1):
        if n == 1:
            seq = [h0, hf]
        else:
            r_eq = 1.0 - (hf / h0) ** (1.0 / n)
            if r_eq <= sc.last_pass_max_reduction:
                seq = [h0 * (1 - r_eq) ** i for i in range(n)] + [hf]
            else:
                h_last_in = hf / (1.0 - sc.last_pass_max_reduction)
                if h_last_in >= h0:
                    seq = [h0, hf]
                else:
                    r = 1.0 - (h_last_in / h0) ** (1.0 / (n - 1))
                    seq = [h0 * (1 - r) ** i for i in range(n)] + [hf]
            seq = [seq[0]] + [round(x, 1) for x in seq[1:-1]] + [seq[-1]]
        ok = True
        for i, (a, c) in enumerate(zip(seq[:-1], seq[1:])):
            last = i == len(seq) - 2
            lim = sc.last_pass_max_reduction if last else sc.max_reduction
            if c >= a or (a - c) / a > lim + 1e-9 or (a - c) > cap + 1e-9:
                ok = False
                break
        if ok:
            return tuple(float(x) for x in seq)
    raise ValueError("no schedule found")


def schedule_for(piece_key: str, target: float, kind: str, sc: Scenario,
                 roll_d_mm: float | None = None) -> tuple:
    if kind == "brief":
        return tuple(float(x) for x in BRIEF_S5_SCHEDULES[(piece_key, target)])
    if kind == "recommended":
        return design_schedule(PIECES[piece_key].thickness_mm, target, sc, roll_d_mm=roll_d_mm)
    raise ValueError(f"unknown schedule kind {kind!r}")


# ---------------------------------------------------------------------------
# 9. PASS-BY-PASS SIMULATION
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PassRow:
    index: int
    heat: int
    direction: str
    reheat_before: bool
    entry_h: float
    exit_h: float
    draft: float
    reduction_pct: float
    cum_reduction_pct: float
    entry_b: float
    exit_b: float
    exit_len_mm: float
    exit_mass_kg: float
    bite_angle_deg: float
    mu_required: float
    bite_limit_mm: float
    bite_ok: bool
    contact_len_mm: float
    strain: float
    strain_rate_s: float
    flow_stress_mpa: float
    q_p: float
    mean_pressure_mpa: float
    force_n: float
    torque_per_roll_nm: float
    torque_total_nm: float
    power_kw: float
    speed_m_s: float
    roll_rpm: float
    rolling_time_s: float
    entry_temp_c: float
    chill_c: float
    deformation_heat_c: float
    exit_temp_c: float
    transfer_after_s: float
    transfer_loss_c: float
    gap_crown_mm: float
    crown_pct_of_h: float
    point_load_deflection_mm: float
    neck_stress_mpa: float
    stretch_mm_low_modulus: float
    stretch_mm_high_modulus: float
    below_finish: bool


@dataclass
class Run:
    piece_key: str
    target: float
    scenario: str
    kind: str
    grade: str
    mu: float
    roll_d_mm: float
    speed_m_s: float
    thermal: Thermal
    thicknesses: tuple
    spread: bool
    passes: list = field(default_factory=list)
    heats: int = 1
    reheats: int = 0
    furnace_time_s: float = 0.0
    mill_time_s: float = 0.0
    scale_w2_per_heat: list = field(default_factory=list)
    scale_area_per_heat: list = field(default_factory=list)
    feasible: bool = True
    notes: list = field(default_factory=list)

    @property
    def final(self) -> PassRow:
        return self.passes[-1]

    @property
    def conversion(self) -> str:
        p = PIECES[self.piece_key]
        return f"{self.piece_key} {p.thickness_mm:g}->{self.target:g}"

    def peak(self, attr: str) -> float:
        return max(getattr(p, attr) for p in self.passes)

    @property
    def rms_power_kw(self) -> float:
        e = sum(p.power_kw ** 2 * p.rolling_time_s for p in self.passes)
        return math.sqrt(e / self.mill_time_s) if self.mill_time_s > 0 else 0.0

    @property
    def rms_torque_total_nm(self) -> float:
        e = sum(p.torque_total_nm ** 2 * p.rolling_time_s for p in self.passes)
        return math.sqrt(e / self.mill_time_s) if self.mill_time_s > 0 else 0.0

    def scale_loss_kg(self, kp_factor: float | None = None) -> float:
        f = self.thermal.kp_factor if kp_factor is None else kp_factor
        return sum(scale_metal_loss_kg(a, w2, f)
                   for a, w2 in zip(self.scale_area_per_heat, self.scale_w2_per_heat))


HANDLING_OVERHEAD_S = 30.0   # ASSUMPTION per piece: tongs, measure, mark, stack
MILL_UTILISATION = 0.65      # ASSUMPTION manual crew, delays, gauge checks (0.5-0.8)


def pass_mechanics(h0: float, h1: float, b0: float, temp_c: float, roll_d_mm: float,
                   speed_m_s: float, mu: float, grade: str, spread: bool = True) -> dict:
    """One hot pass at entry temperature temp_c. Every roll/project input explicit."""
    draft = h0 - h1
    if draft <= 0:
        raise ValueError("draft must be positive")
    lc = contact_length_mm(draft, roll_diameter_mm=roll_d_mm)
    b1 = wusatowski_exit_width_mm(h0, h1, b0, roll_diameter_mm=roll_d_mm) if spread else b0
    eps = math.log(h0 / h1)
    edot = speed_m_s * 1000.0 / lc * eps
    hm, bm = (h0 + h1) / 2.0, (b0 + b1) / 2.0
    cf = constrained_factor(bm, hm)
    sigma = flow_stress_mpa(temp_c, max(edot, 0.01), max(eps, 0.01), grade) * cf
    force, q = roll_force_n(sigma, bm, lc, hm, mu)
    return dict(draft=draft, lc=lc, b1=b1, eps=eps, edot=edot, sigma=sigma, q=q,
                p_mean=q * sigma, force=force)


def simulate(piece_key: str, target: float, scenario: str = "S1", kind: str = "recommended",
             grade: str = "S235JR", mu: float = MU_NOMINAL, thermal: Thermal | None = None,
             roll_d_mm: float | None = None, speed_m_s: float | None = None,
             spread: bool = True, thicknesses: tuple | None = None) -> Run:
    """Pass-by-pass hot simulation with a reheat decision before every pass.

    Rule: if the predicted EXIT temperature of the next pass is below the
    finishing limit, the piece goes back to the furnace first. If a pass fails
    even straight out of a reheat the run is flagged infeasible (warm rolling)."""
    sc = SCENARIOS[scenario]
    if not sc.hot:
        raise ValueError("use cold_schedule() for S4")
    th = thermal or Thermal()
    d = roll_d_mm or sc.roll_d_mm
    v = speed_m_s or sc.speed_m_s
    transfer = sc.transfer_s if th.transfer_s is None else th.transfer_s
    interpass = sc.interpass_s if th.interpass_s is None else th.interpass_s
    piece = PIECES[piece_key]
    seq = thicknesses or schedule_for(piece_key, target, kind, sc, roll_d_mm=d)
    run = Run(piece_key, target, scenario, kind, grade, mu, d, v, th, tuple(seq), spread)
    neck_d = sc.neck_ratio * d
    k_lo, k_hi = sc.mill_modulus_mn_mm

    h, b, length = piece.thickness_mm, piece.width_mm, piece.length_mm
    # first heat: from ambient to first_heat_c, then soak
    t_heat, w2 = heat_up(AMBIENT_C, th.first_heat_c, h, b, length,
                         th.first_heat_c + FURNACE_MARGIN_C)
    w2 += kp_paidassi(th.first_heat_c) * th.soak_s
    run.furnace_time_s = t_heat + th.soak_s
    run.scale_area_per_heat.append(piece_area_m2(h, b, length))
    temp = th.first_heat_c
    # transfer to the first bite
    t_air = transfer
    temp_before = temp
    temp = cool_piece(temp, h, b, length, transfer, th.emissivity)
    w2 += kp_paidassi((temp + temp_before) / 2.0) * transfer
    run.mill_time_s = transfer + HANDLING_OVERHEAD_S
    passes_in_heat = 0
    heat = 1
    reheat_flag = False
    n = len(seq) - 1

    def predict(h0, h1, b0, t_in, length_in):
        m = pass_mechanics(h0, h1, b0, t_in, d, v, mu, grade, spread)
        lc_t = m["lc"] / (v * 1000.0)
        chill = roll_chill_c(t_in, (h0 + h1) / 2.0, lc_t, th.h_gap, th.roll_surface_c)
        heat_def = deformation_heating_c(m["p_mean"], m["eps"])
        len1 = length_in * h0 * b0 / (h1 * m["b1"])
        t_roll = len1 / 1000.0 / v
        t_out = cool_piece(t_in - chill + heat_def, h1, m["b1"], len1, t_roll, th.emissivity)
        return m, chill, heat_def, len1, t_roll, t_out

    for i in range(n):
        h0, h1 = seq[i], seq[i + 1]
        m, chill, heat_def, len1, t_roll, t_out = predict(h0, h1, b, temp, length)
        if t_out < th.finish_min_c and passes_in_heat > 0:
            # reheat before this pass
            run.scale_w2_per_heat.append(w2)
            temp_back = cool_piece(temp, h, b, length, sc.return_s, th.emissivity)
            t_re, w2 = heat_up(round(temp_back), th.reheat_c, h, round(b, 1), round(length),
                               th.reheat_c + FURNACE_MARGIN_C)
            run.furnace_time_s += t_re
            run.mill_time_s += sc.return_s + transfer
            run.scale_area_per_heat.append(piece_area_m2(h, b, length))
            temp = cool_piece(th.reheat_c, h, b, length, transfer, th.emissivity)
            w2 += kp_paidassi(th.reheat_c) * transfer
            heat += 1
            run.reheats += 1
            passes_in_heat = 0
            reheat_flag = True
            m, chill, heat_def, len1, t_roll, t_out = predict(h0, h1, b, temp, length)
        below = t_out < th.finish_min_c
        if below:
            run.feasible = False
            run.notes.append(f"pass {i + 1} exits at {t_out:.0f} C, below "
                             f"{th.finish_min_c:.0f} C even after a reheat")
        force = m["force"]
        torque_roll = force * LAMBDA_ARM * m["lc"] / 1000.0
        torque_bear = MU_BEARING * force * (neck_d / 2.0) / 1000.0
        torque_total = 2.0 * (torque_roll + torque_bear)
        rpm = roll_rpm(v, diameter_mm=d)
        power = torque_total * 2.0 * math.pi * rpm / 60.0 / 1000.0
        last = i == n - 1
        t_after = 0.0 if last else interpass
        t_next = t_out if last else cool_piece(t_out, h1, m["b1"], len1, interpass, th.emissivity)
        crown = 2.0 * roll_crown_mm(force, m["b1"], sc.barrel_mm, d, sc.bearing_offset_mm)
        run.passes.append(PassRow(
            index=i + 1, heat=heat,
            direction=("forward" if (i % 2 == 0 or sc.reversing is False) else "reverse"),
            reheat_before=reheat_flag,
            entry_h=h0, exit_h=h1, draft=m["draft"], reduction_pct=reduction_pct(h0, h1),
            cum_reduction_pct=reduction_pct(piece.thickness_mm, h1),
            entry_b=b, exit_b=m["b1"], exit_len_mm=len1,
            exit_mass_kg=h1 * m["b1"] * len1 * 1e-9 * RHO,
            bite_angle_deg=bite_angle_deg(m["draft"], roll_diameter_mm=d),
            mu_required=mu_required(m["draft"], d),
            bite_limit_mm=bite_limit_mm(MU_RANGE[0], d, sc.bite_utilisation),
            bite_ok=bite_ok(m["draft"], d, MU_RANGE[0], sc.bite_utilisation),
            contact_len_mm=m["lc"], strain=m["eps"], strain_rate_s=m["edot"],
            flow_stress_mpa=m["sigma"], q_p=m["q"], mean_pressure_mpa=m["p_mean"],
            force_n=force, torque_per_roll_nm=torque_roll + torque_bear,
            torque_total_nm=torque_total, power_kw=power, speed_m_s=v, roll_rpm=rpm,
            rolling_time_s=t_roll, entry_temp_c=temp, chill_c=chill,
            deformation_heat_c=heat_def, exit_temp_c=t_out,
            transfer_after_s=t_after, transfer_loss_c=t_out - t_next,
            gap_crown_mm=crown, crown_pct_of_h=100.0 * crown / h1,
            point_load_deflection_mm=barrel_deflection_mm(
                force, strip_width_mm=m["b1"], barrel_mm=sc.barrel_mm,
                diameter_mm=d, offset_mm=sc.bearing_offset_mm),
            neck_stress_mpa=neck_bending_stress_mpa(force, neck_diameter_mm=neck_d,
                                                    offset_mm=sc.bearing_offset_mm),
            stretch_mm_low_modulus=stand_stretch_mm(force, k_lo),
            stretch_mm_high_modulus=stand_stretch_mm(force, k_hi),
            below_finish=below))
        run.mill_time_s += t_roll + t_after
        w2 += kp_paidassi((temp + t_next) / 2.0) * (t_roll + t_after)
        h, b, length, temp = h1, m["b1"], len1, t_next
        passes_in_heat += 1
        reheat_flag = False
    run.scale_w2_per_heat.append(w2)
    run.heats = heat
    return run


# ---------------------------------------------------------------------------
# 10. YIELD / MASS BALANCE
# ---------------------------------------------------------------------------
def yield_breakdown(run: Run, case: str = "nominal", include_scale: bool = True) -> dict:
    """Mass accounting that closes exactly: input = scale + crop + trim + OOT + saleable.

    Scale uses the run's own thermal history (Paidassi parabolic law, kp_factor
    by case). Crop = irregular original ends (at original section) + tongue
    allowance at the final section (scaled by total reduction, full at >= 50 %).
    Trim at final section. OOT a fraction. case 'high' = high LOSS."""
    piece = PIECES[run.piece_key]
    m0 = piece.mass_kg
    kp_case = {"low": "low", "nominal": "nominal", "high": "high"}[case]
    scale = run.scale_loss_kg(KP_FACTOR[kp_case]) if include_scale else 0.0
    rolled = m0 - scale
    f = run.final
    lin_final = f.exit_h * f.exit_b * 1e-9 * RHO * (rolled / m0)   # kg per mm of length
    irregular = 2.0 * YIELD_CASES["irregular_end_mm"][case] * piece.width_mm \
        * piece.thickness_mm * 1e-9 * RHO * (rolled / m0)
    red = 1.0 - f.exit_h / piece.thickness_mm
    tongue = 2.0 * YIELD_CASES["tongue_mm"][case] * min(1.0, red / 0.5) * lin_final
    crop = min(irregular + tongue, rolled)
    after_crop = rolled - crop
    trim_frac = min(2.0 * YIELD_CASES["edge_trim_mm"][case] / f.exit_b, 1.0)
    trim = after_crop * trim_frac
    after_trim = after_crop - trim
    oot = after_trim * YIELD_CASES["out_of_tol"][case]
    saleable = after_trim - oot
    return {"input_kg": m0, "scale_kg": scale, "crop_kg": crop, "trim_kg": trim,
            "oot_kg": oot, "saleable_kg": saleable, "yield": saleable / m0,
            "scale_pct": 100 * scale / m0, "crop_pct": 100 * crop / m0,
            "trim_pct": 100 * trim / m0, "oot_pct": 100 * oot / m0}


# ---------------------------------------------------------------------------
# 11. CAPACITY AND FURNACE TIERS
# ---------------------------------------------------------------------------
TIERS = {
    # name: (annual input tonnes, clock hours per year available, basis). Mill
    # utilisation is already inside the mill pace (MILL_UTILISATION).
    "pilot": (0.1, None, "one campaign of 5-10 pieces, ~100 kg, one charge (HP-01 scenario)"),
    "workshop": (50.0, 2000.0, "50 t/yr, up to one 8 h shift x 250 d"),
    "industrial": (2000.0, 4000.0, "2000 t/yr, up to two 8 h shifts x 250 d"),
}
PILOT_HEAT_H = 1.0                     # ASSUMPTION slow heat of one 100 kg charge
FURNACE_EFFICIENCY = (0.20, 0.35)      # ASSUMPTION small batch gas furnace
STEEL_ENTHALPY_KJ_KG_1200 = 800.0      # ESTIMATE 20 -> 1200 C incl. alpha-gamma
HEARTH_PACKING = 0.6                   # ASSUMPTION single layer, spacing for heating


def capacity(run: Run, utilisation: float = MILL_UTILISATION) -> dict:
    piece = PIECES[run.piece_key]
    occupancy = run.mill_time_s
    pph = 3600.0 * utilisation / occupancy
    residence_h = run.furnace_time_s / 3600.0
    in_furnace = pph * residence_h
    return {"mill_occupancy_s": occupancy, "pieces_per_h": pph,
            "kg_per_h_input": pph * piece.mass_kg,
            "kg_per_h_saleable": pph * piece.mass_kg * yield_breakdown(run)["yield"],
            "furnace_residence_min": run.furnace_time_s / 60.0,
            "pieces_in_furnace": in_furnace}


def furnace_tier(tier: str, kg_per_h_mill: float, heats_per_piece: float,
                 residence_h: float, piece: Piece) -> dict:
    """Furnace sized to keep pace with the mill while it runs (campaign working);
    the annual tonnage sets how many hours the line must run."""
    tonnes, hours, basis = TIERS[tier]
    if hours is None:
        load_kg = tonnes * 1000.0
        rate = load_kg / PILOT_HEAT_H
        shifts_note = (f"one {load_kg:.0f} kg charge heated in ~{PILOT_HEAT_H:g} h; later "
                       "pieces wait at temperature (extra scale)")
    else:
        rate = kg_per_h_mill
        load_kg = rate * residence_h
        need_h = tonnes * 1000.0 / kg_per_h_mill
        shifts_note = (f"{need_h:.0f} h/yr of running at the slowest conversion's pace = "
                       f"{100 * need_h / hours:.0f} % of the {hours:.0f} h available")
    footprint = piece.length_mm * piece.width_mm * 1e-6
    area = load_kg / piece.mass_kg * footprint / HEARTH_PACKING
    energy_kwh_kg = STEEL_ENTHALPY_KJ_KG_1200 / 3600.0 * (1 + 0.35 * (heats_per_piece - 1))
    kw = [rate * energy_kwh_kg / e for e in FURNACE_EFFICIENCY]
    return {"tier": tier, "basis": basis, "throughput_kg_h": rate, "hearth_load_kg": load_kg,
            "hearth_area_m2": area, "firing_kw_range": (min(kw), max(kw)), "note": shifts_note}


# ---------------------------------------------------------------------------
# 12. S1 EQUIPMENT SIZING
# ---------------------------------------------------------------------------
MOTOR_SYNC_RPM = 1000.0          # 6-pole, 50 Hz (FACT for the synchronous speed)
MOTOR_RATED_RPM = 985.0          # ESTIMATE rated slip
VFD_OVERLOAD = 1.5               # ESTIMATE heavy-duty VFD 150 % for 60 s (generic rating)
FORCE_MARGIN = (1.3, 1.5)        # ASSUMPTION bearing/frame margin over envelope peak
IEC_MOTOR_KW = (30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 250, 315, 355, 400)
R20 = (1.00, 1.12, 1.25, 1.40, 1.60, 1.80, 2.00, 2.24, 2.50, 2.80, 3.15, 3.55, 4.00,
       4.50, 5.00, 5.60, 6.30, 7.10, 8.00, 9.00)


def nearest_r20(x: float) -> float:
    cands = [r * 10 ** k for k in range(0, 3) for r in R20]
    return min(cands, key=lambda c: abs(math.log(c / x)))


def next_iec_kw(kw: float) -> float:
    for s in IEC_MOTOR_KW:
        if s >= kw:
            return float(s)
    return float(math.ceil(kw / 50.0) * 50)


def s1_envelope(finish_temps=FINISH_TEMPS_C) -> list[Run]:
    """All S1 runs spanning D, speed, mu, grade, finishing limit and schedule kind."""
    sc = SCENARIOS["S1"]
    runs = []
    for d in (sc.roll_d_range[0], sc.roll_d_mm, sc.roll_d_range[1]):
        for v in (sc.speed_range[0], sc.speed_m_s, sc.speed_range[1]):
            for mu in MU_RANGE:
                for g in GRADES:
                    for tf in finish_temps:
                        for kind in ("brief", "recommended"):
                            for pk, t in CONVERSIONS:
                                runs.append(simulate(pk, t, "S1", kind, g, mu,
                                                     Thermal(finish_min_c=tf),
                                                     roll_d_mm=d, speed_m_s=v))
    return runs


def s1_sizing(envelope: list[Run]) -> dict:
    """[RDR] ranges for S1 from the envelope. Per roll diameter."""
    out = {}
    eta = ETA_GEARBOX ** 2 * ETA_PINION * ETA_SPINDLE
    sf = total_service_factor()
    for d in sorted({r.roll_d_mm for r in envelope}):
        rs = [r for r in envelope if r.roll_d_mm == d]
        f_peak = max(r.peak("force_n") for r in rs)
        t_peak = max(r.peak("torque_total_nm") for r in rs)
        t_rms = max(r.rms_torque_total_nm for r in rs)
        p_peak = max(r.peak("power_kw") for r in rs)
        drive = {}
        for v_top in (0.6, 1.0):
            n_roll = roll_rpm(v_top, diameter_mm=d)
            ratio = nearest_r20(MOTOR_RATED_RPM / n_roll)
            t_motor_peak = t_peak / (ratio * eta)
            t_motor_rated = max(t_motor_peak / VFD_OVERLOAD, t_rms / (ratio * eta))
            kw = t_motor_rated * 2 * math.pi * MOTOR_RATED_RPM / 60.0 / 1000.0
            drive[v_top] = {"ratio_exact": MOTOR_RATED_RPM / n_roll, "ratio_r20": ratio,
                            "motor_peak_nm": t_motor_peak, "motor_rated_nm": t_motor_rated,
                            "motor_kw_min": kw, "motor_kw_iec": next_iec_kw(kw)}
        gearbox_out = max(t_rms * sf, t_peak * BITE_SHOCK_RANGE[1] / GEARBOX_PEAK_ALLOWANCE,
                          t_peak)
        longest = max(r.final.exit_len_mm for r in rs)
        widest = max(max(p.exit_b for p in r.passes) for r in rs)
        out[d] = {"force_peak_n": f_peak,
                  "force_rating_n": (f_peak * FORCE_MARGIN[0], f_peak * FORCE_MARGIN[1]),
                  "torque_total_peak_nm": t_peak, "torque_total_rms_nm": t_rms,
                  "power_peak_kw": p_peak, "drive": drive,
                  "gearbox_output_rating_nm": gearbox_out,
                  "longest_piece_mm": longest, "widest_mm": widest,
                  "table_each_side_m": longest / 1000.0 * 1.15 + 0.5,
                  "neck_stress_peak_mpa": max(r.peak("neck_stress_mpa") for r in rs),
                  "crown_peak_mm": max(r.peak("gap_crown_mm") for r in rs)}
    return out


def gauge_tolerance(run: Run, temp_spread_c: float | None = None) -> dict:
    """Within-piece thickness spread from the finishing pass. dF from the
    head-to-tail temperature difference (cooling during the pass itself, or a
    given spread), divided by the mill modulus, plus gap crown and an assumed
    manual setting repeatability. ESTIMATE; the real figure is [SM]."""
    sc = SCENARIOS[run.scenario]
    f = run.final
    dt = temp_spread_c if temp_spread_c is not None else (
        piece_cooling_rate_c_per_s(f.exit_h, f.exit_b, f.exit_len_mm, f.entry_temp_c,
                                   run.thermal.emissivity) * f.rolling_time_s)
    m_hot = pass_mechanics(f.entry_h, f.exit_h, f.entry_b, f.entry_temp_c,
                           run.roll_d_mm, run.speed_m_s, run.mu, run.grade)
    m_cold = pass_mechanics(f.entry_h, f.exit_h, f.entry_b, f.entry_temp_c - dt,
                            run.roll_d_mm, run.speed_m_s, run.mu, run.grade)
    df = m_cold["force"] - m_hot["force"]
    k_lo, k_hi = sc.mill_modulus_mn_mm
    setting = (0.05, 0.10)   # ASSUMPTION manual screw-down repeatability, mm
    wedge = (stand_stretch_mm(df, k_hi), stand_stretch_mm(df, k_lo))
    return {"head_tail_dT_c": dt, "dF_n": df, "wedge_mm": wedge, "crown_mm": f.gap_crown_mm,
            "setting_mm": setting,
            "spread_total_mm": (wedge[0] + f.gap_crown_mm + setting[0],
                                wedge[1] + f.gap_crown_mm + setting[1]),
            "stretch_mm": (f.stretch_mm_high_modulus, f.stretch_mm_low_modulus)}


# ---------------------------------------------------------------------------
# 13. COLD ROUTE (S4)
# ---------------------------------------------------------------------------
# Swift hardening sigma = K (eps0 + eps)^n. S235: K, n from the textbook values
# for annealed low-carbon (1020-type) steel, K = 530 MPa, n = 0.26 (Kalpakjian &
# Schmid, Manufacturing Engineering and Technology, Table 2.3) - ESTIMATE,
# recalled, not re-fetched. S355: K = 760 MPa, n = 0.18 - ASSUMPTION.
# eps0 is set so sigma(0) equals the nominal yield (235 / 355 MPa).
COLD_HARDENING = {"S235JR": (530.0, 0.26, 235.0), "S355JR": (760.0, 0.18, 355.0)}
MU_COLD = 0.08            # ASSUMPTION lubricated cold rolling (0.05-0.12)
HITCHCOCK_C = 16.0 * (1 - 0.3 ** 2) / (math.pi * 210000.0)   # mm2/N, E=210 GPa
LAMBDA_COLD = 0.45        # ASSUMPTION torque arm factor, cold


def cold_flow_stress_mpa(eq_strain: float, grade: str = "S235JR") -> float:
    k, n, sy = COLD_HARDENING[grade]
    eps0 = (sy / k) ** (1.0 / n)
    return k * (eps0 + max(eq_strain, 0.0)) ** n


def cold_schedule(h0: float, hf: float, width_mm: float, roll_d_mm: float,
                  grade: str = "S235JR", mu: float = MU_COLD, speed_m_s: float = 0.3,
                  max_reduction: float = 0.25, utilisation: float = 0.85) -> dict:
    """Pass sequence limited by bite at mu (x utilisation) and max_reduction.
    Force with Hitchcock-flattened radius, friction-hill Q, Swift hardening.
    No strip tension (plates). ESTIMATE."""
    if not 0 < hf < h0:
        raise ValueError("need 0 < hf < h0")
    cap = bite_limit_mm(mu, roll_d_mm, utilisation)
    h, b, passes = h0, width_mm, []
    r = roll_d_mm / 2.0
    while h > hf + 1e-9:
        d = min(cap, max_reduction * h, h - hf)
        h1 = h - d
        e_in = 2.0 / math.sqrt(3.0) * math.log(h0 / h)
        e_out = 2.0 / math.sqrt(3.0) * math.log(h0 / h1)
        k = 2.0 / math.sqrt(3.0) * (cold_flow_stress_mpa(e_in, grade)
                                    + cold_flow_stress_mpa(e_out, grade)) / 2.0
        r_f = r
        for _ in range(50):
            lc = math.sqrt(r_f * d)
            q = 1.0 + mu * lc / (2.0 * (h + h1) / 2.0)
            f_w = q * k * lc                      # N per mm width
            r_new = r * (1.0 + HITCHCOCK_C * f_w / d)
            if abs(r_new - r_f) < 1e-6 * r:
                r_f = r_new
                break
            r_f = r_new
        lc = math.sqrt(r_f * d)
        force = f_w * b
        torque_total = 2.0 * force * LAMBDA_COLD * math.sqrt(r * d) / 1000.0
        rpm = roll_rpm(speed_m_s, diameter_mm=roll_d_mm)
        passes.append({"entry_h": h, "exit_h": h1, "draft": d, "k_mpa": k,
                       "flattened_r_mm": r_f, "force_n": force,
                       "torque_total_nm": torque_total,
                       "power_kw": torque_total * 2 * math.pi * rpm / 60.0 / 1000.0,
                       "bite_ok": bite_ok(d, roll_d_mm, mu, utilisation)})
        h = h1
    return {"h0": h0, "hf": hf, "reduction_pct": reduction_pct(h0, hf),
            "roll_d_mm": roll_d_mm, "passes": passes, "n_passes": len(passes),
            "peak_force_n": max(p["force_n"] for p in passes),
            "peak_torque_nm": max(p["torque_total_nm"] for p in passes),
            "peak_power_kw": max(p["power_kw"] for p in passes),
            "final_flow_stress_mpa": cold_flow_stress_mpa(
                2.0 / math.sqrt(3.0) * math.log(h0 / hf), grade)}


# ---------------------------------------------------------------------------
# 14. INPUT REGISTER
# ---------------------------------------------------------------------------
INPUT_REGISTER = [
    # (name, value, unit, class, source, sensitivity)
    ("Piece A L x W x T", "500 x 250 x 12", "mm", "ASSUMPTION",
     "brief s2 (cm/mm units assumed; dimensions a CLAIM of the owner)",
     "linear on mass, lengths, capacity; thickness sets the conversion"),
    ("Piece B L x W x T", "400 x 300 x 20", "mm", "ASSUMPTION", "brief s2", "as A"),
    ("Piece C L x W x T", "700 x 200 x 15", "mm", "ASSUMPTION", "brief s2", "as A"),
    ("Number of pieces / tonnage", "unknown", "-", "UNKNOWN", "control doc HP-01",
     "decides pilot vs workshop vs industrial economics"),
    ("Photo (ChatGPT's description): 5 pieces, 3 dimension groups", "-", "-",
     "CLAIM (superseded by the photo itself)", "brief s3", "-"),
    ("Photo received 2026-09-28: 4 pieces visible", 4, "pieces", "MEASUREMENT (count only)",
     "docs/reroll/evidence/PHOTO_pieces_2026-09-28.jpg", "contradicts the brief's 5; kept side by side"),
    ("Photo: plan aspect ratio L/W of the 4 pieces", "1.75-2.44", "-",
     "ESTIMATE (pixel measurement, unscaled, slight perspective)", "evidence/PHOTO_NOTES",
     "fits group A (2.0); B (1.33) and C (3.5) are not visible [SM]"),
    ("Density", 7850, "kg/m3", "ASSUMPTION", "brief s2", "linear on mass"),
    ("Grade", "S235JR nominal, S355JR bound", "-", "ASSUMPTION", "brief s2, HP-02",
     "flow stress x1.15 for S355 (UNSOURCED multiplier) -> force/torque +15 %"),
    ("Targets", "6 / 8 / 10", "mm", "FACT (owner requirement)", "brief s1", "-"),
    ("Hot friction mu", "0.25-0.35 (0.30 nominal)", "-", "ASSUMPTION",
     "validation memo #1 (CONSISTENT); bite checked at 0.25", "bite not binding in S1-S3; "
     "force +/- ~4-6 % across the range"),
    ("Flow stress fit (imported)", "A=2586, beta=0.00307, m=0.13, n=0.15", "MPa",
     "ESTIMATE (anchors UNSOURCED)", "slab_line_design.py; validation memo #14",
     "force, torque and power scale linearly; below 900 C it is an extrapolation"),
    ("S355 flow-stress multiplier", 1.15, "-", "ESTIMATE (UNSOURCED)",
     "slab_line_design.GRADES; memo #15", "linear on all loads"),
    ("Plane-strain factor", "2/sqrt(3) blended b/h 1..5", "-", "FACT (mechanics)",
     "memo #19", "+15 % on loads for b/h >= 5 (all passes here)"),
    ("Geometry factor Q_p", "0.8+0.2L/h (L/h<1); 1+muL/2h", "-", "ESTIMATE",
     "memo #17 (CONSISTENT)", "L/h 1.5-4 here -> Q_p 1.2-1.6"),
    ("Torque arm lambda", LAMBDA_ARM, "-", "ESTIMATE (EDGE)", "memo #2", "linear on torque, power"),
    ("Bearing friction", MU_BEARING, "-", "ASSUMPTION (UNSOURCED)", "memo #3",
     "< 5 % of torque"),
    ("Wusatowski spread", "w=10^(-1.269 (b/h)(h/D)^0.556)", "-", "ESTIMATE (+/-10-20 %)",
     "memo #16", "gives < 0.1 % here (b/h 10-35, h/D < 0.06); real edge bulge a few mm [SM]"),
    ("Emissivity", "0.85 (0.75-0.90)", "-", "ESTIMATE (EDGE)",
     "memo #5: scale 0.85-0.89", "reheat count; see report sensitivity"),
    ("Specific heat cp", CP, "J/kg.K", "ESTIMATE", "memo #6", "linear on cooling rate"),
    ("Convection h", H_CONV, "W/m2.K", "ESTIMATE", "memo #9", "minor vs radiation"),
    ("Ambient", round(AMBIENT_C, 1), "C", "ASSUMPTION", "imported T_AMB_K", "minor"),
    ("Roll-gap heat transfer h_gap", "15000 (10000-30000)", "W/m2.K", "ASSUMPTION",
     "order of magnitude commonly reported for hot rolling (not pinned to a source)",
     "roll chill ~14-22 C/pass at 15 kW/m2K, ~25-37 C at 30 kW/m2K; B 20->6 gains a reheat at 30"),
    ("Roll surface temperature", ROLL_SURFACE_C, "C", "ASSUMPTION", "uncooled small mill",
     "weak (enters as T - T_roll)"),
    ("Deformation heat fraction", ETA_DEFORMATION_HEAT, "-", "ESTIMATE",
     "Taylor-Quinney ~0.9 (textbook)", "+4-10 C per pass"),
    ("First heat piece temperature", "1200 (1150-1250)", "C", "ESTIMATE",
     "see THERMAL_SOURCE_NOTE (ASM Handbook Vol. 14A, recalled)",
     "first-pass force -8/+9 % for +/-50 C; scale 2.2-3.1 % (B)"),
    ("Reheat piece temperature", 1150, "C", "ASSUMPTION", "lower bound to limit scale",
     "passes per reheat"),
    ("Overheating onset", OVERHEATING_ONSET_C, "C", "ESTIMATE", "see THERMAL_SOURCE_NOTE",
     "hard limit for furnace set point"),
    ("Burning onset", BURNING_ONSET_C, "C", "ESTIMATE", "see THERMAL_SOURCE_NOTE",
     "irreversible; furnace overshoot protection"),
    ("Minimum finishing temperature", "800 / 850 / 880", "C", "HYPOTHESIS (Ar3 EDGE)",
     "memo #30: two sources differ by ~200 C", "reheat count 0-2 per conversion"),
    ("Furnace margin above target", FURNACE_MARGIN_C, "C", "ASSUMPTION", "-",
     "heating time"),
    ("Furnace effective emissivity", EPS_FURNACE_EFF, "-", "ASSUMPTION", "-",
     "heating time +/- 20-30 %"),
    ("First-heat soak", "600 (300-900)", "s", "ASSUMPTION [RDR]",
     "equalisation; Bi < 0.1 so through-thickness gradient is small", "scale, furnace size"),
    ("Scale law", "kp = 0.37 exp(-138 kJ/RT) g2/cm4/s", "-", "ESTIMATE",
     "Paidassi (1958) as quoted in Chen & Yuen 2003 review; recalled", "scale loss"),
    ("Scale kp factor", "0.5 / 0.8 / 1.2", "-", "ASSUMPTION", "atmosphere, chemistry",
     "scale loss ~ sqrt(factor): 2.1-3.2 / 2.6-4.0 / 3.2-5.0 % per piece, one heat"),
    ("Irregular end per end (average over all ends)", "5 / 15 / 30", "mm", "ASSUMPTION [SM]",
     "photo description (CLAIM): SOME ends rounded/conical", "crop 2.5-5 / 7-13 / 13-24 % of "
     "input (low/nominal/high, incl. tongue)"),
    ("Tongue/fishtail per end", "10 / 25 / 40 at >= 50 % reduction, pro rata below", "mm",
     "ASSUMPTION", "-", "part of the crop figures above"),
    ("Edge trim per side", "0 / 5 / 12", "mm", "ASSUMPTION", "HP-03 (product spec)",
     "trim loss 0 / 3-4.5 / 6-10 % of input"),
    ("Out-of-tolerance fraction", "2 / 5 / 10", "%", "ASSUMPTION", "manual mill pilot",
     "linear on yield"),
    ("S1 roll diameter", "400 (350-450)", "mm", "ASSUMPTION [RDR]", "task scenario S1",
     "force ~ sqrt(D); torque ~ D"),
    ("S1 barrel", "550 (500-600)", "mm", "ASSUMPTION [RDR]", "task scenario S1",
     "must exceed exit width + margin"),
    ("S1 speed", "0.6 (0.3-1.0)", "m/s", "ASSUMPTION", "task scenario S1",
     "power ~ v; at 0.3 m/s longer contact chill adds a reheat on A and B 6 mm"),
    ("S1 interpass time", "8 (5-12)", "s", "ASSUMPTION [SM]", "manual/semi-auto handling",
     "B 20->6 last-pass force 1.29-1.55 MN; reheats under the cold-side set"),
    ("S1 furnace-to-bite transfer", "20 (12-40)", "s", "ASSUMPTION [SM]", "-",
     "40 s adds a reheat on A 12->6 and +17 % force on B 20->6"),
    ("S1 bearing offset", 150, "mm", "ASSUMPTION", "~0.375 D", "neck stress, crown"),
    ("Neck/barrel diameter ratio", 0.55, "-", "ASSUMPTION (UNSOURCED)", "memo #10",
     "neck stress ~ d^-3"),
    ("S1 mill modulus", "0.5-1.5", "MN/mm", "ASSUMPTION [SM]", "small stand; measure by "
     "closed-roll test", "thickness spread and absolute gauge"),
    ("S1 max reduction / last pass", "30 % / 20 %", "-", "ASSUMPTION [RDR]",
     "conventional hot flat practice", "pass count"),
    ("Bite utilisation", 0.85, "-", "ASSUMPTION", "margin on exact bite limit", "-"),
    ("Handling overhead per piece", HANDLING_OVERHEAD_S, "s", "ASSUMPTION [SM]", "-",
     "capacity"),
    ("Mill utilisation", "0.65 (0.5-0.8)", "-", "ASSUMPTION", "manual crew", "capacity linear"),
    ("VFD overload", VFD_OVERLOAD, "x", "ESTIMATE", "generic heavy-duty VFD rating 150 %/60 s",
     "motor kW ~ 1/overload"),
    ("Drive efficiencies", "gear 0.97/stage, pinion 0.98, spindle 0.99", "-", "ESTIMATE",
     "memo #20", "minor"),
    ("Gearbox service factor", round(total_service_factor(), 3), "-", "ASSUMPTION",
     "slab_line_design.SERVICE_FACTORS; memo #21-22 EDGE", "gearbox rating linear"),
    ("Bite shock", "2-3 x steady torque", "-", "ASSUMPTION (UNSOURCED)", "memo #24",
     "gearbox peak criterion"),
    ("Force margin (bearings/frame)", "1.3-1.5", "-", "ASSUMPTION", "-", "rating"),
    ("Option C stand", "D600 x 600, up to 3 m/s", "-", "UNKNOWN status",
     "control doc: not operational, not recorded as owned", "verdict"),
    ("Option C furnace", "20 t/h walking beam, 1250 C, 1.2 t slabs", "-", "ASSUMPTION "
     "(design basis of the other project)", "control doc; RFI draft only", "verdict"),
    ("Option C rating proxy", f"{_SLD_FORCE_N / 1e6:.2f} MN / {_SLD_TORQUE_NM / 1e3:.0f} kN.m", "-",
     "ESTIMATE (model design duty, not a rating)",
     "slab_line_design worst_cases over 6-30 mm, balanced, S355JR (= stand RFI basis)", "force fraction"),
    ("S3 toll-mill class", "D500-1000, barrel 800-2500, 0.5-3 m/s, >=5 MN", "-",
     "ASSUMPTION", "task scenario S3", "acceptance of short pieces is the risk"),
    ("Cold hardening S235", "K=530 MPa, n=0.26", "-", "ESTIMATE",
     "Kalpakjian & Schmid Table 2.3 (1020 annealed), recalled", "cold force linear"),
    ("Cold hardening S355", "K=760 MPa, n=0.18", "-", "ASSUMPTION", "-", "cold force"),
    ("Cold friction", "0.08 (0.05-0.12)", "-", "ASSUMPTION", "lubricated", "passes ~ 1/mu^2"),
    ("Cold torque arm", LAMBDA_COLD, "-", "ASSUMPTION", "-", "cold torque linear"),
    ("Hitchcock constant", f"{HITCHCOCK_C:.3e}", "mm2/N", "FACT (elastic formula, E 210 GPa, "
     "nu 0.3)", "Hitchcock roll flattening", "cold force +5-20 %"),
    ("Cold max reduction per pass", "25 %", "-", "ASSUMPTION", "-", "cold pass count"),
    ("Cold mills evaluated", "two-high D400; four-high work roll D180", "mm", "ASSUMPTION",
     "task scenario S4", "passes ~ 1/D; force ~ sqrt(D)"),
    ("Young's modulus (roll)", E_STEEL_MPA, "MPa", "ESTIMATE", "memo #4", "crown only"),
    ("Shear modulus (roll)", G_ROLL_MPA, "MPa", "ESTIMATE", "handbook order", "crown only"),
    ("Timoshenko shear coefficient", KAPPA_ROUND, "-", "ESTIMATE", "solid round section",
     "crown only"),
    ("Roll conductivity / cp", f"{K_ROLL:g} / {CP_ROLL:g}", "W/m.K / J/kg.K", "ASSUMPTION",
     "roll steel near 150 C", "roll-chill cap only"),
    ("Stock conductivity", K_STOCK, "W/m.K", "ESTIMATE", "memo #7", "chill cap, Biot"),
    ("Furnace efficiency (small batch)", "0.20-0.35", "-", "ASSUMPTION", "-",
     "firing kW ~ 1/eff"),
    ("Steel enthalpy 20->1200 C", STEEL_ENTHALPY_KJ_KG_1200, "kJ/kg", "ESTIMATE",
     "generic thermophysical data incl. alpha-gamma", "firing kW linear"),
    ("Hearth packing", HEARTH_PACKING, "-", "ASSUMPTION", "single layer with gaps",
     "hearth area ~ 1/packing"),
    ("Pilot charge heat time", PILOT_HEAT_H, "h", "ASSUMPTION", "slow low-power chamber furnace",
     "pilot firing kW"),
    ("Tier hours available", "workshop 2000; industrial 4000", "h/yr", "ASSUMPTION",
     "1 and 2 shifts x 250 d", "shift count needed"),
    ("Motor speed", "985 rpm (6-pole, 50 Hz)", "rpm", "ESTIMATE", "synchronous 1000 rpm FACT",
     "gear ratio"),
    ("IEC motor sizes", "30-400 kW series", "kW", "FACT (standard series, IEC 60072)", "-",
     "rounding only"),
    ("Option C table roller pitch", "600-1000", "mm", "ASSUMPTION [SM]", "heavy slab table",
     "short-piece conveyance"),
    ("Option C furnace fuel", "1.2-1.6 GJ/t full rate; 20-30 % to hold", "-", "ESTIMATE / "
     "ASSUMPTION", "typical reheating furnace", "idle energy per kg"),
    ("Option C min threading speed", 0.8, "m/s", "ASSUMPTION", "slab_line_design v_first",
     "chill, rolling time"),
]


# ---------------------------------------------------------------------------
# 15. STUDY ASSEMBLY
# ---------------------------------------------------------------------------
def s1_nominal(kind: str = "recommended", finish_c: float = FINISH_NOMINAL_C,
               grade: str = "S235JR") -> dict:
    return {(pk, t): simulate(pk, t, "S1", kind, grade, MU_NOMINAL, Thermal(finish_min_c=finish_c))
            for pk, t in CONVERSIONS}


def thermal_band_reheats(pk: str, t: float, kind: str, finish_c: float) -> tuple[int, int]:
    """Reheat count under a hot-side and a cold-side thermal parameter set."""
    hot = Thermal(finish_min_c=finish_c, emissivity=EMISSIVITY_RANGE[0], h_gap=H_GAP_RANGE[0],
                  interpass_s=SCENARIOS["S1"].interpass_range[0], transfer_s=12.0,
                  first_heat_c=1250.0, reheat_c=1200.0)
    cold = Thermal(finish_min_c=finish_c, emissivity=EMISSIVITY_RANGE[1], h_gap=H_GAP_RANGE[1],
                   interpass_s=SCENARIOS["S1"].interpass_range[1], transfer_s=40.0,
                   first_heat_c=1150.0, reheat_c=1150.0)
    r_hot = simulate(pk, t, "S1", kind, "S235JR", MU_NOMINAL, hot)
    r_cold = simulate(pk, t, "S1", kind, "S355JR", MU_NOMINAL, cold)
    return r_hot.reheats, r_cold.reheats


def time_to_limit_s(h: float, b: float, length: float, start_c: float, limit_c: float,
                    emissivity: float = EMISSIVITY_NOMINAL) -> float:
    t, temp = 0.0, start_c
    while temp > limit_c and t < 3600.0:
        temp = cool_piece(temp, h, b, length, 0.5, emissivity)
        t += 0.5
    return t


def option_c(s1_runs: dict) -> dict:
    sc = SCENARIOS["S2"]
    runs = {(pk, t): simulate(pk, t, "S2", "recommended", "S355JR", MU_RANGE[1],
                              Thermal(finish_min_c=FINISH_NOMINAL_C))
            for pk, t in CONVERSIONS}
    f_peak = max(r.peak("force_n") for r in runs.values())
    t_peak = max(r.peak("torque_total_nm") for r in runs.values())
    p_peak = max(r.peak("power_kw") for r in runs.values())
    shortest = min(p.length_mm for p in PIECES.values())
    longest = max(r.final.exit_len_mm for r in runs.values())
    reheats = {k: r.reheats for k, r in runs.items()}
    piece_masses = [p.mass_kg for p in PIECES.values()]
    slab_mass = 0.400 * 0.125 * 3.0 * RHO
    rated_tph = 20.0
    full_fuel_gj_t = (1.2, 1.6)            # ESTIMATE typical reheating furnace
    hold_fraction = (0.20, 0.30)           # ASSUMPTION hold/idle fuel as fraction of full
    hold_mw = (rated_tph * full_fuel_gj_t[0] * hold_fraction[0] / 3.6,
               rated_tph * full_fuel_gj_t[1] * hold_fraction[1] / 3.6)
    tiers = {}
    for name, (tonnes, hours, _) in TIERS.items():
        rate_tph = (tonnes / hours) if hours else 0.1 / 1.0
        tiers[name] = {"rate_tph": rate_tph, "fraction_of_rated": rate_tph / rated_tph,
                       "hold_kwh_per_kg": (hold_mw[0] * 1000 / (rate_tph * 1000),
                                           hold_mw[1] * 1000 / (rate_tph * 1000))}
    stretch = (stand_stretch_mm(f_peak, sc.mill_modulus_mn_mm[1]),
               stand_stretch_mm(f_peak, sc.mill_modulus_mn_mm[0]))
    s1_force = max(r.peak("force_n") for r in s1_runs.values())
    nominal = [simulate(pk, t, "S2", "recommended", "S235JR", MU_NOMINAL,
                        Thermal(finish_min_c=FINISH_NOMINAL_C)) for pk, t in CONVERSIONS]
    f_nom = max(r.peak("force_n") for r in nominal)
    return {"runs": runs, "force_peak_n": f_peak, "force_fraction": f_peak / sc.force_rating_n,
            "torque_peak_nm": t_peak, "torque_fraction": t_peak / sc.torque_rating_nm,
            "power_peak_kw": p_peak, "power_fraction_of_1600kw": p_peak / 1600.0,
            "time_at_3ms_s": {k: p.length_mm / 3000.0 for k, p in PIECES.items()},
            "time_at_08ms_s": {k: p.length_mm / 800.0 for k, p in PIECES.items()},
            "shortest_piece_mm": shortest, "longest_exit_mm": longest,
            "table_pitch_assumed_mm": (600.0, 1000.0),
            "pieces_per_slab_mass": (slab_mass / max(piece_masses), slab_mass / min(piece_masses)),
            "slab_mass_kg": slab_mass, "piece_len_vs_slab": (shortest / 3000.0, 700.0 / 3000.0),
            "hold_mw": hold_mw, "tiers": tiers, "min_unloaded_gap_mm": (6.0 - stretch[1], 6.0 - stretch[0]),
            "stretch_mm": stretch, "reheats": reheats, "s1_force_peak_n": s1_force,
            "force_peak_nominal_n": f_nom,
            "bite_util_max": max(p.draft / max_draft_bite_exact_mm(MU_RANGE[0], roll_diameter_mm=600.0)
                                 for r in runs.values() for p in r.passes)}


def option_s3() -> dict:
    sc = SCENARIOS["S3"]
    out = {}
    for d in (sc.roll_d_range[0], sc.roll_d_mm, sc.roll_d_range[1]):
        runs = [simulate(pk, t, "S3", "recommended", "S355JR", MU_RANGE[1],
                         Thermal(finish_min_c=FINISH_NOMINAL_C), roll_d_mm=d)
                for pk, t in CONVERSIONS]
        out[d] = {"force_peak_n": max(r.peak("force_n") for r in runs),
                  "torque_peak_nm": max(r.peak("torque_total_nm") for r in runs),
                  "reheats_max": max(r.reheats for r in runs),
                  "passes": {r.conversion: len(r.passes) for r in runs}}
    return out


def cold_route() -> dict:
    out = {}
    for label, d, b in (("two-high D400", 400.0, None), ("four-high WR D180", 180.0, None)):
        for h0, width in ((20.0, 300.0), (12.0, 250.0)):
            for red in (0.5, 0.6, 0.7):
                for g in GRADES:
                    hf = round(h0 * (1 - red), 2)
                    out[(label, h0, red, g)] = cold_schedule(h0, hf, width, d, g)
    return out


def sensitivity() -> list[tuple]:
    """One-at-a-time sensitivities around S1 nominal (B 20->6 and A 12->6, recommended)."""
    rows = []
    base_b = simulate("B", 6.0, "S1", "recommended", "S235JR", MU_NOMINAL, Thermal())
    base_a = simulate("A", 6.0, "S1", "recommended", "S235JR", MU_NOMINAL, Thermal())

    def row(name, rb, ra):
        rows.append((name, rb.peak("force_n") / 1e6, rb.peak("torque_total_nm") / 1e3,
                     rb.reheats, ra.reheats,
                     100 * yield_breakdown(rb)["scale_pct"] / 100,
                     100 * yield_breakdown(rb)["yield"]))
    row("baseline (D400, v0.6, mu0.30, S235, Tfin 850, eps 0.85)", base_b, base_a)
    for mu in MU_RANGE:
        row(f"mu = {mu}", simulate("B", 6.0, "S1", grade="S235JR", mu=mu),
            simulate("A", 6.0, "S1", grade="S235JR", mu=mu))
    row("grade S355JR", simulate("B", 6.0, "S1", grade="S355JR"),
        simulate("A", 6.0, "S1", grade="S355JR"))
    for e in EMISSIVITY_RANGE:
        row(f"emissivity {e}", simulate("B", 6.0, "S1", thermal=Thermal(emissivity=e)),
            simulate("A", 6.0, "S1", thermal=Thermal(emissivity=e)))
    for hg in H_GAP_RANGE:
        row(f"h_gap {hg:.0f}", simulate("B", 6.0, "S1", thermal=Thermal(h_gap=hg)),
            simulate("A", 6.0, "S1", thermal=Thermal(h_gap=hg)))
    for ip in SCENARIOS["S1"].interpass_range:
        row(f"interpass {ip:.0f} s", simulate("B", 6.0, "S1", thermal=Thermal(interpass_s=ip)),
            simulate("A", 6.0, "S1", thermal=Thermal(interpass_s=ip)))
    for tr in (12.0, 40.0):
        row(f"transfer {tr:.0f} s", simulate("B", 6.0, "S1", thermal=Thermal(transfer_s=tr)),
            simulate("A", 6.0, "S1", thermal=Thermal(transfer_s=tr)))
    for fh in (1150.0, 1250.0):
        row(f"first heat {fh:.0f} C", simulate("B", 6.0, "S1", thermal=Thermal(first_heat_c=fh)),
            simulate("A", 6.0, "S1", thermal=Thermal(first_heat_c=fh)))
    for tf in FINISH_TEMPS_C:
        row(f"finish limit {tf:.0f} C", simulate("B", 6.0, "S1", thermal=Thermal(finish_min_c=tf)),
            simulate("A", 6.0, "S1", thermal=Thermal(finish_min_c=tf)))
    for d in SCENARIOS["S1"].roll_d_range:
        row(f"roll D {d:.0f}", simulate("B", 6.0, "S1", roll_d_mm=d),
            simulate("A", 6.0, "S1", roll_d_mm=d))
    for v in SCENARIOS["S1"].speed_range:
        row(f"speed {v} m/s", simulate("B", 6.0, "S1", speed_m_s=v),
            simulate("A", 6.0, "S1", speed_m_s=v))
    return rows


# ---------------------------------------------------------------------------
# 16. OUTPUT: CSV
# ---------------------------------------------------------------------------
CSV_FIELDS = ["scenario", "conversion", "schedule", "grade", "mu", "finish_min_c", "roll_d_mm",
              "speed_m_s"] + [f for f in PassRow.__dataclass_fields__]


def csv_rows() -> list[dict]:
    rows = []
    for sc_key in ("S1", "S2", "S3"):
        finishes = FINISH_TEMPS_C if sc_key == "S1" else (FINISH_NOMINAL_C,)
        for tf in finishes:
            for kind in ("brief", "recommended"):
                for pk, t in CONVERSIONS:
                    r = simulate(pk, t, sc_key, kind, "S235JR", MU_NOMINAL,
                                 Thermal(finish_min_c=tf))
                    for p in r.passes:
                        row = {"scenario": sc_key, "conversion": r.conversion, "schedule": kind,
                               "grade": r.grade, "mu": r.mu, "finish_min_c": tf,
                               "roll_d_mm": r.roll_d_mm, "speed_m_s": r.speed_m_s}
                        for k, val in asdict(p).items():
                            row[k] = round(val, 4) if isinstance(val, float) else val
                        rows.append(row)
    return rows


def write_csv(path: str) -> int:
    rows = csv_rows()
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


# ---------------------------------------------------------------------------
# 17. OUTPUT: INPUTS TABLE
# ---------------------------------------------------------------------------
def inputs_markdown() -> str:
    out = io.StringIO()
    w = out.write
    w(f"# Inputs and assumptions - {PROJECT_ID}\n\n")
    w(f"Generated by `reroll_study.py --inputs` on {STUDY_DATE}. Do not edit by hand; edit "
      "`INPUT_REGISTER` in `reroll_study.py` and regenerate.\n\n")
    w("Evidence classes follow the brief (s14): FACT, MEASUREMENT, SUPPLIER CLAIM, ESTIMATE, "
      "ASSUMPTION, HYPOTHESIS, UNKNOWN. 'CLAIM' marks the owner's or ChatGPT's unverified "
      "statements. [RDR] = recommended design range, [SM] = requires site measurement. "
      "Literature constants marked 'recalled' were not re-fetched in this session and must be "
      "checked against the primary source before any purchase decision.\n\n")
    w("No value here is an operating setpoint or a recipe.\n\n")
    w("| # | Input / constant | Value | Unit | Evidence class | Source | Sensitivity |\n")
    w("|---|---|---|---|---|---|---|\n")
    for i, (name, val, unit, cls, src, sens) in enumerate(INPUT_REGISTER, 1):
        w(f"| {i} | {name} | {val} | {unit} | {cls} | {src} | {sens} |\n")
    w("\nComputed sensitivities are in `ENGINEERING_CALCS_2026-09-28.md`, section 12.\n")
    return out.getvalue()


# ---------------------------------------------------------------------------
# 18. OUTPUT: REPORT
# ---------------------------------------------------------------------------
def _mn(x):
    return f"{x / 1e6:.2f}"


def _knm(x):
    return f"{x / 1e3:.1f}"


def build_report() -> str:
    out = io.StringIO()
    w = out.write
    s1 = s1_nominal("recommended")
    s1_brief = s1_nominal("brief")
    s1_by_tf = {tf: s1_nominal("recommended", tf) for tf in FINISH_TEMPS_C}
    s1_brief_by_tf = {tf: s1_nominal("brief", tf) for tf in FINISH_TEMPS_C}
    env = s1_envelope()
    sizing = s1_sizing(env)
    oc = option_c(s1)
    s3 = option_s3()
    cold = cold_route()
    sens = sensitivity()

    # headline numbers for the Persian summary
    max_force_env = max(v["force_peak_n"] for v in sizing.values())
    y_nom = {k: yield_breakdown(r)["yield"] for k, r in s1.items()}
    y_lo = {k: yield_breakdown(r, "high")["yield"] for k, r in s1.items()}
    y_hi = {k: yield_breakdown(r, "low")["yield"] for k, r in s1.items()}
    cap = {k: capacity(r) for k, r in s1.items()}
    kgph = [c["kg_per_h_input"] for c in cap.values()]
    d400 = sizing[400.0]
    bands = {(k, tf): thermal_band_reheats(*k, "recommended", tf)
             for k in CONVERSIONS for tf in FINISH_TEMPS_C}
    band_max = {tf: max(bands[(k, tf)][1] for k in CONVERSIONS) for tf in FINISH_TEMPS_C}
    reheats_nom = {tf: max(r.reheats for r in s1_by_tf[tf].values()) for tf in FINISH_TEMPS_C}
    changed = [(s1[k].conversion, len(s1_brief[k].passes), len(s1[k].passes))
               for k in CONVERSIONS if len(s1[k].passes) != len(s1_brief[k].passes)]
    cold_runs = {k: simulate(*k, "S1", "recommended", "S355JR", MU_NOMINAL, Thermal(
        finish_min_c=850.0, emissivity=EMISSIVITY_RANGE[1], h_gap=H_GAP_RANGE[1],
        interpass_s=12.0, transfer_s=40.0, first_heat_c=1150.0, reheat_c=1150.0))
        for k in CONVERSIONS}
    reheat_scale = [100 * (scale_metal_loss_kg(a, w2, KP_FACTOR["nominal"])
                           / PIECES[r.piece_key].mass_kg)
                    for r in cold_runs.values()
                    for a, w2 in list(zip(r.scale_area_per_heat, r.scale_w2_per_heat))[1:]]
    first_scale = [100 * scale_metal_loss_kg(r.scale_area_per_heat[0], r.scale_w2_per_heat[0],
                                             KP_FACTOR["nominal"]) / PIECES[r.piece_key].mass_kg
                   for r in s1.values()]
    loss_lo = 100 * (1 - max(y_hi.values()))
    loss_hi = 100 * (1 - min(y_lo.values()))

    w(f"# Engineering calculations - {PROJECT_ID} (re-rolling 12/15/20 mm pieces to 6/8/10 mm)\n\n")
    w(f"Generated by `python reroll_study.py --report ...` on {STUDY_DATE}. "
      "Every figure is a CONCEPT figure: [PC] preliminary concept unless marked [RDR] "
      "(recommended design range) or [SM] (requires site measurement). **Nothing here is an "
      "operating setpoint, a pass recipe or a purchase specification.** No vendor or third "
      "party was contacted.\n\n")

    w("## خلاصهٔ فارسی\n\n")
    w(f"- مسیر گرم روی استند کوچک دوغلتکه (S1، غلتک ~Ø۴۰۰) از نظر نیرو و Bite ممکن است: "
      f"Bite در هیچ پاسی محدودکننده نیست و پیک نیروی جدایش در کل بازهٔ فرض‌ها "
      f"~{max_force_env / 1e6:.1f} MN است [PC].\n")
    w(f"- محدودیت اصلی حرارتی است: قطعات ۱۲ تا ۱۹ کیلوگرمی ۵ تا ۱۵ °C/s سرد می‌شوند. "
      f"با فرض‌های اسمی (انتقال ۲۰ s، بین‌پاس ۸ s) و حد پایان نورد ۸۵۰ °C بازگرمایش "
      f"{reheats_nom[850.0]} است، ولی با فرض‌های بدبینانه تا {band_max[850.0]} بار "
      f"(و در ۸۸۰ °C تا {band_max[880.0]} بار) لازم می‌شود [PC].\n")
    w(f"- راندمان وزنی خالص قابل‌فروش (اسمی) {min(y_nom.values()) * 100:.0f} تا "
      f"{max(y_nom.values()) * 100:.0f}٪ و در بازهٔ بدبینانه تا خوش‌بینانه "
      f"{min(y_lo.values()) * 100:.0f} تا {max(y_hi.values()) * 100:.0f}٪ است؛ "
      f"پوستهٔ اکسیدی و سر و ته‌بری بیشترین پرت را دارند [PC].\n")
    w(f"- ظرفیت S1 با کار دستی حدود {min(kgph):.0f} تا {max(kgph):.0f} kg/h ورودی است [PC]؛ "
      f"موتور AC با VFD حدود {d400['drive'][0.6]['motor_kw_iec']:.0f} تا "
      f"{d400['drive'][1.0]['motor_kw_iec']:.0f} kW برای Ø۴۰۰ [RDR].\n")
    w(f"- گزینهٔ C (استند Ø۶۰۰ پروژهٔ دیگر) در دسترس نیست و عملیاتی نیست. اگر هم بود، نیرو "
      f"~{oc['force_fraction'] * 100:.0f}٪ و گشتاور ~{oc['torque_fraction'] * 100:.0f}٪ بار طراحی "
      f"تقریبی آن است (کسر ناچیز نیست)، و کورهٔ ۲۰ t/h و میز غلتکی برای قطعات ۰٫۴ تا ۰٫۷ متری "
      f"مناسب نیستند.\n")
    cold_passes = [c["n_passes"] for (lab, h0, red, g), c in cold.items() if h0 == 20.0 and red == 0.7]
    cold_f = [c["peak_force_n"] for (lab, h0, red, g), c in cold.items() if h0 == 20.0 and red == 0.7]
    w(f"- نورد سرد (S4) از نظر فنی ممکن ولی نامتناسب است: برای ۲۰→۶ حدود {min(cold_passes)} تا "
      f"{max(cold_passes)} پاس، نیروی {min(cold_f) / 1e6:.1f} تا {max(cold_f) / 1e6:.1f} MN، "
      "اسیدشویی و آنیل کامل. توصیه نمی‌شود.\n")
    w("- هیچ عددی دستور کار یا Setpoint نیست؛ پایلوت و اندازه‌گیری [SM] لازم است.\n\n")

    # 1 inputs
    w("## 1. Inputs and the brief's s4 table reproduced\n\n")
    w("Pieces (ASSUMPTION: cm for length/width, mm for thickness; brief s2). Density "
      f"{RHO:.0f} kg/m3 (ASSUMPTION). Grade S235JR nominal, S355JR bound (ASSUMPTION, HP-02). "
      "Full register: `docs/reroll/INPUTS_AND_ASSUMPTIONS.md`.\n\n")
    w("| Piece | L x W x T (mm) | Mass kg (model) | Mass kg (brief) |\n|---|---|---|---|\n")
    for k, p in PIECES.items():
        w(f"| {k} | {p.length_mm:g} x {p.width_mm:g} x {p.thickness_mm:g} | {p.mass_kg:.2f} | "
          f"{BRIEF_S4_MASS_KG[k]:.2f} |\n")
    w("\nTheoretical length, width constant, no spread, no losses: L_f = L_0 h_0 / h_f.\n\n")
    w("| Conversion | Reduction % | Length factor | L_f model (mm) | L_f brief (mm) | Match |\n")
    w("|---|---|---|---|---|---|\n")
    for pk, t in CONVERSIONS:
        p = PIECES[pk]
        lf = theoretical_length_mm(p, t)
        w(f"| {pk} {p.thickness_mm:g}->{t:g} | {reduction_pct(p.thickness_mm, t):.1f} | "
          f"{p.thickness_mm / t:.3f} | {lf:.1f} | {BRIEF_S4_LENGTH_MM[(pk, t)]} | "
          f"{'yes' if abs(lf - BRIEF_S4_LENGTH_MM[(pk, t)]) <= 0.5 else 'NO'} |\n")
    w("\nThe brief's s4 numbers are reproduced (its 1313 and 1333 are roundings of 1312.5 and "
      "1333.3). They are upper bounds: spread shortens the piece slightly and scale, crop and "
      "trim remove mass (sections 4 and 6).\n\n")

    # 2 models
    w("## 2. Models, formulas, constants, units and validity\n\n")
    w("| Quantity | Formula / model | Constants | Validity range and caveats |\n|---|---|---|---|\n")
    w("| Bite | exact: dh_max = D (1 - cos(arctan mu)); required mu = tan(alpha), "
      "cos(alpha) = 1 - dh/D | mu 0.25-0.35, checked at 0.25 x utilisation 0.85 | "
      "geometry, exact; mu itself is an ASSUMPTION |\n")
    w("| Contact length | L = sqrt(R dh) | - | hot: roll flattening neglected (<2 %) |\n")
    w("| Flow stress (hot) | sigma = A e^(-beta T) (edot/10)^m (eps/0.3)^n x grade x plane-strain "
      "factor | imported fit, anchors 900-1200 C at 10/s | anchors UNSOURCED; below 900 C an "
      "extrapolation; in the two-phase field below Ar3 the real value can differ either way; "
      "no strain accumulation between passes (full recrystallisation assumed) |\n")
    w("| Force | F = Q_p k b_m L; Q_p = 0.8 + 0.2 L/h (L/h<1), 1 + mu L/(2h) (L/h>=1) | "
      "mu 0.30 nominal | Ekelund/Sims-type; +/-15-20 % typical for this family |\n")
    w("| Torque | per roll T = F lambda L + mu_b F r_neck; total = 2 x per roll | lambda 0.48, "
      "mu_b 0.004 | hot flat rolling |\n")
    w("| Power | P = T_total omega | - | instantaneous at roll; RMS over the mill occupancy per "
      "piece |\n")
    w("| Spread | Wusatowski b1/b0 = (h0/h1)^w, w = 10^(-1.269 (b0/h0)(h0/D)^0.556) | - | "
      "empirical, +/-10-20 %; b/h 10-35 and h/D < 0.06 here, so it predicts < 0.1 % spread; "
      "real edge bulging of a few mm is likely and is [SM] |\n")
    w("| Air cooling | lumped radiation + convection, imported per-length rate x end-face "
      "correction | eps 0.85, h 15 W/m2K, cp 700 | lumped valid: Biot 0.01-0.05 (checked) |\n")
    w("| Roll chill | per face Q = min(h_gap dT t_c, 2 e_eff dT sqrt(t_c/pi)); dT_mean = 2Q/(rho "
      "cp h) | h_gap 15 kW/m2K, T_roll 150 C | replaces the imported fixed 8 C/contact, which "
      "was set for 125 mm stock |\n")
    w("| Deformation heat | dT = 0.9 p_mean eps / (rho cp) | - | adiabatic |\n")
    w("| Furnace heating | lumped radiation from walls at target+40 C, eps_eff 0.7 | soak 10 "
      "min first heat | ignores shading of stacked pieces and the rust layer [SM] |\n")
    w("| Scale | parabolic, w^2 = int kp dt, kp = 0.37 exp(-138 kJ/RT) g2/cm4/s (O uptake); metal "
      "= 3.49 x O | kp factor 0.5/0.8/1.2 | Paidassi iron-in-air, 700-1250 C; scale "
      "removed at each descale |\n")
    w("| Roll crown | simply supported roll, load spread over strip width, bending + "
      "Timoshenko shear; gap crown = 2 x per roll | E 200 GPa, G 80 GPa | no thermal crown, "
      "wear or ground camber [SM] |\n")
    w("| Stand stretch | F / M | M 0.5-1.5 MN/mm (S1) | M is [SM]: closed-roll test |\n")
    w("| Cold flow stress | Swift sigma = K (eps0 + eps)^n, eps0 from yield | S235 K 530, n 0.26 "
      "(ESTIMATE); S355 K 760, n 0.18 (ASSUMPTION) | cumulative plane-strain equivalent strain "
      "to ~1.4 |\n")
    w("| Cold force | Hitchcock flattened R', F = Q k b L', Q = 1 + mu L'/(2h) | mu 0.08 | no "
      "tension; Bland-Ford would be more exact |\n\n")
    w("Units: mm, C, N (MN in tables), N.m (kN.m), kW, s, kg.\n\n")

    # 3 scenarios
    w("## 3. Route / equipment scenarios (data)\n\n")
    w("| Key | Scenario | D (mm) | Barrel (mm) | Speed (m/s) | Reversing | Interpass (s) | "
      "Reheat policy | Status |\n|---|---|---|---|---|---|---|---|---|\n")
    for sc in SCENARIOS.values():
        rev = {True: "yes", False: "no", None: "UNKNOWN"}[sc.reversing]
        w(f"| {sc.key} | {sc.label} | {sc.roll_d_mm:g} ({sc.roll_d_range[0]:g}-"
          f"{sc.roll_d_range[1]:g}) | {sc.barrel_mm:g} ({sc.barrel_range[0]:g}-"
          f"{sc.barrel_range[1]:g}) | {sc.speed_m_s:g} ({sc.speed_range[0]:g}-"
          f"{sc.speed_range[1]:g}) | {rev} | {sc.interpass_s:g} | {sc.reheat_policy} | "
          f"{sc.status} |\n")
    w("\n")

    # 4 thermal window
    w("## 4. Heating and the thermal window\n\n")
    w(f"- Reheat range {REHEAT_RANGE_C[0]:.0f}-{REHEAT_RANGE_C[1]:.0f} C [RDR]. Overheating from "
      f"~{OVERHEATING_ONSET_C:.0f} C, burning from ~{BURNING_ONSET_C:.0f} C (ESTIMATE). "
      f"Source note: {THERMAL_SOURCE_NOTE}\n")
    w("- Finishing limit evaluated at 800 / 850 / 880 C because Ar3 is EDGE (validation memo #30: "
      "two estimates ~200 C apart, neither chemistry-matched). A measured chemistry (HP-02) and a "
      "dilatometer or handbook Ar3 for it replace this parameter.\n")
    w("- Lumped model validity: Biot number (imported `biot_number`) at 1000 C: " + ", ".join(
        f"{h:g} mm -> {biot_number(h, 250.0, 1000.0, emissivity=EMISSIVITY_NOMINAL):.3f}"
        for h in (6.0, 12.0, 20.0)) + " (all << 0.1).\n\n")
    w("Air cooling of the pieces (radiation + convection, eps 0.85) [PC]:\n\n")
    w("| Section (h x b x L mm) | rate at 1150 C (C/s) | rate at 900 C (C/s) | "
      "time 1200 -> 850 C in air (s) |\n|---|---|---|---|\n")
    for h, b, length in ((20, 300, 400), (15, 200, 700), (12, 250, 500), (10, 300, 800),
                         (8, 250, 750), (6, 250, 1000), (6, 300, 1333)):
        w(f"| {h} x {b} x {length} | "
          f"{piece_cooling_rate_c_per_s(h, b, length, 1150.0, EMISSIVITY_NOMINAL):.1f} | "
          f"{piece_cooling_rate_c_per_s(h, b, length, 900.0, EMISSIVITY_NOMINAL):.1f} | "
          f"{time_to_limit_s(h, b, length, 1200.0, 850.0):.0f} |\n")
    w("\nFurnace time [PC] (lumped, single layer, furnace at target + 40 C, eps_eff 0.7): "
      "first heat to 1200 C, then a 10 min soak [RDR 5-15 min]:\n\n")
    w("| Piece | heat-up to 1200 C (min) | + soak (min) | reheat 850 -> 1150 C (min) |\n"
      "|---|---|---|---|\n")
    for k, p in PIECES.items():
        t1, _ = heat_up(AMBIENT_C, 1200.0, p.thickness_mm, p.width_mm, p.length_mm, 1240.0)
        t2, _ = heat_up(850.0, 1150.0, p.thickness_mm * 0.6, p.width_mm, p.length_mm / 0.6, 1190.0)
        w(f"| {k} ({p.thickness_mm:g} mm) | {t1 / 60:.1f} | {(t1 + FIRST_SOAK_S) / 60:.1f} | "
          f"{t2 / 60:.1f} (at 0.6 h0) |\n")
    w("\nStacked or touching pieces heat 1.5-2x slower; rust delays the start [SM].\n\n")
    w("### Reheats needed per conversion, S1 nominal (D400, 0.6 m/s, interpass 8 s, transfer "
      "20 s, first heat 1200 C, reheat 1150 C)\n\n")
    w("Rule: before each pass the model predicts the exit temperature; if it is below the "
      "finishing limit, the piece returns to the furnace first. Band = hot-side set (eps 0.75, "
      "h_gap 10 kW/m2K, interpass 5 s, transfer 12 s, 1250/1200 C) to cold-side set (eps 0.90, "
      "h_gap 30 kW/m2K, interpass 12 s, transfer 40 s, 1150/1150 C, S355).\n\n")
    w("| Conversion | Brief passes | Rec. passes | Reheats brief @800/850/880 | "
      "Reheats rec. @800/850/880 | Rec. band @850 (hot..cold) | Last-pass exit C rec. @850 |\n"
      "|---|---|---|---|---|---|---|\n")
    for pk, t in CONVERSIONS:
        rb = [s1_brief_by_tf[tf][(pk, t)].reheats for tf in FINISH_TEMPS_C]
        rr = [s1_by_tf[tf][(pk, t)].reheats for tf in FINISH_TEMPS_C]
        band = bands[((pk, t), 850.0)]
        r = s1[(pk, t)]
        w(f"| {r.conversion} | {len(s1_brief[(pk, t)].passes)} | {len(r.passes)} | "
          f"{'/'.join(map(str, rb))} | {'/'.join(map(str, rr))} | {band[0]}..{band[1]} | "
          f"{r.final.exit_temp_c:.0f} |\n")
    w("\nThin pieces cool fast: a 6 mm x 250 mm piece loses ~" +
      f"{piece_cooling_rate_c_per_s(6, 250, 1000, 1000.0, EMISSIVITY_NOMINAL):.0f} C/s at "
      "1000 C, so every 8 s interpass costs "
      f"{min(p.transfer_loss_c for r in s1.values() for p in r.passes if p.transfer_after_s):.0f}-"
      f"{max(p.transfer_loss_c for r in s1.values() for p in r.passes if p.transfer_after_s):.0f} C "
      "(nominal runs), and each bite on a roll at 150 C costs "
      f"{min(p.chill_c for r in s1.values() for p in r.passes):.0f}-"
      f"{max(p.chill_c for r in s1.values() for p in r.passes):.0f} C of mean temperature at "
      "h_gap 15 kW/m2K and 0.6 m/s ("
      f"{min(p.chill_c for r in cold_runs.values() for p in r.passes):.0f}-"
      f"{max(p.chill_c for r in cold_runs.values() for p in r.passes):.0f} C at 30 kW/m2K), "
      "partly offset by "
      f"{min(p.deformation_heat_c for r in s1.values() for p in r.passes):.0f}-"
      f"{max(p.deformation_heat_c for r in s1.values() for p in r.passes):.0f} C of deformation "
      "heat.\n\n")

    # 5 schedules
    w("## 5. Pass schedules - S1 nominal\n\n")
    w("**Correction to the brief's s5 schedules.** Every brief schedule passes the bite check "
      "with a wide margin (S1 bite is never binding) and every reduction is 17-24 %. What the "
      "brief schedules do not account for is heat: the 5- and 6-thickness schedules spend 4-5 "
      "interpass intervals on pieces cooling at 5-15 C/s. The recommended schedules use the "
      "fewest passes that respect (a) bite at mu 0.25 x 0.85, (b) <= 30 % per pass [RDR], "
      "(c) <= 20 % on the last pass for gauge and shape [RDR]. Pass count changes: "
      + "; ".join(f"{c} {a} -> {b}" for c, a, b in changed)
      + ", at the cost of higher per-pass force (shown). "
      "The intermediate gauges are concept figures, not gap settings.\n\n")
    w("| Conversion | Schedule (mm) | Passes | Reheats @850 | Peak F (MN) | Peak T/roll "
      "(kN.m) | Peak P (kW) | RMS P (kW) | Max mu req. | Exit b x L (mm) |\n"
      "|---|---|---|---|---|---|---|---|---|---|\n")
    for kind, table in (("brief", s1_brief), ("recommended", s1)):
        for pk, t in CONVERSIONS:
            r = table[(pk, t)]
            w(f"| {r.conversion} ({kind}) | {' > '.join(f'{x:g}' for x in r.thicknesses)} | "
              f"{len(r.passes)} | {r.reheats} | {_mn(r.peak('force_n'))} | "
              f"{_knm(r.peak('torque_per_roll_nm'))} | {r.peak('power_kw'):.0f} | "
              f"{r.rms_power_kw:.1f} | {r.peak('mu_required'):.3f} | "
              f"{r.final.exit_b:.0f} x {r.final.exit_len_mm:.0f} |\n")
    w("\n### Pass-by-pass, recommended schedules, S1 nominal, S235, mu 0.30, finish limit 850 C\n\n")
    w("Columns: heat number (R = reheated before the pass), gauges, reduction, cumulative "
      "reduction, required mu vs bite limit, contact length, mean pressure, force, torque per "
      "roll, power, speed, rolling time, entry/exit temperature, roll chill, interpass loss, "
      "exit width/length/mass, gap crown. All [PC].\n\n")
    for pk, t in CONVERSIONS:
        r = s1[(pk, t)]
        w(f"**{r.conversion}** - mill occupancy {r.mill_time_s:.0f} s, furnace "
          f"{r.furnace_time_s / 60:.0f} min, heats {r.heats}\n\n")
        w("| # | Heat | h in>out | Red % | Cum % | mu req (lim 0.25) | L (mm) | p (MPa) | F (MN) | "
          "T/roll (kN.m) | P (kW) | v | t_roll (s) | T in>out (C) | chill (C) | "
          "loss after (C) | b x L (mm) | kg | crown (mm) |\n")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for p in r.passes:
            w(f"| {p.index} | {p.heat}{'R' if p.reheat_before else ''} | {p.entry_h:g}>{p.exit_h:g} "
              f"| {p.reduction_pct:.1f} | {p.cum_reduction_pct:.1f} | {p.mu_required:.3f} | "
              f"{p.contact_len_mm:.1f} | {p.mean_pressure_mpa:.0f} | {_mn(p.force_n)} | "
              f"{_knm(p.torque_per_roll_nm)} | {p.power_kw:.0f} | {p.speed_m_s:g} | "
              f"{p.rolling_time_s:.2f} | {p.entry_temp_c:.0f}>{p.exit_temp_c:.0f} | "
              f"{p.chill_c:.0f} | {p.transfer_loss_c:.0f} | {p.exit_b:.0f} x {p.exit_len_mm:.0f} | "
              f"{p.exit_mass_kg:.2f} | {p.gap_crown_mm:.3f} |\n")
        w("\n")
    w("The full set (S1 at 800/850/880 C, S2, S3, brief and recommended) is in "
      "`docs/reroll/pass_schedules_2026-09-28.csv`.\n\n")

    # 6 yield
    w("## 6. Yield (mass balance closes exactly: input = scale + crop + trim + OOT + saleable)\n\n")
    w("Scale from each run's own time-temperature history (Paidassi parabolic law, reset at "
      "each descale). Cross-check: the forging-shop rule of thumb of ~2-3 % scale per heat for "
      "small sections (CLAIM, widely quoted, not pinned to a source) is of the same order. "
      "Crop = irregular original ends ("
      + "/".join(f"{YIELD_CASES['irregular_end_mm'][c]:g}" for c in ("low", "nominal", "high"))
      + " mm per end averaged over all ends, at the original section, [SM]) + tongue/fishtail ("
      + "/".join(f"{YIELD_CASES['tongue_mm'][c]:g}" for c in ("low", "nominal", "high"))
      + " mm per end at the final section, full at >= 50 % reduction, pro rata below). Trim "
      + "/".join(f"{YIELD_CASES['edge_trim_mm'][c]:g}" for c in ("low", "nominal", "high"))
      + " mm per side. OOT "
      + "/".join(f"{100 * YIELD_CASES['out_of_tol'][c]:g}" for c in ("low", "nominal", "high"))
      + " %.\n\n")
    w("| Conversion (S1 rec.) | Heats | Scale % | Crop % | Trim % | OOT % | Net yield nominal | "
      "Range (high loss .. low loss) |\n|---|---|---|---|---|---|---|---|\n")
    for pk, t in CONVERSIONS:
        r = s1[(pk, t)]
        yn, yl, yh = yield_breakdown(r), yield_breakdown(r, "high"), yield_breakdown(r, "low")
        w(f"| {r.conversion} | {r.heats} | {yn['scale_pct']:.1f} | {yn['crop_pct']:.1f} | "
          f"{yn['trim_pct']:.1f} | {yn['oot_pct']:.1f} | {yn['yield'] * 100:.1f} % | "
          f"{yl['yield'] * 100:.0f}-{yh['yield'] * 100:.0f} % |\n")
    w("\nPre-squaring the ends cold (saw) removes the same mass as cropping afterwards but "
      "removes the rounded/conical ends before they can bite off-centre or fold; it is "
      "recommended for the pilot [RDR]. The rounded ends do NOT help bite here, because bite "
      "is not binding.\n\n")

    # 7 capacity
    w("## 7. Capacity (S1, manual cycle) and furnace size by tier\n\n")
    w(f"Mill occupancy per piece = transfer + rolling + interpasses + reheat round trips + "
      f"{HANDLING_OVERHEAD_S:.0f} s handling; utilisation {MILL_UTILISATION:.2f} (ASSUMPTION). "
      "The furnace holds several pieces so reheating overlaps with rolling of other pieces.\n\n")
    w("| Conversion | Occupancy (s) | Pieces/h | kg/h input | kg/h saleable | Furnace "
      "residence (min) | Pieces in furnace |\n|---|---|---|---|---|---|---|\n")
    for pk, t in CONVERSIONS:
        c = cap[(pk, t)]
        w(f"| {s1[(pk, t)].conversion} | {c['mill_occupancy_s']:.0f} | {c['pieces_per_h']:.0f} | "
          f"{c['kg_per_h_input']:.0f} | {c['kg_per_h_saleable']:.0f} | "
          f"{c['furnace_residence_min']:.0f} | {c['pieces_in_furnace']:.1f} |\n")
    worst = min(s1.items(), key=lambda kv: cap[kv[0]]["kg_per_h_input"])
    kg_worst = cap[worst[0]]["kg_per_h_input"]
    heats_avg = sum(r.heats for r in s1.values()) / len(s1)
    res_max = max(r.furnace_time_s for r in s1.values()) / 3600.0
    tier_notes = {}
    w("\n| Tier | Basis | Throughput (kg/h) | Hearth load (kg) | Hearth area (m2) | Firing "
      "(kW, eff 20-35 %) | Note |\n|---|---|---|---|---|---|---|\n")
    for tier in TIERS:
        ft = furnace_tier(tier, kg_worst, heats_avg, res_max, PIECES["B"])
        tier_notes[tier] = ft
        w(f"| {tier} | {ft['basis']} | {ft['throughput_kg_h']:.0f} | {ft['hearth_load_kg']:.0f} | "
          f"{ft['hearth_area_m2']:.2f} | {ft['firing_kw_range'][0]:.0f}-"
          f"{ft['firing_kw_range'][1]:.0f} | {ft['note']} |\n")
    need_ind = TIERS["industrial"][0] * 1000.0 / kg_worst
    w(f"\nThe workshop tier is a campaign of a few weeks a year on one S1. The industrial tier "
      f"needs {need_ind:.0f} h/yr at the slowest conversion's pace against "
      f"{TIERS['industrial'][1]:.0f} h on two shifts: "
      + ("it fits on two shifts. " if need_ind <= TIERS["industrial"][1] else
         "it needs a third shift, a faster semi-automatic handling cycle or a second stand. ")
      + "In every tier the furnace is a small batch or twin-chamber unit of a few hundred kW "
      "at most, not a 20 t/h walking beam. [PC]\n\n")

    # 8 sizing
    w("## 8. S1 equipment sizing [RDR]\n\n")
    w("Envelope: D 350/400/450, speed 0.3/0.6/1.0 m/s, mu 0.25/0.35, S235/S355, finish limit "
      "800/850/880 C, brief and recommended schedules, all 9 conversions "
      f"({len(env)} runs).\n\n")
    w("| Item | D350 | D400 | D450 |\n|---|---|---|---|\n")
    ds = sorted(sizing)

    def line(name, fn):
        w(f"| {name} | " + " | ".join(fn(sizing[d]) for d in ds) + " |\n")
    line("Peak separating force (MN) [PC]", lambda s: _mn(s["force_peak_n"]))
    line("Bearing/frame rating, x1.3-1.5 (MN) [RDR]",
         lambda s: f"{s['force_rating_n'][0] / 1e6:.1f}-{s['force_rating_n'][1] / 1e6:.1f}")
    line("Peak total roll torque, steady (kN.m) [PC]", lambda s: _knm(s["torque_total_peak_nm"]))
    line("RMS total roll torque (kN.m) [PC]", lambda s: _knm(s["torque_total_rms_nm"]))
    line("Gearbox output rating (kN.m) [RDR]", lambda s: _knm(s["gearbox_output_rating_nm"]))
    line("Peak roll power in envelope (kW) [PC]", lambda s: f"{s['power_peak_kw']:.0f}")
    for vt in (0.6, 1.0):
        line(f"Top speed {vt} m/s: ratio (985 rpm motor, R20)",
             lambda s, vt=vt: f"{s['drive'][vt]['ratio_exact']:.1f} -> {s['drive'][vt]['ratio_r20']:g}")
        line(f"Top speed {vt} m/s: motor kW min -> IEC [RDR]",
             lambda s, vt=vt: f"{s['drive'][vt]['motor_kw_min']:.0f} -> {s['drive'][vt]['motor_kw_iec']:.0f}")
    line("Peak neck bending stress (MPa) [PC]", lambda s: f"{s['neck_stress_peak_mpa']:.0f}")
    line("Peak gap crown from bending+shear (mm) [PC]", lambda s: f"{s['crown_peak_mm']:.3f}")
    line("Longest exit piece (mm)", lambda s: f"{s['longest_piece_mm']:.0f}")
    line("Widest exit (mm)", lambda s: f"{s['widest_mm']:.0f}")
    line("Table each side, 1.15 L + 0.5 m (m) [RDR]", lambda s: f"{s['table_each_side_m']:.1f}")
    w("\nMotor: AC induction, 6-pole, with a heavy-duty VFD (150 % for 60 s), rated at the "
      "roll speed chosen as the top speed. Motor kW = max(peak/1.5, RMS) x base speed. "
      "Bite shock (2-3x steady) is taken by the gearbox rating (peak criterion: shock / 2.0 "
      "catalogue allowance) and by VFD torque limiting. A pinion stand drives both rolls. "
      "The frame must carry overload protection (breaker block or hydraulic relief) because a "
      "cold or double-thickness piece entering by mistake would exceed any rating chosen from "
      "hot flow stress. [RDR]\n\n")
    w("Roll diameter 380-420 mm and barrel 500-600 mm [RDR]: bite is never binding even at "
      "D350, and a smaller roll reduces force and torque, but below ~350 mm the neck stress and "
      "crown rise and the roll cannot be re-ground many times. Barrel >= 500 covers the widest "
      "exit (~310 mm) with >= 90 mm each side for side guides; cross-rolling piece A (500 mm "
      "wide) would need >= 650 mm and is not assumed.\n\n")
    ga = [gauge_tolerance(s1[k]) for k in CONVERSIONS]
    w("### Thickness tolerance and flatness - an honest range\n\n")
    w("| Conversion | head-tail dT (C) | dF (kN) | wedge (mm) at M 1.5..0.5 MN/mm | gap crown (mm) | "
      "within-piece spread (mm) | absolute stretch (mm) |\n|---|---|---|---|---|---|---|\n")
    for (pk, t), g in zip(CONVERSIONS, ga):
        w(f"| {s1[(pk, t)].conversion} | {g['head_tail_dT_c']:.0f} | {g['dF_n'] / 1e3:.0f} | "
          f"{g['wedge_mm'][0]:.2f}-{g['wedge_mm'][1]:.2f} | {g['crown_mm']:.3f} | "
          f"{g['spread_total_mm'][0]:.2f}-{g['spread_total_mm'][1]:.2f} | "
          f"{g['stretch_mm'][0]:.1f}-{g['stretch_mm'][1]:.1f} |\n")
    w("\nReading: roll bending crown is small (<0.05 mm) for these narrow pieces; the real "
      f"thickness scatter comes from stand stretch ({min(g['stretch_mm'][0] for g in ga):.1f}-"
      f"{max(g['stretch_mm'][1] for g in ga):.1f} mm absolute at M 0.5-1.5 MN/mm, which "
      "the gap setting must pre-compensate by a first-piece check) and from temperature "
      "differences. A realistic expectation for a manual small mill without AGC is +/-0.2 to "
      "+/-0.4 mm on 6-10 mm [RDR], i.e. in the order of the EN 10029 class A band for plate "
      "(about -0.4/+0.8 mm at 5-8 mm and -0.5/+0.9 mm at 8-15 mm: CLAIM, recalled, check the "
      "standard text), but NOT a cold-rolled tolerance. Flatness: short, stiff pieces with "
      "crown < 1 % of h should roll without edge waves; bow and twist from uneven cooling are "
      "the likely defects and a roller leveller (or press straightening for the pilot) is "
      "required [RDR]. Final figures are [SM] from the pilot.\n\n")

    # 9 option C
    w("## 9. Option C (S2): the D600 x 600 stand of the other project\n\n")
    w(f"**Status: NOT available.** Per the control doc, no equipment of PRJ-STEEL-ROLLING-LINE-01 "
      f"is recorded as operational or purchased (as of 2026-09-28); the stand's status is open "
      f"(PRC-01), the furnace exists only as a draft RFI, and the 1.6-2 MW DC motor is a design "
      f"option, not an asset. The numbers below answer 'would it make sense IF it existed'.\n\n")
    w("| Check | Value [PC] | Reading |\n|---|---|---|\n")
    w(f"| Peak force, all 9 conversions, S355, mu 0.35, D600 at 0.8 m/s | "
      f"{_mn(oc['force_peak_n'])} MN | {oc['force_fraction'] * 100:.0f} % of the {_SLD_FORCE_N / 1e6:.2f} MN proxy "
      f"(the slab-line model's design duty over 6-30 mm at S355, as quoted in its stand RFI; "
      f"the real rating is UNKNOWN). "
      f"At S235 / mu 0.30: {_mn(oc['force_peak_nominal_n'])} MN = "
      f"{oc['force_peak_nominal_n'] / SCENARIOS['S2'].force_rating_n * 100:.0f} %. "
      f"Not a tiny fraction: the D600 roll has a longer arc of contact on thin, cooler stock "
      f"than S1 (S1 nominal peak {_mn(oc['s1_force_peak_n'])} MN) |\n")
    w(f"| Peak total torque | {_knm(oc['torque_peak_nm'])} kN.m | "
      f"{oc['torque_fraction'] * 100:.0f} % of the 218 kN.m proxy |\n")
    w(f"| Peak power at 0.8 m/s | {oc['power_peak_kw']:.0f} kW | "
      f"{oc['power_fraction_of_1600kw'] * 100:.0f} % of a 1600 kW motor (itself only a design "
      "option) |\n")
    w(f"| Bite | max draft / exact limit at mu 0.25 = {oc['bite_util_max']:.2f} | no issue |\n")
    w(f"| Rolling time at 3 m/s | " + ", ".join(f"{k} {v:.2f} s" for k, v in oc['time_at_3ms_s'].items())
      + " (entry lengths) | shorter than a DC reversal ramp (2-3 s): the mill would never reach "
      "speed; it must run at threading speed (~0.8 m/s) |\n")
    w(f"| Piece length vs table | shortest entry {oc['shortest_piece_mm']:.0f} mm; longest exit "
      f"{oc['longest_exit_mm']:.0f} mm; table roller pitch assumed 600-1000 mm [SM] | a piece "
      "must span at least 2-3 rollers: 400-700 mm entry pieces do not; tables need a short-"
      "pitch insert or manual handling |\n")
    w(f"| Piece vs slab | entry pieces are {oc['piece_len_vs_slab'][0] * 100:.0f}-"
      f"{oc['piece_len_vs_slab'][1] * 100:.0f} % of a 3 m slab's length; a 1.2 t slab weighs "
      f"{oc['pieces_per_slab_mass'][0]:.0f}-{oc['pieces_per_slab_mass'][1]:.0f} pieces | "
      "walking-beam spacing designed for 3 m slabs cannot carry 0.4-0.7 m pieces [SM] |\n")
    w(f"| Furnace 20 t/h at the tiers | pilot {oc['tiers']['pilot']['fraction_of_rated'] * 100:.1f} %, "
      f"workshop {oc['tiers']['workshop']['fraction_of_rated'] * 100:.2f} %, industrial "
      f"{oc['tiers']['industrial']['fraction_of_rated'] * 100:.1f} % of rated | holding fuel alone "
      f"~{oc['hold_mw'][0]:.1f}-{oc['hold_mw'][1]:.1f} MW (ESTIMATE: 1.2-1.6 GJ/t full rate, "
      f"20-30 % to hold) = {oc['tiers']['industrial']['hold_kwh_per_kg'][0]:.1f}-"
      f"{oc['tiers']['industrial']['hold_kwh_per_kg'][1]:.1f} kWh/kg at the industrial tier vs "
      "~0.6-1.1 kWh/kg in a right-sized batch furnace |\n")
    w(f"| Minimum gap | stretch {oc['stretch_mm'][0]:.2f}-{oc['stretch_mm'][1]:.2f} mm at 3-8 MN/mm; "
      f"unloaded gap ~{oc['min_unloaded_gap_mm'][0]:.1f}-{oc['min_unloaded_gap_mm'][1]:.1f} mm for "
      "6 mm | the slab-line design range includes 6 mm, so in principle yes; the real "
      "screw-down range and resolution are [SM] |\n")
    w("| Reheat loop | " + ", ".join(f"{k[0]}->{k[1]:g}: {v}" for k, v in oc['reheats'].items())
      + " | any reheat needs a separate small furnace next to the stand |\n")
    w("| Operational | NO | not commissioned, possibly not owned |\n\n")
    w(f"**Verdict [PC]:** the stand could carry the load (force {oc['force_fraction'] * 100:.0f} % "
      f"and torque {oc['torque_fraction'] * 100:.0f} % of the slab-line duty proxy, power "
      f"{oc['power_fraction_of_1600kw'] * 100:.0f} % of the design motor), but force is NOT a small "
      "fraction, so the stand's real rating must be known before it is used for thin gauges; "
      "and its furnace, tables, speed range and drive are built for 1.2 t slabs. Option C only makes sense if ALL of "
      "these become true: (1) the stand is owned, installed and commissioned for its own slab "
      "product anyway, so the re-roll campaign is marginal use of spare hours; (2) a separate "
      "small batch furnace (~60-450 kW class, section 7; not 20 t/h) is placed next to it; (3) a short-pitch "
      "table insert or manual tong handling is provided for 0.4-1.8 m pieces; (4) the screw-"
      f"down can set an unloaded gap of ~{oc['min_unloaded_gap_mm'][0]:.1f}-"
      f"{oc['min_unloaded_gap_mm'][1]:.1f} mm with a gauge check; (5) the drive can hold a low "
      "threading speed (0.5-1 m/s) and reverse quickly. None of these is true today.\n\n")

    # 10 S3
    w("## 10. Toll rolling (S3) - parameter range\n\n")
    w("| D (mm) | Peak F (MN) | Peak total torque (kN.m) | Max reheats @850 | Passes per conversion |\n"
      "|---|---|---|---|---|\n")
    for d, v in s3.items():
        w(f"| {d:.0f} | {_mn(v['force_peak_n'])} | {_knm(v['torque_peak_nm'])} | {v['reheats_max']} | "
          + ", ".join(f"{k.split()[0]}{k.split()[1].split('->')[1]}: {n}" for k, n in v['passes'].items())
          + " |\n")
    s3max = max(v["force_peak_n"] for v in s3.values())
    w(f"\nPeak force rises with roll diameter to {s3max / 1e6:.1f} MN at D1000 "
      f"({100 * s3max / SCENARIOS['S3'].force_rating_n:.0f} % of the 5 MN floor assumed for "
      "this class; real plate-mill stands are usually rated far higher, [SM] per host). The "
      "risk is acceptance, not load: a plate or strip mill typically has a minimum slab length "
      "of a metre or more and handles tonne pieces (HYPOTHESIS, host-specific); 0.4-0.7 m, "
      "12-19 kg pieces may be refused or need hand-feeding. Better toll hosts are small "
      "section/strip mills, forge shops with a small two-high stand, or a university/"
      "research pilot mill (D 300-500) - the same class as S1. Speed and interpass time at "
      "the host decide the reheat count exactly as for S1. [PC]\n\n")

    # 11 cold
    w("## 11. Cold route (S4)\n\n")
    w("Cold flow stress: Swift law, S235 K 530 MPa n 0.26 (ESTIMATE, textbook annealed 1020-type), "
      "S355 K 760 MPa n 0.18 (ASSUMPTION). Lubricated mu 0.08, bite x 0.85, <= 25 % per pass, "
      "Hitchcock flattening, no tension, 0.3 m/s.\n\n")
    w("| Mill | h0 (mm) | Reduction | Grade | Passes | Peak F (MN) | Peak total torque (kN.m) | "
      "Peak P (kW) | Final flow stress (MPa) |\n|---|---|---|---|---|---|---|---|---|\n")
    for (label, h0, red, g), c in cold.items():
        w(f"| {label} | {h0:g} | {red * 100:.0f} % | {g} | {c['n_passes']} | "
          f"{_mn(c['peak_force_n'])} | {_knm(c['peak_torque_nm'])} | {c['peak_power_kw']:.0f} | "
          f"{c['final_flow_stress_mpa']:.0f} |\n")
    c20 = cold[("two-high D400", 20.0, 0.7, "S235JR")]
    w(f"\n**Verdict [PC]: not recommended.** 20->6 mm cold needs ~{c20['n_passes']} passes on a "
      f"D400 two-high at ~{c20['peak_force_n'] / 1e6:.1f} MN peak (S235), i.e. a mill several "
      "times heavier than S1, plus: acid pickling first (the pieces are rusty and scaled; rust "
      "pits elongate but do not roll out); a full recrystallisation anneal after 50-70 % "
      "(flow stress rises to ~550-800 MPa, elongation collapses; ~650-720 C sub-critical "
      "or normalising ~900-920 C, under protective atmosphere or it re-scales); and a product "
      "(6-10 mm cold-rolled plate) that is not a standard commercial item. A light cold "
      "planishing pass after hot rolling (<= 5-10 %) is the only cold step worth keeping in "
      "view, and only if HP-03 asks for a surface/tolerance the hot route cannot give.\n\n")

    # 12 sensitivity
    w("## 12. Sensitivity (one at a time, S1 recommended; B 20->6 and A 12->6)\n\n")
    w("| Case | B peak F (MN) | B peak T total (kN.m) | B reheats | A reheats | B scale % | "
      "B net yield % |\n|---|---|---|---|---|---|---|\n")
    for name, f, t, rb, ra, sp, y in sens:
        w(f"| {name} | {f:.2f} | {t:.1f} | {rb} | {ra} | {sp:.1f} | {y:.1f} |\n")
    w("\n")

    # 13 risks
    w("## 13. Engineering risks and hold points\n\n")
    w("Top three engineering risks:\n\n")
    w("1. **Heat loss on thin, light pieces.** The finishing limit (Ar3, EDGE) and the real "
      f"interpass/transfer times decide between {reheats_nom[850.0]} (nominal) and "
      f"{band_max[850.0]} (cold-side) reheats per conversion at 850 C, up to "
      f"{band_max[880.0]} at 880 C; the first heat costs {min(first_scale):.1f}-"
      f"{max(first_scale):.1f} % scale and each reheat another "
      f"{min(reheat_scale or [0]):.1f}-{max(reheat_scale or [0]):.1f} %, plus furnace time. "
      "Mitigation: fewer heavier passes, short transfers, "
      "a furnace next to the stand, measured Ar3 for the real chemistry (HP-02), pyrometer "
      "log in the pilot [SM].\n")
    w("2. **Yield.** Scale (several % per heat on 12-20 mm pieces), irregular ends and tongue "
      f"crops on 0.6-1.8 m products, and edge trim together remove {loss_lo:.0f}-{loss_hi:.0f} % "
      "of the input (section 6). "
      "The product spec (HP-03: mill edge acceptable? minimum length?) moves yield more than "
      "any mill parameter.\n")
    w("3. **Unknown material and flow stress.** The hot flow-stress anchors are unsourced, the "
      "S355 multiplier is unsourced, and a higher-carbon or alloyed grade (HP-02) raises loads "
      "and cracking risk. Size S1 on the S355 envelope with the stated margin and run PMI "
      "before any heat.\n\n")
    w("Hold points unchanged: HP-01 quantity/tonnage, HP-02 grade/chemistry, HP-03 product "
      "spec. New [SM] items: mill modulus of whichever stand is used, real transfer/interpass "
      "times, irregular-end lengths, table pitch and gap range if option C is ever revisited.\n\n")

    # 14 errors
    w("## 14. Errors or gaps found in the brief (and how they are handled)\n\n")
    w("- s4 table: correct as geometry; 1313 and 1333 are roundings. It omits spread "
      "(Wusatowski gives < 0.1 % here; real edge bulge is [SM]) and all losses; handled in "
      "sections 5-6.\n")
    w(f"- s5 schedules: pass bite and reduction checks but ignore heat; {len(changed)} of them use "
      "one pass more than needed. Corrected in section 5.\n")
    w("- s6 option C lists the stand's speed (~3 m/s) as a capability; for 0.4-0.7 m pieces "
      "top speed is irrelevant and the threading speed and reversal time govern.\n")
    w("- s8 'rounded ends help bite' (s10 question): bite is not binding on any scenario here, "
      "so the ends are a crop-loss and fold-defect question, not a bite aid.\n")
    w("- The imported slab-line roll-chill constant (8 C/contact) is not valid for 6-20 mm "
      "stock and was replaced by a contact-conduction model.\n")
    return out.getvalue()


# ---------------------------------------------------------------------------
# 19. CLI
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=f"{PROJECT_ID} concept calculations")
    ap.add_argument("--report", help="write the engineering report (Markdown)")
    ap.add_argument("--csv", help="write all pass schedules (CSV)")
    ap.add_argument("--inputs", help="write the inputs/assumptions table (Markdown)")
    a = ap.parse_args(argv)
    if not (a.report or a.csv or a.inputs):
        for (pk, t), r in s1_nominal().items():
            print(f"{r.conversion}: {len(r.passes)} passes, {r.reheats} reheats, "
                  f"F {r.peak('force_n') / 1e6:.2f} MN, yield {yield_breakdown(r)['yield']:.2f}")
        return 0
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            fh.write(build_report())
        print(f"report -> {a.report}")
    if a.csv:
        n = write_csv(a.csv)
        print(f"csv -> {a.csv} ({n} rows)")
    if a.inputs:
        with open(a.inputs, "w", encoding="utf-8") as fh:
            fh.write(inputs_markdown())
        print(f"inputs -> {a.inputs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
