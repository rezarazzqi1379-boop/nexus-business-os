"""Executable transmission-number check.

Origin: docs/system/TRANSMISSION_AUDIT_STEEL_2026-09-26.md. That audit was a
one-off comparison of the vendor-facing RFIs against what `slab_line_design.py`
computes. This module turns it into a standing check: every CLAIM below binds
one number (or number range) on one line of a vendor RFI to the model call
that is supposed to produce it. If a future edit — to the RFI text, or to the
model itself — makes the document disagree with the model, the claim fails.

Design, per claim:
  - `globs`: filename glob(s) under docs/procurement/, EN and ZH twins both
    listed (FM-006 bilingual parity: the same numbers appear on the same
    line in both languages, unabbreviated units kept in Latin script except
    "mm", which the ZH text spells 毫米).
  - `patterns`: one regex per language variant that finds the exact line and
    captures the number(s) as named groups (`group_order` fixes the order).
    Patterns tolerate ≥, ≈, thousands commas and both "-"/"–" dashes,
    because superseded_values.py already showed these appear in this project's
    documents; Persian digits are normalised the same way it does, in case a
    Persian-language RFI twin is ever added.
  - `compute(m)`: calls into the imported `slab_line_design` module and
    returns the expected raw value(s), in the same order as `group_order`.
    This is what makes the check track the MODEL, not a frozen number: change
    a model constant and `compute` returns a different number next run.
  - `round`: the rounding rule the RFI text itself applies (stated as a
    docstring-visible callable, e.g. "ceil to nearest 5 kN·m"), plus `tol`,
    the residual slack after that rounding (float noise only, unless noted).
  - `basis`: the stated engineering basis, for the failure message.
  - `source`: "model" (checked) or "input" (vendor-stated or a buyer
    assumption with no model function behind it - listed for visibility,
    never checked; see CLAIMS_INPUT below).

Every "model" claim here was run against the real v5 RFIs on 2026-09-26 and
matches exactly (see evals/test_nexus_checks_transmission.py::test_a_real_rfis_pass).
A number that did NOT match was left out rather than faked - see the module
docstring in evals/test_nexus_checks_transmission.py for that list.
"""
from __future__ import annotations

import importlib
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import Finding

# ---------------------------------------------------------------------------
# number parsing (same normalisation as superseded_values.py)
# ---------------------------------------------------------------------------
_FA = str.maketrans("۰۱۲۳۴۵۶۷۸۹٫", "0123456789.")


def _num(s: str) -> float:
    return float(s.translate(_FA).replace(",", ""))


# ---------------------------------------------------------------------------
# rounding rules the RFIs themselves use
# ---------------------------------------------------------------------------
def ceil_to(step: float) -> Callable[[float], float]:
    """'rounded up to nearest <step>' - used for the gearbox torque ratings,
    which the RFI states as ">=" floors, and for the regen power, which the
    RFI rounds up to a cleaner instrument-catalogue number."""
    def f(v: float) -> float:
        return math.ceil(v / step - 1e-9) * step
    return f


def round_to(ndigits: int = 0) -> Callable[[float], float]:
    """plain nearest-value rounding, e.g. 218.296 kN·m -> 218.3 (1 decimal)."""
    def f(v: float) -> float:
        return round(v, ndigits)
    return f


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Claim:
    id: str
    globs: tuple[str, ...]                 # filenames under docs/procurement/
    patterns: tuple[re.Pattern, ...]        # tried in line order, first match wins
    group_order: tuple[str, ...]            # named-group order == compute() order
    compute: Callable[[object], tuple[float, ...]] | None
    round: Callable[[float], float]
    tol: float
    basis: str
    source: str = "model"                  # "model" (checked) or "input" (listed only)


def _p(*alts: str) -> tuple[re.Pattern, ...]:
    return tuple(re.compile(a) for a in alts)


DASH = r"[–—-]"   # en dash, em dash, hyphen-minus


