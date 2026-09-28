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
