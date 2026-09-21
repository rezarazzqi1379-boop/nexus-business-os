"""Thermal transfer model + feedstock-route mass balance for the engineer's
2026-09-21 requirement (300/400 mm now, 600 mm future, 8-30 mm thick).

STATUS: ESTIMATE. Every material property here is a literature ASSUMPTION, not a
measurement of this line's steel. Nothing in this module measures anything.

Why it exists: the engineer declared a five-point temperature profile
(1250/1200/1050/950/800 C) over real distances (12 m furnace->roughing,
21 m roughing->ST2). Whether that profile is physically reachable is a
calculation, not an opinion. This module does that calculation.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# --- material ASSUMPTIONS (literature, not measured on this line) -----------
RHO = 7850.0            # kg/m3 at room T; used for mass. ASSUMPTION
CP = 700.0              # J/kg.K, austenite above ~800 C. ASSUMPTION (+-10%)
K_STEEL = 28.0          # W/m.K at ~1100 C. ASSUMPTION
EMISSIVITY = 0.80       # oxidised/scaled hot steel. ASSUMPTION (range 0.75-0.85)
SIGMA_SB = 5.670e-8     # W/m2.K4 FACT
T_AMB_K = 303.0         # 30 C mill bay. ASSUMPTION


@dataclass(frozen=True)
class Section:
    """A rectangular hot section in transit."""
    thickness_mm: float
    width_mm: float
    volume_m3: float

    @property
    def area_m2(self) -> float:
        return (self.thickness_mm / 1000.0) * (self.width_mm / 1000.0)

    @property
    def length_m(self) -> float:
        return self.volume_m3 / self.area_m2

    @property
    def mass_kg(self) -> float:
        return self.volume_m3 * RHO

    @property
    def surface_m2(self) -> float:
        """Four long faces. Ends are <1% and are ignored (stated, not hidden)."""
        per = 2.0 * (self.thickness_mm + self.width_mm) / 1000.0
        return per * self.length_m

    @property
    def char_length_m(self) -> float:
        return self.volume_m3 / self.surface_m2


def billet_section(t_mm=150.0, w_mm=150.0, l_mm=3150.0) -> Section:
    v = (t_mm / 1000.0) * (w_mm / 1000.0) * (l_mm / 1000.0)
    return Section(t_mm, w_mm, v)


def h_convection(velocity_m_s: float) -> float:
    """Forced convection over a moving hot surface in a mill bay.
    Simple engineering correlation h = 5.7 + 3.8*v (W/m2.K). ASSUMPTION."""
    return 5.7 + 3.8 * max(velocity_m_s, 0.0)


def cool_transit(section: Section, t_start_c: float, distance_m: float,
                 velocity_m_s: float, emissivity: float = EMISSIVITY,
                 covered: bool = False, dt: float = 0.05):
    """Lumped-capacitance cooling of a moving section. Returns a dict.

    `covered` models an insulated/reflective tunnel by cutting the NET radiative
    driving force: the cover re-radiates. Modelled as an effective emissivity
    reduction to 0.25 - ESTIMATE, not vendor data.
    """
    eps = 0.25 if covered else emissivity
    h_c = h_convection(velocity_m_s)
    if velocity_m_s <= 0:
        raise ValueError("velocity must be positive")
    t_total = distance_m / velocity_m_s
    m_cp = section.mass_kg * CP
    A = section.surface_m2
    T = t_start_c + 273.15
    elapsed = 0.0
    q_rad0 = eps * SIGMA_SB * (T ** 4 - T_AMB_K ** 4)
    while elapsed < t_total:
        step = min(dt, t_total - elapsed)
        q_rad = eps * SIGMA_SB * (T ** 4 - T_AMB_K ** 4)
        q_con = h_c * (T - T_AMB_K)
        T -= (q_rad + q_con) * A * step / m_cp
        elapsed += step
    t_end_c = T - 273.15
    # surface skin: semi-infinite body, constant surface flux (upper bound on
    # the extra drop the SURFACE sees beyond the mean)
    alpha = K_STEEL / (RHO * CP)
    skin_depth_m = math.sqrt(alpha * t_total)
    dT_surface_extra = 2.0 * q_rad0 * math.sqrt(alpha * t_total / math.pi) / K_STEEL
    h_rad0 = q_rad0 / max(t_start_c + 273.15 - T_AMB_K, 1.0)
    biot = (h_rad0 + h_c) * section.char_length_m / K_STEEL
    return {
        "transit_s": t_total,
        "mean_drop_c": t_start_c - t_end_c,
        "t_end_mean_c": t_end_c,
        "rad_flux_kw_m2": q_rad0 / 1000.0,
        "con_flux_kw_m2": h_c * (t_start_c + 273.15 - T_AMB_K) / 1000.0,
        "surface_m2": A,
        "mass_kg": section.mass_kg,
        "length_m": section.length_m,
        "biot": biot,
        "skin_depth_mm": skin_depth_m * 1000.0,
        "surface_extra_drop_c": dT_surface_extra,
        "lumped_valid": biot < 0.1,
    }


# --- feedstock routes -------------------------------------------------------
@dataclass(frozen=True)
class Feedstock:
    name: str
    thickness_mm: float
    width_mm: float
    length_mm: float
    evidence: str

    @property
    def area_mm2(self) -> float:
        return self.thickness_mm * self.width_mm

    @property
    def volume_m3(self) -> float:
        return self.area_mm2 * self.length_mm / 1e9

    @property
    def mass_kg(self) -> float:
        return self.volume_m3 * RHO


ROUTE_A = Feedstock("A - current 150x150 billet", 150, 150, 3150,
                    "MEASUREMENT-class: engineer stated, on intake record")
ROUTE_B1 = Feedstock("B1 - 200x200 bloom", 200, 200, 3150, "HYPOTHETICAL")
ROUTE_B2 = Feedstock("B2 - 250x250 bloom", 250, 250, 3000, "HYPOTHETICAL")
ROUTE_B3 = Feedstock("B3 - 320x150 rect. bloom", 150, 320, 3150, "HYPOTHETICAL")
ROUTE_C1 = Feedstock("C1 - 60x320 slab", 60, 320, 4000, "HYPOTHETICAL")
ROUTE_C2 = Feedstock("C2 - 50x620 slab", 50, 620, 4000, "HYPOTHETICAL")


def route_metrics(feed: Feedstock, out_t_mm: float, out_w_mm: float,
                  yield_fraction: float = 0.96) -> dict:
    """Mass balance and the two ratios that decide feasibility."""
    a_in = feed.area_mm2
    a_out = out_t_mm * out_w_mm
    out_len_m = feed.volume_m3 * yield_fraction / (a_out / 1e6)
    return {
        "feed": feed.name,
        "in_area_mm2": a_in,
        "out_area_mm2": a_out,
        "reduction_ratio": a_in / a_out,
        "width_ratio": out_w_mm / feed.width_mm,
        "thickness_ratio": feed.thickness_mm / out_t_mm,
        "product_length_m": out_len_m,
        "mass_kg": feed.mass_kg,
        "pieces_per_tonne": 1000.0 / feed.mass_kg,
    }