# ---- compute helpers, each a thin call into slab_line_design --------------
def _s(m, t: float):
    return m.build_schedule(t, "balanced", grade="S355JR")


def _gearbox_trace_30mm(m) -> dict:
    s30 = _s(m, 30.0)
    cs = m.cycle_summary(s30)
    return m.gearbox_rating_trace(s30, 7.1, cs["cycle_s"])


def _output_factor(m) -> float:
    return m.ETA_SPINDLE * m.ETA_COUPLING * m.ETA_PINION * m.ETA_COUPLING


def compute_accel_brake_range(m) -> tuple[float, float]:
    mb = m.mass_balance()
    vals = [2 * len(_s(m, t)) * mb.slabs_per_hour for t in m.THICKNESS_TARGETS_MM]
    return min(vals), max(vals)


def compute_reversals_range(m) -> tuple[float, float]:
    mb = m.mass_balance()
    vals = [m.reversals_per_slab(_s(m, t)) * mb.slabs_per_hour for t in m.THICKNESS_TARGETS_MM]
    return min(vals), max(vals)


def compute_gearbox_rated(m) -> tuple[float, float]:
    tr = _gearbox_trace_30mm(m)
    f = _output_factor(m)
    return tr["criterion_b_peak_nm"] / f / 1e3, tr["rated_recommendation_nm"] / f / 1e3


def compute_gearbox_guaranteed_peak(m) -> tuple[float]:
    tr = _gearbox_trace_30mm(m)
    f = _output_factor(m)
    return (tr["guaranteed_peak_requirement_nm"] / f / 1e3,)


def compute_gearbox_expansion_peak(m) -> tuple[float]:
    tr = _gearbox_trace_30mm(m)
    f = _output_factor(m)
    return (tr["expansion_option_peak_nm"] / f / 1e3,)


def compute_bite_impact_range(m) -> tuple[float, float]:
    tr = _gearbox_trace_30mm(m)
    f = _output_factor(m)
    return tr["bite_shock_2x_nm"] / f / 1e3, tr["bite_shock_3x_nm"] / f / 1e3


def compute_accel_torque_range(m) -> tuple[float, float]:
    mb = m.mass_balance()
    s30 = _s(m, 30.0)
    cs = m.cycle_summary(s30)
    lo = m.motor_duty(s30, 1600, 350, 7.1, cs["cycle_s"], mb.slabs_per_hour,
                       accel_time_s=3, max_rpm=700, motor_rotor_j=450).accel_torque_nm / 1e3
    hi = m.motor_duty(s30, 2000, 350, 7.1, cs["cycle_s"], mb.slabs_per_hour,
                       accel_time_s=2, max_rpm=700, motor_rotor_j=750).accel_torque_nm / 1e3
    return lo, hi


def compute_regen_680(m) -> tuple[float]:
    r = m.braking_per_stop(m.inertia_at_motor_kgm2(7.1, motor_rotor_j=750), 678, 3)
    return (r["instantaneous_power_kw"],)


def compute_peak_force_mn(m) -> tuple[float]:
    return (max(m.worst_cases(_s(m, t))["max_force"].force_n for t in m.THICKNESS_TARGETS_MM) / 1e6,)


def compute_peak_torque_knm(m) -> tuple[float]:
    return (max(m.worst_cases(_s(m, t))["max_torque"].torque_roll_nm for t in m.THICKNESS_TARGETS_MM) / 1e3,)


def compute_spindle_design_torque(m) -> tuple[float]:
    s30 = _s(m, 30.0)
    peak = m.worst_cases(s30)["max_torque"].torque_roll_nm
    return (m.torque_per_roll_nm(peak)["design_per_spindle_nm"] / 1e3,)


def compute_ratio_7_1(m) -> tuple[float]:
    o = m.build_dc_option("x", _s(m, 30.0), 1600, 350, 2.0, "")
    return (o.gear_ratio,)


