import reroll_economics as ec


def test_uplift_ordering_pessimistic_nominal_optimistic():
    for r in ec.decision_table()["rows"]:
        u = r["uplift"]
        assert u["low"] < u["nom"] < u["high"], r["conv"]


def test_yield_case_mapping_is_not_inverted():
    # 'low' loss case = best yield; the pessimistic uplift must use the WORST yield.
    for r in ec.decision_table()["rows"]:
        assert r["yield"]["high"] < r["yield"]["nominal"] < r["yield"]["low"], r["conv"]


def test_breakeven_tonnage_is_fixed_cost_over_margin():
    u = 36_000.0
    t = ec.breakeven_tonnage_own_line(u, "nom")
    margin = u - ec.PRICES["energy_var"].nom
    assert abs(t * 1000 * margin - ec.own_line_fixed_cost_per_year("nom")) < 1.0


def test_no_margin_gives_no_breakeven():
    assert ec.breakeven_tonnage_own_line(100.0, "nom") is None
    assert ec.toll_campaign_breakeven_t(10_000, 20_000, 1e6) is None


def test_offcut_baseline_raises_the_own_line_threshold():
    for r in ec.decision_table()["rows"]:
        assert r["own_line_vs_offcut_t"] > r["own_line_breakeven_t"]["nom"]


def test_every_price_has_evidence_and_source():
    for p in ec.PRICES.values():
        assert p.evidence and p.source and p.low <= p.nom <= p.high, p.key


def test_report_builds_and_states_it_is_not_a_quote():
    txt = ec.build_report()
    assert "not quotes" in txt and "## 3." in txt


# --- Phase 1.5 decision closure (2026-09-30) ---------------------------------------
def test_closure_zero_costs_reproduces_gross_uplift_over_offcut():
    import reroll_economics as e
    d = e.closure_delta(75_000, 0.82, 0.78, 0, H=0, R=0, L=0, Q=0, r=0, s=0.03, months=0)
    # run-1 gross threshold vs offcut was ~15.6k Toman/kg; same identity, same order
    assert 13_000 < d < 18_000


def test_closure_threshold_falls_when_costs_are_added():
    import reroll_economics as e
    gross = e.closure_delta(75_000, 0.82, 0.78, 0, H=0, R=0, L=0, Q=0, r=0, s=0.03, months=0)
    assert e.closure_threshold_toll(75_000, 0.82, 0.78) < gross - 10_000


def test_closure_monotonic():
    import reroll_economics as e
    c = e._cost_case("low")
    assert e.closure_delta(60_000, 0.82, 0.8, 10_000, **c) > e.closure_delta(75_000, 0.82, 0.8, 10_000, **c)
    assert e.closure_delta(60_000, 0.92, 0.8, 10_000, **c) > e.closure_delta(60_000, 0.70, 0.8, 10_000, **c)
    assert e.closure_delta(60_000, 0.82, 0.8, 5_000, **c) > e.closure_delta(60_000, 0.82, 0.8, 20_000, **c)


def test_closure_verdict_logic_and_grid_size():
    import reroll_economics as e
    assert e.closure_verdict(90_000, 0.70, 0.60, 30_000) == "SELL"
    assert e.closure_verdict(60_000, 0.92, 0.90, 5_000) == "ROLL"
    t = e.closure_table()
    assert len(t) == 9 and all(len(r["cells"]) == 4 and len(r["cells"][0]) == 5 for r in t)


def test_pilot_cost_fixed_dominates_and_scales():
    import reroll_economics as e
    c100, c500, c1000 = (e.pilot_cost(kg) for kg in (100, 500, 1000))
    assert c100 < c500 < c1000
    assert c100 / 100 > 5 * (c1000 / 1000)  # per-kg cost collapses with batch size
    assert 80e6 < c100 < 100e6               # consistent with run-1 lump of ~92 M
