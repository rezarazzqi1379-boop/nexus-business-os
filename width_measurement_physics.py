"""IC-02 measurement physics - what accuracy does the question actually demand?

!!! SUPERSEDED IN PART - READ THIS FIRST !!!
============================================
An independent review on 2026-09-21 returned REJECT on the conclusions this
module was built to support. Three of its findings are structural, not
cosmetic, and they are recorded in
`.nexus/expert_foundry/registers/ENGINEERING_FAILURE_MEMORY.md` as FM-001:

 1. THE DENOMINATOR HAS NO ERROR TERM. kappa = actual_gain / free_spread_gain,
    and the free-spread gain is a Wusatowski fit carrying roughly +/-10-20%
    of its own scatter - at an 8mm gain that is +/-0.8-1.6mm, equal to or
    larger than the ENTIRE measurement budget below. Thickness error, which
    kappa also depends on, is absent from the budget altogether. So the fine
    kappa question is MODEL-limited, not instrument-limited, and the
    architecture ranking this module computes cannot be used to justify
    buying a better instrument.

 2. SYSTEMATIC TERMS CANCEL IN THE DIFFERENCE. Obliquity is a multiplicative
    scale factor (width x cos(theta)), not an additive mm bias, and for one
    fixed sensor it cancels when entry and exit readings are differenced -
    this module over-penalises the good architectures by roughly 20x. The
    same applies to calibration drift and the bulk thermal correction.

 3. THE THERMAL TREATMENT IS INVERTED. Pyrometer emissivity and calibration
    error is COMMON-MODE between the two readings of one pass and largely
    harmless; what actually survives is the entry-to-exit COOLING within the
    pass, which is one-signed. This module models the harmless term as random
    noise and omits the harmful one.

WHAT REMAINS USABLE: the thermal-expansion arithmetic, the pixel/bloom
geometry, and - most importantly - the inverse-design framing in
required_width_accuracy_mm(), which correctly shows the coarse and fine
questions land in different instrument classes. That framing survives; the
absolute numbers attached to each architecture do not.

WHAT REPLACED IT: the review pointed out that this whole module solves an
inverse problem whose forward data is physically accessible - the groove
drawings are lost, but the rolls are not. See
`docs/expert_foundry/IC02_REVISED_DESIGN_v0_2.md`.

Kept in the repository deliberately, not deleted: the failure is the record.

FIRST-PRINCIPLES FRAMING
========================
The usual way to pick a measurement system is to look at catalogues and buy the
best affordable one. That is backwards. The right question is:

    how small an error must we achieve before the ANSWER changes?

IC-02 asks two questions of very different difficulty, and they have very
different accuracy requirements:

  Q1 (coarse) - is width made by grooves or by free spread?
      Answered by the CUMULATIVE gap: flat rolling predicts ~183mm final width,
      the mill makes ~250mm. That is a 67mm difference. Almost any instrument
      resolves it.

  Q2 (fine) - what is kappa per pass, so a groove set can be characterised?
      Answered by comparing a per-pass width GAIN (~8-18mm) against its
      free-spread prediction. To separate kappa = 1.0 from the 1.3
      classification threshold you must resolve ~0.3 x gain, i.e. a few mm,
      on a 150-250mm workpiece.

So the cheap instrument may fully answer Q1 while being useless for Q2. This
module computes where that line falls instead of assuming it.

ERROR SOURCES, from the physics rather than from a datasheet:
  - thermal expansion: the piece is measured hot and reported cold
  - edge bloom: a glowing hot edge spreads across sensor pixels
  - camera obliquity: an off-perpendicular view reads width x cos(theta)
  - vibration blur: symmetric edge smearing, biases width UP
  - steam/fume: intermittent dropout, not bias, if many frames are combined
  - calibration drift: scale-factor error on the reference

All values are ASSUMPTION unless a datasheet is cited. Nothing here is a
measurement of the real mill.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

# Linear thermal expansion of low-carbon steel. Rises with temperature; 13e-6/K
# is a reasonable mean over 20-1100C for austenitic-range carbon steel.
# ESTIMATE - replace with a grade-specific curve before any precision claim.
ALPHA_PER_K = 13e-6
REFERENCE_TEMP_C = 20.0


def thermal_expansion_mm(true_cold_width_mm: float, temperature_c: float,
                         alpha_per_k: float = ALPHA_PER_K) -> float:
    """How much wider the piece measures because it is hot."""
    if true_cold_width_mm <= 0:
        raise ValueError("width must be positive")
    return true_cold_width_mm * alpha_per_k * (temperature_c - REFERENCE_TEMP_C)


def hot_to_cold(measured_hot_mm: float, temperature_c: float,
                alpha_per_k: float = ALPHA_PER_K) -> float:
    """Correct a hot reading back to cold dimensions."""
    if measured_hot_mm <= 0:
        raise ValueError("measured width must be positive")
    return measured_hot_mm / (1.0 + alpha_per_k * (temperature_c - REFERENCE_TEMP_C))


def temperature_uncertainty_mm(width_mm: float, temp_uncertainty_k: float,
                               alpha_per_k: float = ALPHA_PER_K) -> float:
    """Width error contributed purely by NOT knowing the temperature.

    This is the coupling that makes the pyrometer non-optional: a width gauge
    cannot be more accurate than the temperature knowledge feeding its
    hot-to-cold correction.
    """
    if width_mm <= 0 or temp_uncertainty_k < 0:
        raise ValueError("width must be positive and temperature uncertainty non-negative")
    return width_mm * alpha_per_k * temp_uncertainty_k


def obliquity_error_mm(width_mm: float, angle_deg: float) -> float:
    """A camera off-perpendicular by angle_deg reads width * cos(angle).

    Always reads SHORT, so it is a bias, not noise - it does not average out.
    """
    if width_mm <= 0:
        raise ValueError("width must be positive")
    return width_mm * (1.0 - math.cos(math.radians(angle_deg)))


def pixel_resolution_mm(field_of_view_mm: float, sensor_pixels: int) -> float:
    if field_of_view_mm <= 0 or sensor_pixels <= 0:
        raise ValueError("field of view and pixel count must be positive")
    return field_of_view_mm / sensor_pixels


def edge_bloom_error_mm(pixel_mm: float, bloom_pixels: float) -> float:
    """A glowing edge spreads over neighbouring pixels, on BOTH edges."""
    if pixel_mm <= 0 or bloom_pixels < 0:
        raise ValueError("pixel size must be positive and bloom non-negative")
    return 2.0 * pixel_mm * bloom_pixels


@dataclass(frozen=True)
class MeasurementArchitecture:
    """One candidate way of measuring inter-pass width."""
    arch_id: str
    name: str
    principle: str
    field_of_view_mm: float
    sensor_pixels: int
    bloom_pixels: float          # edge spread in pixels
    mounting_angle_deg: float    # achievable alignment accuracy
    vibration_blur_mm: float     # symmetric smear, biases width up
    calibration_drift_frac: float
    sample_rate_hz: float
    temp_uncertainty_k: float    # how well temperature is known for correction
    cost_class: str
    buildable_locally: bool
    reversible_install: bool
    notes: str = ""

    @property
    def pixel_mm(self) -> float:
        return pixel_resolution_mm(self.field_of_view_mm, self.sensor_pixels)

    def error_budget_mm(self, width_mm: float) -> dict:
        """Per-source error contributions at a given workpiece width."""
        bloom = edge_bloom_error_mm(self.pixel_mm, self.bloom_pixels)
        oblique = obliquity_error_mm(width_mm, self.mounting_angle_deg)
        temp = temperature_uncertainty_mm(width_mm, self.temp_uncertainty_k)
        drift = width_mm * self.calibration_drift_frac
        return {
            "pixel_mm": self.pixel_mm,
            "edge_bloom": bloom,
            "obliquity_bias": oblique,
            "vibration_blur": self.vibration_blur_mm,
            "temperature": temp,
            "calibration_drift": drift,
        }

    def total_error_mm(self, width_mm: float) -> dict:
        """Biases add; independent noise adds in quadrature."""
        b = self.error_budget_mm(width_mm)
        bias = b["obliquity_bias"] + b["vibration_blur"]     # both systematic
        noise = math.sqrt(b["edge_bloom"] ** 2 + b["temperature"] ** 2
                          + b["calibration_drift"] ** 2)
        return {
            "systematic_bias_mm": bias,
            "random_1sigma_mm": noise,
            "worst_case_mm": bias + 2.0 * noise,
        }


def simulate_reading(true_width_mm: float, arch: MeasurementArchitecture,
                     temperature_c: float, rng: random.Random) -> float:
    """One corrupted, then corrected, width reading."""
    hot = true_width_mm * (1.0 + ALPHA_PER_K * (temperature_c - REFERENCE_TEMP_C))
    hot -= obliquity_error_mm(hot, arch.mounting_angle_deg)     # always reads short
    hot += arch.vibration_blur_mm                                # always reads long
    b = arch.error_budget_mm(true_width_mm)
    hot += rng.gauss(0.0, b["edge_bloom"] / 2.0)
    hot *= 1.0 + rng.gauss(0.0, arch.calibration_drift_frac)
    assumed_temp = temperature_c + rng.gauss(0.0, arch.temp_uncertainty_k)
    return hot_to_cold(hot, assumed_temp)


def required_width_accuracy_mm(natural_gain_mm: float, kappa_a: float, kappa_b: float,
                               confidence_sigma: float = 2.0) -> float:
    """Inverse design: how accurate must width be to separate two kappa values?

    kappa = actual_gain / natural_gain, and actual_gain is a DIFFERENCE of two
    width readings, so its error is sqrt(2) x the single-reading error.
    """
    if natural_gain_mm <= 0:
        raise ValueError("natural gain must be positive")
    if kappa_a == kappa_b:
        raise ValueError("the two kappa values must differ")
    gain_separation = abs(kappa_a - kappa_b) * natural_gain_mm
    allowed_gain_error = gain_separation / confidence_sigma
    return allowed_gain_error / math.sqrt(2.0)


def monte_carlo_kappa(true_kappa: float, entry_width_mm: float, natural_gain_mm: float,
                      arch: MeasurementArchitecture, temperature_c: float,
                      trials: int = 2000, seed: int = 7) -> dict:
    """Propagate measurement error into kappa uncertainty."""
    if trials < 100:
        raise ValueError("use at least 100 trials for a meaningful distribution")
    rng = random.Random(seed)
    exit_width = entry_width_mm + true_kappa * natural_gain_mm
    kappas = []
    for _ in range(trials):
        b0 = simulate_reading(entry_width_mm, arch, temperature_c, rng)
        b1 = simulate_reading(exit_width, arch, temperature_c, rng)
        kappas.append((b1 - b0) / natural_gain_mm)
    kappas.sort()
    n = len(kappas)
    mean = sum(kappas) / n
    var = sum((k - mean) ** 2 for k in kappas) / (n - 1)
    return {
        "true_kappa": true_kappa,
        "mean_kappa": round(mean, 3),
        "sigma_kappa": round(math.sqrt(var), 3),
        "p05": round(kappas[int(0.05 * n)], 3),
        "p95": round(kappas[int(0.95 * n)], 3),
        "bias": round(mean - true_kappa, 3),
        "trials": n,
    }


def can_discriminate(arch: MeasurementArchitecture, entry_width_mm: float,
                     natural_gain_mm: float, temperature_c: float,
                     kappa_a: float = 1.0, kappa_b: float = 1.3,
                     trials: int = 2000) -> dict:
    """Can this architecture actually tell free spread from groove-assisted?"""
    a = monte_carlo_kappa(kappa_a, entry_width_mm, natural_gain_mm, arch, temperature_c, trials, seed=11)
    b = monte_carlo_kappa(kappa_b, entry_width_mm, natural_gain_mm, arch, temperature_c, trials, seed=23)
    separation = abs(b["mean_kappa"] - a["mean_kappa"])
    pooled_sigma = math.sqrt((a["sigma_kappa"] ** 2 + b["sigma_kappa"] ** 2) / 2.0)
    z = separation / pooled_sigma if pooled_sigma > 0 else float("inf")
    return {
        "architecture": arch.arch_id,
        "separation_sigma": round(z, 2),
        "resolves_fine_kappa": z >= 3.0,
        "case_a": a,
        "case_b": b,
        "verdict": ("resolves per-pass kappa" if z >= 3.0
                    else "cannot resolve per-pass kappa - usable only for the coarse question"),
    }