def compute_pinion_centre(m) -> tuple[float]:
    c12 = m.optimal_pinion_centre_mm(_s(m, 12.0), diameter_worn_mm=560)["optimal_centre_mm"]
    c6 = m.optimal_pinion_centre_mm(_s(m, 6.0), diameter_worn_mm=560)["optimal_centre_mm"]
    return ((c12 + c6) / 2.0,)


def compute_service_factor(m) -> tuple[float]:
    return (m.total_service_factor(),)


# ---- the registry -----------------------------------------------------------
CLAIMS: list[Claim] = [
    Claim(
        id="accel-brake-204-374",
        globs=("RFQ-MAIN-GEARBOX_EN_v5_*.md", "RFQ-MAIN-GEARBOX_ZH_v5_*.md",
               "RFQ-DC-MOTOR-DRIVE_EN_v5_*.md", "RFQ-DC-MOTOR-DRIVE_ZH_v5_*.md"),
        patterns=_p(
            rf"accelerations plus brakings about (?P<lo>[\d,]+)\s*{DASH}\s*(?P<hi>[\d,]+) per hour",
            rf"加速与制动合计每小时约(?P<lo>[\d,]+){DASH}(?P<hi>[\d,]+)次",
        ),
        group_order=("lo", "hi"),
        compute=compute_accel_brake_range,
        round=round_to(0),
        tol=0.5,
        basis="2*len(build_schedule(t,'balanced',grade='S355JR'))*mass_balance().slabs_per_hour, min/max over t=30..6 mm",
    ),
    Claim(
        id="reversals-85-170",
        globs=("RFQ-MAIN-GEARBOX_EN_v5_*.md", "RFQ-MAIN-GEARBOX_ZH_v5_*.md",
               "RFQ-DC-MOTOR-DRIVE_EN_v5_*.md", "RFQ-DC-MOTOR-DRIVE_ZH_v5_*.md",
               "RFQ-REVERSING-STAND_EN_v5_*.md", "RFQ-REVERSING-STAND_ZH_v5_*.md"),
        patterns=_p(
            rf"(?P<lo>[\d,]+)\s*{DASH}\s*(?P<hi>[\d,]+)\s*(?:reversals\s+)?per hour depending on product thickness",
            rf"每小时(?:正反转)?(?P<lo>[\d,]+){DASH}(?P<hi>[\d,]+)次",
        ),
        group_order=("lo", "hi"),
        compute=compute_reversals_range,
        round=round_to(0),
        tol=0.5,
        basis="reversals_per_slab(build_schedule(t,...))*mass_balance().slabs_per_hour, min/max over t=30..6 mm",
    ),
    Claim(
        id="gearbox-rated-345-420",
        globs=("RFQ-MAIN-GEARBOX_EN_v5_*.md", "RFQ-MAIN-GEARBOX_ZH_v5_*.md"),
        patterns=_p(
            r"Rated output torque \| ≥(?P<a>[\d.]+) kN·m \(≈(?P<b>[\d.]+) kN·m preferred\)",
            r"额定输出扭矩 \| ≥(?P<a>[\d.]+) kN·m（推荐约(?P<b>[\d.]+) kN·m）",
        ),
        group_order=("a", "b"),
        compute=compute_gearbox_rated,
        round=ceil_to(5),
        tol=1e-6,
        basis="gearbox_rating_trace(s30,7.1,cycle_summary(s30)['cycle_s'])"
              "['criterion_b_peak_nm' | 'rated_recommendation_nm'] / "
              "(ETA_SPINDLE*ETA_COUPLING*ETA_PINION*ETA_COUPLING), rounded up to 5",
    ),
    Claim(
        id="gearbox-guaranteed-peak-685",
        globs=("RFQ-MAIN-GEARBOX_EN_v5_*.md", "RFQ-MAIN-GEARBOX_ZH_v5_*.md"),
        patterns=_p(
            r"Guaranteed peak output torque \| ≥(?P<a>[\d.]+) kN·m",
            r"保证峰值输出扭矩 \| ≥(?P<a>[\d.]+) kN·m",
        ),
        group_order=("a",),
        compute=compute_gearbox_guaranteed_peak,
        round=ceil_to(5),
        tol=1e-6,
        basis="gearbox_rating_trace(...)['guaranteed_peak_requirement_nm'] / output factor, rounded up to 5",
    ),
    Claim(
        id="gearbox-expansion-peak-840",
        globs=("RFQ-MAIN-GEARBOX_EN_v5_*.md", "RFQ-MAIN-GEARBOX_ZH_v5_*.md"),
        patterns=_p(
            r"Expansion option \| Peak (?P<a>[\d.]+) kN·m",
            r"扩展选项 \| 峰值(?P<a>[\d.]+) kN·m",
        ),
        group_order=("a",),
        compute=compute_gearbox_expansion_peak,
        round=ceil_to(5),
        tol=1e-6,
        basis="gearbox_rating_trace(...)['expansion_option_peak_nm'] / output factor, rounded up to 5",
    ),
    Claim(
        id="duty-bite-impact-455-682",
        globs=("RFQ-MAIN-GEARBOX_EN_v5_*.md", "RFQ-MAIN-GEARBOX_ZH_v5_*.md"),
        patterns=_p(
            r"Bite impact \| (?P<lo>[\d.]+) to (?P<hi>[\d.]+) kN·m",
            r"咬入冲击 \| (?P<lo>[\d.]+)至(?P<hi>[\d.]+) kN·m",
        ),
        group_order=("lo", "hi"),
        compute=compute_bite_impact_range,
        round=ceil_to(1),
        tol=1e-6,
        basis="gearbox_rating_trace(...)['bite_shock_2x_nm' | 'bite_shock_3x_nm'] / output factor, rounded up to 1",
    ),
    Claim(
        id="accel-torque-12-29",
        globs=("RFQ-MAIN-GEARBOX_EN_v5_*.md", "RFQ-MAIN-GEARBOX_ZH_v5_*.md"),
        patterns=_p(
            r"\| (?P<lo>[\d.]+) to (?P<hi>[\d.]+) kN·m equivalent at motor shaft",
            r"折算至电机轴(?P<lo>[\d.]+)至(?P<hi>[\d.]+) kN·m",
        ),
        group_order=("lo", "hi"),
        compute=compute_accel_torque_range,
        round=round_to(0),
        tol=0.5,
        basis="motor_duty(...).accel_torque_nm: low = rotor 450 kg·m^2 @ 3 s ramp, "
              "high = rotor 750 kg·m^2 @ 2 s ramp, both at i=7.1, max_rpm=700",
    ),
    Claim(
        id="regen-680-at-3s",
        globs=("RFQ-DC-MOTOR-DRIVE_EN_v5_*.md", "RFQ-DC-MOTOR-DRIVE_ZH_v5_*.md"),
        patterns=_p(
            r"peak regenerative power ≥(?P<v>[\d.]+) kW instantaneous at a 3 s braking ramp",
            r"瞬时峰值回馈功率≥(?P<v>[\d.]+) kW（制动斜坡3秒时",
        ),
        group_order=("v",),
        compute=compute_regen_680,
        round=ceil_to(10),
        tol=1e-6,
        basis="braking_per_stop(inertia_at_motor_kgm2(7.1, motor_rotor_j=750), 678, 3)"
              "['instantaneous_power_kw'], rounded up to 10",
    ),
    Claim(
        id="stand-peak-force-5.12mn",
        globs=("RFQ-REVERSING-STAND_EN_v5_*.md", "RFQ-REVERSING-STAND_ZH_v5_*.md"),
        patterns=_p(
            r"Design rolling force \| (?P<v>[\d.]+) MN",
            r"设计轧制力 \| (?P<v>[\d.]+) MN",
        ),
        group_order=("v",),
        compute=compute_peak_force_mn,
        round=round_to(2),
        tol=1e-6,
        basis="max(worst_cases(build_schedule(t,'balanced','S355JR'))['max_force']) over t=30..6mm, in MN, 2 decimals",
    ),
    Claim(
        id="stand-peak-torque-218.3",
        globs=("RFQ-REVERSING-STAND_EN_v5_*.md", "RFQ-REVERSING-STAND_ZH_v5_*.md"),
        patterns=_p(
            r"Roll torque \| (?P<v>[\d.]+) kN·m total",
            r"轧辊扭矩 \| 总计(?P<v>[\d.]+) kN·m",
        ),
        group_order=("v",),
        compute=compute_peak_torque_knm,
        round=round_to(1),
        tol=1e-6,
        basis="max(worst_cases(build_schedule(t,'balanced','S355JR'))['max_torque']) over t=30..6mm, in kN·m, 1 decimal",
    ),
    Claim(
        id="stand-spindle-torque-120.1",
        globs=("RFQ-REVERSING-STAND_EN_v5_*.md", "RFQ-REVERSING-STAND_ZH_v5_*.md"),
        patterns=_p(
            r"(?P<v>[\d.]+) kN·m design per spindle",
            r"每根接轴设计扭矩(?P<v>[\d.]+) kN·m",
        ),
        group_order=("v",),
        compute=compute_spindle_design_torque,
        round=round_to(1),
        tol=1e-6,
        basis="torque_per_roll_nm(worst_cases(build_schedule(30,'balanced','S355JR'))['max_torque'])"
              "['design_per_spindle_nm'], 1 decimal",
    ),
    Claim(
        id="ratio-7.1",
        globs=("RFQ-MAIN-GEARBOX_EN_v5_*.md", "RFQ-MAIN-GEARBOX_ZH_v5_*.md"),
        patterns=_p(
            r"≈(?P<v>[\d.]+):1\*\*, our preliminary preferred value",
            r"约(?P<v>[\d.]+):1\*\*，我方初步推荐值",
        ),
        group_order=("v",),
        compute=compute_ratio_7_1,
        round=round_to(1),
        tol=1e-6,
        basis="build_dc_option(..., rated_kw=1600, base_rpm=350, field_weakening=2.0).gear_ratio "
              "(the model's own snap-down rule)",
    ),
    Claim(
        id="pinion-centre-646mm",
        globs=("RFQ-REVERSING-STAND_EN_v5_*.md", "RFQ-REVERSING-STAND_ZH_v5_*.md"),
        patterns=_p(
            r"centre distance ≈(?P<v>[\d.]+) mm",
            r"中心距约(?P<v>[\d.]+)毫米",
        ),
        group_order=("v",),
        compute=compute_pinion_centre,
        round=round_to(0),
        tol=2.0,   # midpoint of the 12mm (648.5) and 6mm (645.5) worn-roll optima; "≈" in the RFI
        basis="mean of optimal_pinion_centre_mm(build_schedule(t,...), diameter_worn_mm=560)"
              "['optimal_centre_mm'] for t in (12, 6) mm",
    ),
    Claim(
        id="gearbox-service-factor-2.21",
        globs=("RFQ-MAIN-GEARBOX_EN_v5_*.md", "RFQ-MAIN-GEARBOX_ZH_v5_*.md"),
        patterns=_p(
            r"Service factor used by us \| (?P<v>[\d.]+) =",
            r"我方采用的服务系数 \| (?P<v>[\d.]+) =",
        ),
        group_order=("v",),
        compute=compute_service_factor,
        round=round_to(2),
        tol=1e-6,
        basis="total_service_factor(), 2 decimals",
    ),
]

