"""PRJ-STEEL-REROLL-01 - economics and decision rule (concept level).

Answers one question with numbers: for the existing thick pieces, which route
leaves the most money per kg of input?
  E  sell/keep the pieces as they are and buy 6/8/10 mm product
  A  toll rolling (pay a rolling workshop per kg)
  B  own small reversing hot mill (sized in reroll_study.py, scenario S1)

Every price carries its evidence class and source. Toman prices are a single-week
snapshot (Iran rial is volatile): the RESULTS are ratios and break-even tonnages,
which move far less than the absolute prices. Nothing here is a quote.
Engineering inputs (net yield, mill capacity) are recomputed from reroll_study.py,
never copied (FM-010).

Run:  python reroll_economics.py --report docs/reroll/ECONOMICS_2026-09-28.md
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

import reroll_study as rs

STUDY_DATE = "2026-09-28"

# --------------------------------------------------------------------------------------
# Market inputs (Toman/kg unless stated). (low, nominal, high) + evidence + source.
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Price:
    key: str
    low: float
    nom: float
    high: float
    unit: str
    evidence: str
    source: str


PRICES = {
    "scrap_heavy": Price(
        "Heavy scrap buy price (dealer, >=2 t lots)", 52_000, 54_000, 56_500, "Toman/kg",
        "DAILY-MARKET-LIST (buyer posting)",
        "mesterahan.com scrap table read 2026-09-28: Isfahan super-special 565,000 / heavy "
        "550,000 Rial; Khorasan heavy 520,000; Shiraz super-special <1 m 520,000 Rial"),
    "offcut_usable": Price(
        "Usable plate offcut (ته‌ورق) sale to fabricators", 60_000, 75_000, 90_000, "Toman/kg",
        "ESTIMATE (no current published quote found)",
        "bracketed between scrap (floor) and ~75 % of new 12-20 mm plate; market research "
        "s1d: no listing retrievable"),
    "plate_6": Price(
        "New HR plate 6 mm ST37 (mill sheet)", 124_500, 128_200, 130_900, "Toman/kg",
        "DAILY-MARKET-LIST", "ahanmelal 2026-09-27 (Mobarakeh 124,545); pivan 2026-09-25 "
        "128,200-130,900; fooladsell 2026-09-25 125,091"),
    "plate_8": Price(
        "New HR plate 8 mm ST37", 101_200, 124_500, 129_100, "Toman/kg", "DAILY-MARKET-LIST",
        "shahrahan 2026-09-28 low end 101,200 (8 mm fabric); ahanmelal 2026-09-27 Mobarakeh "
        "124,545, Oxin 129,091"),
    "plate_10": Price(
        "New HR plate 10 mm ST37", 120_000, 123_600, 136_000, "Toman/kg", "DAILY-MARKET-LIST",
        "ahanmelal 2026-09-27 (Mobarakeh 120,000, Oxin 123,636); smtnews 2026-09-28 136,000"),
    "product_discount": Price(
        "Rerolled small pieces vs new mill plate (value ratio)", 0.70, 0.82, 0.92, "-",
        "ESTIMATE", "non-standard sizes (200-300 wide, 0.6-1.75 m), no mill certificate; "
        "buyers are small fabricators. HP-03"),
    "toll_rate": Price(
        "Toll rolling charge (اجرت نورد), small batch", 10_000, 20_000, 35_000, "Toman/kg",
        "ESTIMATE (UNKNOWN: no workshop publishes a rate)",
        "market research s3; bracket only - the model reports the break-even rate instead"),
    "toll_fixed": Price(
        "Toll campaign fixed cost (setup, furnace heat-up, transport, 1 trip)",
        30e6, 60e6, 120e6, "Toman/campaign", "ESTIMATE", "no published figure; bracket"),
    "usd": Price("Free-market USD", 166_000, 228_000, 241_000, "Toman/USD",
                 "DAILY-MARKET-LIST (conflicting channels)",
                 "nournews 2026-09-19: 228,000 free market; 166,000 'tavafoghi' channel"),
    "capex_usd": Price(
        "Own small line CAPEX (mill S1 + batch furnace + tables + leveller + shear + "
        "install + import)", 150_000, 250_000, 400_000, "USD",
        "ESTIMATE", "Chinese small hot-mill listings USD 20-128k (ADVERTISED, 2026-09-28, "
        "not an exact spec match) + furnace, auxiliaries, foundation, freight, duties"),
    "labour_month": Price(
        "Operator cost incl. overheads", 26e6, 35e6, 45e6, "Toman/person-month", "ESTIMATE",
        "1405 statutory package ~26.15M Toman/month (married, 2 children); skilled premium "
        "UNKNOWN"),
    "energy_var": Price(
        "Energy (gas reheat + mill electricity) per kg input", 300, 800, 2_000, "Toman/kg",
        "ESTIMATE (tariffs not retrieved)",
        "~1.5-3 GJ/t batch-furnace gas + 30-60 kWh/t; Iranian industrial tariffs UNKNOWN "
        "this session; bracket is wide on purpose and still small vs the margin"),
    "testing_pilot": Price(
        "Pilot testing (chemistry/PMI, 3 tensile, 3 bend, hardness, metallography)",
        15e6, 30e6, 60e6, "Toman", "ESTIMATE", "lab price list not retrieved"),
}

LABOUR_PER_SHIFT = (3, 4, 5)          # persons: furnace, mill, handling/QC (ASSUMPTION)
SHIFT_HOURS_YEAR = 250 * 8            # 1 shift
MAINT_FRAC_CAPEX = (0.03, 0.05, 0.08)  # per year incl. rolls (ESTIMATE)
AMORT_YEARS = 5                        # simple, no financing cost (ASSUMPTION)


def _plate_price(target: float, which: str) -> float:
    p = PRICES[{6.0: "plate_6", 8.0: "plate_8", 10.0: "plate_10"}[target]]
    return {"low": p.low, "nom": p.nom, "high": p.high}[which]


# --------------------------------------------------------------------------------------
# Engineering inputs, recomputed from reroll_study (not copied)
# --------------------------------------------------------------------------------------
def engineering_inputs() -> dict:
    """Net saleable yield (range) and S1 capacity per conversion, from reroll_study."""
    out = {}
    for piece, target in rs.CONVERSIONS:
        run = rs.simulate(piece, target, "S1")
        y = {c: rs.yield_breakdown(run, c)["yield"] for c in ("low", "nominal", "high")}
        cap = rs.capacity(run)
        out[(piece, target)] = {"yield": y, "kg_per_h_input": cap["kg_per_h_input"]
                                if "kg_per_h_input" in cap else cap.get("kg_per_h"),
                                "scale_pct": rs.yield_breakdown(run)["scale_pct"]}
    return out


# --------------------------------------------------------------------------------------
# Value per kg of INPUT for each route
# --------------------------------------------------------------------------------------
def value_uplift_per_kg(target: float, y: float, case: str) -> float:
    """Revenue per kg input from rolling (product + crop sold as scrap), minus the value
    the same kg has if simply sold as scrap (the opportunity cost). Before conversion
    cost. case 'low' = pessimistic on every price, 'high' = optimistic."""
    pick = {"low": ("low", "low", "high"), "nom": ("nom", "nom", "nom"),
            "high": ("high", "high", "low")}[case]
    plate = _plate_price(target, pick[0])
    disc = getattr(PRICES["product_discount"], {"low": "low", "nom": "nom", "high": "high"}[pick[1]])
    scrap = getattr(PRICES["scrap_heavy"], {"low": "low", "nom": "nom", "high": "high"}[pick[2]])
    scale_loss = 0.03  # of input, not recoverable (reroll_study: 2.6-4 % per heat)
    crop_scrap = max(0.0, 1.0 - y - scale_loss)
    revenue = y * plate * disc + crop_scrap * scrap
    return revenue - scrap


def alternative_offcut_premium(case: str = "nom") -> float:
    """Selling as usable offcut instead of scrap: the no-rolling upside (option E)."""
    return getattr(PRICES["offcut_usable"], {"low": "low", "nom": "nom", "high": "high"}[case]) \
        - PRICES["scrap_heavy"].nom


def own_line_fixed_cost_per_year(case: str = "nom", shifts: int = 1) -> float:
    i = {"low": 0, "nom": 1, "high": 2}[case]
    k = {"low": "low", "nom": "nom", "high": "high"}[case]
    capex_toman = getattr(PRICES["capex_usd"], k) * PRICES["usd"].nom
    labour = LABOUR_PER_SHIFT[i] * shifts * 12 * getattr(PRICES["labour_month"], k)
    return capex_toman / AMORT_YEARS + MAINT_FRAC_CAPEX[i] * capex_toman + labour


def breakeven_tonnage_own_line(uplift: float, case: str = "nom") -> float | None:
    var = getattr(PRICES["energy_var"], {"low": "low", "nom": "nom", "high": "high"}[case])
    margin = uplift - var
    if margin <= 0:
        return None
    return own_line_fixed_cost_per_year(case) / margin / 1000.0  # t/yr


def breakeven_toll_rate(uplift: float) -> float:
    """Maximum toll charge per kg at which rolling still beats selling as scrap."""
    return uplift


def toll_campaign_breakeven_t(uplift: float, rate: float, fixed: float) -> float | None:
    margin = uplift - rate
    return None if margin <= 0 else fixed / margin / 1000.0


def pilot_economics(uplift: float) -> dict:
    kg = 100.0
    cost = PRICES["toll_fixed"].nom + PRICES["testing_pilot"].nom + kg * PRICES["toll_rate"].nom
    return {"kg": kg, "cost_toman": cost, "value_created_toman": kg * uplift,
            "net_toman": kg * uplift - cost}


def decision_table() -> dict:
    eng = engineering_inputs()
    rows = []
    for (piece, target), e in eng.items():
        # yield_breakdown cases name the LOSS level: 'low' loss = best yield. Pessimistic
        # prices pair with high losses and vice versa.
        u = {c: value_uplift_per_kg(target, e["yield"][cy], c)
             for c, cy in (("low", "high"), ("nom", "nominal"), ("high", "low"))}
        off = PRICES["offcut_usable"].nom - PRICES["scrap_heavy"].nom
        rows.append({
            "conv": f"{piece} {rs.PIECES[piece].thickness_mm:g}->{target:g}",
            "yield": e["yield"], "kg_h": e["kg_per_h_input"], "uplift": u,
            "toll_breakeven_rate": breakeven_toll_rate(u["nom"]),
            # pessimistic: low uplift with HIGH cost; optimistic: high uplift with LOW cost
            "own_line_breakeven_t": {"nom": breakeven_tonnage_own_line(u["nom"], "nom"),
                                     "low": breakeven_tonnage_own_line(u["low"], "high")},
            # against the better no-rolling alternative (sell as usable offcut)
            "own_line_vs_offcut_t": breakeven_tonnage_own_line(u["nom"] - off, "nom"),
            "toll_net_vs_scrap": u["nom"] - PRICES["toll_rate"].nom,
            "toll_net_vs_offcut": u["nom"] - PRICES["toll_rate"].nom - off,
            "toll_campaign_breakeven_t": toll_campaign_breakeven_t(
                u["nom"], PRICES["toll_rate"].nom, PRICES["toll_fixed"].nom),
        })
    return {"rows": rows, "offcut_premium": {c: alternative_offcut_premium(c) for c in ("low", "nom", "high")},
            "pilot": pilot_economics(sorted(r["uplift"]["nom"] for r in rows)[len(rows) // 2]),
            "fixed_own_line_nom": own_line_fixed_cost_per_year("nom")}


def _t(v):
    return "n/a (no margin)" if v is None else f"{v:,.0f}"


def build_report() -> str:
    d = decision_table()
    L = []
    w = L.append
    w("# PRJ-STEEL-REROLL-01: economics and decision rule [PC]\n")
    w(f"Generated {STUDY_DATE} by `reroll_economics.py`. All values are concept estimates, not "
      "quotes. The Toman prices are a one-week snapshot. The conclusions rest on **ratios and "
      "break-even tonnages**, which move far less than absolute prices.\n")
    w("## 1. Price inputs\n")
    w("| Input | Low | Nominal | High | Unit | Evidence | Source |\n|---|---|---|---|---|---|---|")
    for p in PRICES.values():
        w(f"| {p.key} | {p.low:,.2f} | {p.nom:,.2f} | {p.high:,.2f} | {p.unit} | {p.evidence} | {p.source} |")
    w("\n## 2. Value added by rolling, per kg of input (before conversion cost)\n")
    w("Definition: (net yield × new-plate price × value ratio for rerolled pieces) + (crop sold as "
      "scrap) − (value of the same kg sold as scrap). Net yield comes from `reroll_study` "
      "(low / nominal / high loss cases). Mill capacity is scenario S1 (Ø400 two-high reversing).\n")
    w("| Conversion | Net yield worst/nom/best | Uplift vs scrap: pessimistic | nominal | optimistic | Max toll rate vs scrap | Toll net vs scrap / vs offcut (nom) | Own line break-even t/yr: vs scrap nom / pessimistic / vs offcut nom |\n|---|---|---|---|---|---|---|---|")
    for r in d["rows"]:
        y = r["yield"]; u = r["uplift"]; be = r["own_line_breakeven_t"]
        w(f"| {r['conv']} | {y['high']:.0%} / {y['nominal']:.0%} / {y['low']:.0%} | {u['low']:,.0f} | "
          f"{u['nom']:,.0f} | {u['high']:,.0f} | {r['toll_breakeven_rate']:,.0f} | "
          f"{r['toll_net_vs_scrap']:,.0f} / {r['toll_net_vs_offcut']:,.0f} | "
          f"{_t(be['nom'])} / {_t(be['low'])} / {_t(r['own_line_vs_offcut_t'])} |")
    op = d["offcut_premium"]
    w(f"\n**Option E, no rolling:** selling the pieces as usable offcut (ته‌ورق) instead of scrap is "
      f"worth {op['low']:,.0f} / {op['nom']:,.0f} / {op['high']:,.0f} Toman/kg (L/N/H). This needs "
      "no equipment, no energy and no testing.\n")
    w(f"**Own small line:** fixed cost at nominal is about {d['fixed_own_line_nom'] / 1e9:,.1f} billion "
      f"Toman/yr for one shift ({AMORT_YEARS}-year simple amortisation of CAPEX, maintenance and "
      "labour).\n")
    p = d["pilot"]
    w(f"**Pilot (about 100 kg, toll + tests):** cost about {p['cost_toman'] / 1e6:,.0f} M Toman against "
      f"value created of about {p['value_created_toman'] / 1e6:,.1f} M Toman. The pilot is an "
      "**information purchase**. It pays back only if a large recurring tonnage follows.\n")
    rows = d["rows"]
    med = lambda xs: sorted(xs)[len(xs) // 2]
    u_nom = med([r["uplift"]["nom"] for r in rows])
    off = PRICES["offcut_usable"].nom - PRICES["scrap_heavy"].nom
    toll = PRICES["toll_rate"].nom
    fixed_campaign = PRICES["toll_fixed"].nom + PRICES["testing_pilot"].nom
    toll_t_vs_scrap = toll_campaign_breakeven_t(u_nom, toll, fixed_campaign)
    toll_max_rate_vs_offcut = u_nom - off
    own_vs_scrap = med([r["own_line_breakeven_t"]["nom"] for r in rows])
    own_vs_scrap_pess = med([r["own_line_breakeven_t"]["low"] or 1e9 for r in rows])
    own_vs_off = med([r["own_line_vs_offcut_t"] for r in rows])
    d["thresholds"] = {"toll_t_vs_scrap": toll_t_vs_scrap, "toll_max_rate_vs_offcut": toll_max_rate_vs_offcut,
                       "own_vs_scrap": own_vs_scrap, "own_vs_scrap_pess": own_vs_scrap_pess,
                       "own_vs_off": own_vs_off}
    w("## 3. Decision rule by tonnage and by what the pieces can be sold as (HP-01, HP-03)\n")
    w(f"Median across the 9 conversions, nominal case: rolling adds **{u_nom:,.0f} Toman/kg** over "
      f"scrap value. A usable-offcut sale adds **{off:,.0f} Toman/kg** over scrap with no rolling.\n")
    w("| If the pieces can only be sold as... | Toll rolling pays when | Own small line pays when |\n|---|---|---|")
    w(f"| **scrap** (~{PRICES['scrap_heavy'].nom:,.0f} Toman/kg) | the lot exceeds **~{toll_t_vs_scrap:,.1f} t** "
      f"per campaign at a {toll:,.0f} Toman/kg rate, including one pilot's fixed cost | recurring supply above "
      f"**~{own_vs_scrap:,.0f} t/yr** at nominal prices (~{own_vs_scrap_pess:,.0f} t/yr pessimistic) |")
    w(f"| **usable offcut** (~{PRICES['offcut_usable'].nom:,.0f} Toman/kg) | only if the toll rate is below "
      f"**~{toll_max_rate_vs_offcut:,.0f} Toman/kg**; otherwise selling as offcut wins | recurring supply "
      f"above **~{own_vs_off:,.0f} t/yr** |")
    w("\n## 4. Sensitivity notes\n")
    w("- The **value ratio of rerolled pieces** (HP-03) is the dominant unknown. At 0.70 several "
      "conversions barely beat scrap.\n")
    w("- **Energy** is under 3 % of the margin even at the high bracket. The missing tariff does not change "
      "any decision.\n")
    w("- **Toll rate:** no workshop publishes one. The table gives the maximum affordable rate instead "
      "of a guessed rate.\n")
    w("- **USD rate:** the free-market and 'tavafoghi' channels differ by about 30 %. This only shifts the own-line "
      "break-even (CAPEX is in USD). The ranking of routes does not change.\n")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------------------
# Phase 1.5 (2026-09-30): full decision identity, all costs explicit
# --------------------------------------------------------------------------------------
# Every value is an ESTIMATE or ASSUMPTION (Toman per kg of INPUT unless stated); none is a quote.
CLOSURE_COSTS = {
    #          low     high     basis
    "H": (1_000, 3_000),    # transport round trip per kg, campaign scale (ASSUMPTION)
    "R": (0, 3_000),        # extra reheat charge if billed separately (ASSUMPTION)
    "L": (1_500, 3_000),    # cropping + levelling per kg (ASSUMPTION)
    "Q": (1_000, 4_000),    # QC tests spread over the campaign lot (ESTIMATE)
    "r": (0.0, 0.15),       # reject fraction of rolled product, sold as scrap (ASSUMPTION)
    "s": (0.03, 0.06),      # scale loss of input, no value (reroll_study 2.6-4 %; 05 doc 3-6 %)
    "months": (1, 3),       # capital tied up (ASSUMPTION)
}
FIN_RATE_MONTH = 0.03       # cost of money per month, ~36 %/yr (ASSUMPTION)
P_STD = 125_000             # standard 6-10 mm plate, mid of DAILY-MARKET-LIST 120-131k (ADVERTISED)
P_SCR = 54_000              # heavy scrap buyer posting, mesterahan 2026-09-28 (ADVERTISED)


def closure_delta(p_in, k, y, toll, *, H, R, L, Q, r, s, months,
                  p_std=P_STD, p_scr=P_SCR, fin=FIN_RATE_MONTH):
    """Advantage of toll re-rolling over selling the piece as it is, per kg of input.

    revenue = y(1-r)*k*p_std + (y*r + max(0, 1-y-s))*p_scr   # product + rejects/crop as scrap
    costs   = toll + H + R + L + Q + F,  F = (p_in + toll + H + R + L + Q) * fin * months
    delta   = revenue - costs - p_in                            # > 0: roll; < 0: sell as is
    """
    revenue = y * (1 - r) * k * p_std + (y * r + max(0.0, 1 - y - s)) * p_scr
    outlay = toll + H + R + L + Q
    F = (p_in + outlay) * fin * months
    return revenue - outlay - F - p_in


def _cost_case(which: str) -> dict:
    i = 0 if which == "low" else 1
    return {k: v[i] for k, v in CLOSURE_COSTS.items()}


def closure_verdict(p_in, k, y, toll) -> str:
    """ROLL if it pays even with high other costs; SELL if it loses even with low ones."""
    best = closure_delta(p_in, k, y, toll, **_cost_case("low"))
    worst = closure_delta(p_in, k, y, toll, **_cost_case("high"))
    if worst > 0:
        return "ROLL"
    if best < 0:
        return "SELL"
    return "UNCLEAR"


def closure_threshold_toll(p_in, k, y, which="nom") -> float:
    """Maximum toll rate (Toman/kg) at which rolling still breaks even (delta = 0)."""
    if which == "nom":
        c = {k2: (v[0] + v[1]) / 2 for k2, v in CLOSURE_COSTS.items()}
    else:
        c = _cost_case(which)
    lo, hi = -200_000.0, 200_000.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if closure_delta(p_in, k, y, mid, **c) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


CLOSURE_GRID = {"p_in": (60_000, 75_000, 90_000), "k": (0.70, 0.82, 0.92),
                "y": (0.60, 0.70, 0.80, 0.90), "toll": (5_000, 10_000, 15_000, 20_000, 30_000)}


def closure_table() -> list:
    g = CLOSURE_GRID
    return [{"p_in": p, "k": k, "cells": [[closure_verdict(p, k, y, t) for t in g["toll"]] for y in g["y"]]}
            for p in g["p_in"] for k in g["k"]]


def pilot_breakdown() -> list:
    """Bottom-up pilot cost (Toman). Fixed items do not scale with kg; variable items do."""
    items = [  # name, fixed (low, nom, high), variable per kg (low, nom, high), basis
        ("حمل رفت و برگشت (تا ۱٫۵ تن یک سفر)", (6e6, 10e6, 15e6), (0, 0, 0), "ASSUMPTION"),
        ("آماده‌سازی: شماره‌گذاری، اندازه‌گیری، برس یا ساچمه", (1e6, 3e6, 5e6), (500, 1_000, 2_000), "ASSUMPTION"),
        ("کوره: گرم‌کردن برای یک نوبت کوچک", (8e6, 15e6, 25e6), (0, 0, 0), "ESTIMATE"),
        ("اجرت نورد", (0, 0, 0), (5_000, 20_000, 35_000), "ESTIMATE (بدون نرخ منتشرشده)"),
        ("حداقل هزینهٔ پذیرش کارگاه (راه‌اندازی، تنظیم غلتک)", (10e6, 25e6, 40e6), (0, 0, 0), "ESTIMATE"),
        ("برش سر و ته و لولر", (2e6, 5e6, 8e6), (1_000, 2_000, 3_000), "ASSUMPTION"),
        ("آنالیز شیمیایی (۴ نمونه: یکی از هر گروه + مرجع)", (4e6, 6e6, 12e6), (0, 0, 0), "ESTIMATE"),
        ("کشش ۳ + خمش ۳", (6e6, 9e6, 15e6), (0, 0, 0), "ESTIMATE"),
        ("متالوگرافی ۱ + سختی", (3e6, 6e6, 10e6), (0, 0, 0), "ESTIMATE"),
        ("سایر: ماشین‌کاری نمونه، هماهنگی، گزارش", (3e6, 7e6, 12e6), (0, 0, 0), "ASSUMPTION"),
    ]
    return items


def pilot_cost(kg: float, case: str = "nom") -> float:
    i = {"low": 0, "nom": 1, "high": 2}[case]
    return sum(fx[i] + var[i] * kg for _, fx, var, _ in pilot_breakdown())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report")
    a = ap.parse_args(argv)
    text = build_report()
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"report -> {a.report}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