# Deliberately stale / not-model-derived claims (task item 4): recorded for
# visibility, never checked. Each is a real RFI number that the transmission
# audit (2026-09-26, §4 M12/M24; §2.1) found no model function behind.
CLAIMS_INPUT: list[Claim] = [
    Claim(
        id="gearbox-rated-power-1800-2200",
        globs=("RFQ-MAIN-GEARBOX_EN_v5_*.md", "RFQ-MAIN-GEARBOX_ZH_v5_*.md"),
        patterns=(),
        group_order=(),
        compute=None,
        round=round_to(0),
        tol=0.0,
        basis="'Rated power >=1800 / >=2200 kW' (RFQ-MAIN-GEARBOX EN:37): audit M12 - no "
              "slab_line_design function produces it; 330/405 kN·m at 49.3 rpm correspond to "
              "1704/2091 kW, not 1800/2200. UNSUPPORTED, buyer-stated.",
        source="input",
    ),
    Claim(
        id="gearbox-ratio-25-reference",
        globs=("RFQ-MAIN-GEARBOX_EN_v5_*.md", "RFQ-MAIN-GEARBOX_ZH_v5_*.md"),
        patterns=(),
        group_order=(),
        compute=None,
        round=round_to(0),
        tol=0.0,
        basis="'(A) 25:1' comparison option: an unverified vendor/market reference number, "
              "explicitly labelled as such in the RFI; not derived from the model.",
        source="input",
    ),
    Claim(
        id="stand-nominal-capacity-6mn",
        globs=("RFQ-REVERSING-STAND_EN_v5_*.md", "RFQ-REVERSING-STAND_ZH_v5_*.md"),
        patterns=(),
        group_order=(),
        compute=None,
        round=round_to(0),
        tol=0.0,
        basis="'nominal stand capacity for this enquiry >=6 MN': audit M24 - sourced to "
              "EXEC/SLAB, not Package A or any model function; a buyer-chosen round target "
              "above the model's 5.12/6.02 MN peaks, not a computed value.",
        source="input",
    ),
]


# ---------------------------------------------------------------------------
# checker
# ---------------------------------------------------------------------------
def _load_model(repo: Path):
    """Import slab_line_design from the repo root. stdlib-only (verified: it
    imports only `math` and `dataclasses`), so this needs nothing beyond
    putting the repo root on sys.path."""
    repo_str = str(repo.resolve())
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
    if "slab_line_design" in sys.modules:
        m = importlib.reload(sys.modules["slab_line_design"])
    else:
        m = importlib.import_module("slab_line_design")
    return m


def _check_claim(claim: Claim, expected: tuple[float, ...], docs_dir: Path) -> list[Finding]:
    out: list[Finding] = []
    for g in claim.globs:
        matches = sorted(docs_dir.glob(g))
        if not matches:
            out.append(Finding("transmission", "WARN", str(docs_dir / g), 0, claim.id,
                               "no file matches this claim's glob"))
            continue
        for path in matches:
            out.extend(_check_claim_in_file(claim, expected, path))
    return out


def _check_claim_in_file(claim: Claim, expected: tuple[float, ...], path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), 1):
        for pat in claim.patterns:
            mobj = pat.search(line)
            if not mobj:
                continue
            actual = tuple(_num(mobj.group(g)) for g in claim.group_order)
            findings = []
            for a, e in zip(actual, expected):
                rounded = claim.round(e)
                if abs(a - rounded) > claim.tol:
                    findings.append(Finding(
                        "transmission", "ERROR", str(path), i, claim.id,
                        f"document states {a:g} but the model gives {e:.3f} "
                        f"(rounded {rounded:g}); basis: {claim.basis}"))
            return findings
    return [Finding("transmission", "ERROR", str(path), 0, claim.id,
                    f"expected line not found (basis: {claim.basis})")]


def check(model, docs_dir: Path) -> list[Finding]:
    """Core checker: `model` is an already-imported slab_line_design module
    (a test may monkeypatch it beforehand), `docs_dir` is the directory to
    glob the RFIs from (normally <repo>/docs/procurement)."""
    out: list[Finding] = []
    for claim in CLAIMS:
        expected = claim.compute(model)
        out.extend(_check_claim(claim, expected, docs_dir))
    return out


def check_repo(repo: Path) -> list[Finding]:
    """CLI entry point: import slab_line_design from `repo` and check
    `repo/docs/procurement` against it."""
    m = _load_model(repo)
    return check(m, repo / "docs" / "procurement")
