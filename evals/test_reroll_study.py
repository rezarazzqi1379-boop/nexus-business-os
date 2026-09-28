"""PRJ-STEEL-REROLL-01 - tests for reroll_study.py (concept calculations).

These pin the physics invariants and the evidence rules, not the concept
numbers themselves: mass conservation, the brief's s4 geometry, the bite
check, monotonic force, cooling, reheat trend, schedule legality, option C.
"""
import math

import pytest

import reroll_study as rs
import slab_line_design as sld

COLD_SIDE = rs.Thermal(finish_min_c=850.0, emissivity=rs.EMISSIVITY_RANGE[1],
                       h_gap=rs.H_GAP_RANGE[1], interpass_s=12.0, transfer_s=40.0,
                       first_heat_c=1150.0, reheat_c=1150.0)


# ---------------------------------------------------------------------------
# 1. Mass conservation
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("pk,t", rs.CONVERSIONS)
def test_rolled_volume_equals_input_volume_with_spread_on(pk, t):
    run = rs.simulate(pk, t, "S1")
    p = rs.PIECES[pk]
    f = run.final
    v_out = f.exit_h * f.exit_b * f.exit_len_mm
    assert v_out == pytest.approx(p.volume_mm3, rel=1e-9)
    assert f.exit_mass_kg == pytest.approx(p.mass_kg, rel=1e-9)


@pytest.mark.parametrize("case", ["low", "nominal", "high"])
@pytest.mark.parametrize("pk,t", rs.CONVERSIONS)
def test_yield_breakdown_closes_exactly(pk, t, case):
    """volume in = volume out + losses, as mass."""
    run = rs.simulate(pk, t, "S1")
    y = rs.yield_breakdown(run, case)
    parts = y["scale_kg"] + y["crop_kg"] + y["trim_kg"] + y["oot_kg"] + y["saleable_kg"]
    assert parts == pytest.approx(y["input_kg"], rel=1e-12)
    assert all(y[k] >= 0 for k in ("scale_kg", "crop_kg", "trim_kg", "oot_kg", "saleable_kg"))
    assert 0.0 < y["yield"] < 1.0


@pytest.mark.parametrize("pk,t", rs.CONVERSIONS)
def test_yield_range_is_ordered(pk, t):
    run = rs.simulate(pk, t, "S1")
    lo_loss = rs.yield_breakdown(run, "low")["yield"]
    nom = rs.yield_breakdown(run, "nominal")["yield"]
    hi_loss = rs.yield_breakdown(run, "high")["yield"]
    assert lo_loss > nom > hi_loss


def test_losses_off_gives_full_yield_geometry():
    run = rs.simulate("B", 6.0, "S1")
    y = rs.yield_breakdown(run, "nominal", include_scale=False)
    assert y["scale_kg"] == 0.0


# ---------------------------------------------------------------------------
# 2. Brief s4 table
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("pk,t", rs.CONVERSIONS)
def test_theoretical_length_matches_brief_s4(pk, t):
    lf = rs.theoretical_length_mm(rs.PIECES[pk], t)
    assert abs(lf - rs.BRIEF_S4_LENGTH_MM[(pk, t)]) <= 0.5


@pytest.mark.parametrize("pk,t", rs.CONVERSIONS)
@pytest.mark.parametrize("kind", ["brief", "recommended"])
def test_simulated_length_equals_s4_when_spread_and_losses_off(pk, t, kind):
    run = rs.simulate(pk, t, "S1", kind, spread=False)
    assert run.final.exit_b == rs.PIECES[pk].width_mm
    assert run.final.exit_len_mm == pytest.approx(rs.theoretical_length_mm(rs.PIECES[pk], t),
                                                  rel=1e-12)


def test_brief_masses_and_reductions_reproduced():
    for k, p in rs.PIECES.items():
        assert p.mass_kg == pytest.approx(rs.BRIEF_S4_MASS_KG[k], abs=0.005)
    for (h0, hf), (red, factor) in rs.BRIEF_S4_REDUCTION.items():
        assert rs.reduction_pct(h0, hf) == pytest.approx(red, abs=0.05)
        assert h0 / hf == pytest.approx(factor, abs=0.0005)


def test_brief_s5_schedules_start_and_end_on_the_conversion():
    for (pk, t), seq in rs.BRIEF_S5_SCHEDULES.items():
        assert seq[0] == rs.PIECES[pk].thickness_mm
        assert seq[-1] == t
        assert all(a > b for a, b in zip(seq, seq[1:]))


# ---------------------------------------------------------------------------
# 3. Bite
# ---------------------------------------------------------------------------
def test_bite_check_fails_for_an_absurd_draft():
    assert not rs.bite_ok(30.0, 400.0, mu=0.35)
    assert not rs.bite_ok(15.0, 350.0, mu=0.25)
    assert not rs.bite_ok(500.0, 400.0, mu=0.35)      # draft larger than the roll
    assert rs.mu_required(30.0, 400.0) > 0.35


def test_bite_check_passes_a_normal_draft_and_uses_exact_limit():
    assert rs.bite_ok(4.0, 400.0, mu=0.25)
    exact = rs.bite_limit_mm(0.25, 400.0)
    approx = sld.max_draft_bite_mm(0.25, roll_diameter_mm=400.0)
    assert exact < approx                              # the mu^2 R form overstates
    assert rs.bite_ok(exact - 1e-6, 400.0, mu=0.25)
    assert not rs.bite_ok(exact + 0.01, 400.0, mu=0.25)


def test_mu_required_matches_bite_angle():
    for draft in (1.0, 3.0, 6.0):
        a = math.acos(1 - draft / 400.0)
        assert rs.mu_required(draft, 400.0) == pytest.approx(math.tan(a))


# ---------------------------------------------------------------------------
# 4. Force monotonic in draft and flow stress
# ---------------------------------------------------------------------------
def test_force_monotonic_in_draft():
    forces = [rs.pass_mechanics(20.0, 20.0 - d, 300.0, 1100.0, 400.0, 0.6, 0.30,
                                "S235JR")["force"] for d in (0.5, 1, 2, 3, 4, 5, 6)]
    assert all(b > a for a, b in zip(forces, forces[1:]))


def test_force_monotonic_in_flow_stress():
    f = [rs.roll_force_n(s, 300.0, 25.0, 12.0, 0.3)[0] for s in (50, 100, 150, 200, 300)]
    assert all(b > a for a, b in zip(f, f[1:]))
    hot = rs.pass_mechanics(12.0, 9.5, 250.0, 1100.0, 400.0, 0.6, 0.3, "S235JR")["force"]
    cold = rs.pass_mechanics(12.0, 9.5, 250.0, 900.0, 400.0, 0.6, 0.3, "S235JR")["force"]
    hard = rs.pass_mechanics(12.0, 9.5, 250.0, 1100.0, 400.0, 0.6, 0.3, "S355JR")["force"]
    assert cold > hot and hard > hot


def test_cold_force_rises_with_reduction():
    f = [rs.cold_schedule(20.0, 20.0 * (1 - r), 300.0, 400.0)["peak_force_n"]
         for r in (0.5, 0.6, 0.7)]
    assert f[0] < f[1] < f[2]
    assert rs.cold_flow_stress_mpa(0.0) == pytest.approx(235.0)


# ---------------------------------------------------------------------------
# 5. Thermal
# ---------------------------------------------------------------------------
def test_temperature_falls_with_time():
    temps = [rs.cool_piece(1200.0, 10.0, 250.0, 800.0, t) for t in (0, 5, 10, 20, 40, 80)]
    assert temps[0] == 1200.0
    assert all(b < a for a, b in zip(temps, temps[1:]))


def test_thin_pieces_cool_faster():
    rates = [rs.piece_cooling_rate_c_per_s(h, 250.0, 800.0, 1000.0, 0.85)
             for h in (20.0, 12.0, 8.0, 6.0)]
    assert all(b > a for a, b in zip(rates, rates[1:]))


def test_lumped_model_is_valid_for_all_gauges():
    for h in (6.0, 8.0, 10.0, 12.0, 15.0, 20.0):
        assert sld.biot_number(h, 250.0, 1100.0, emissivity=0.9) < 0.1


def test_roll_chill_scales_inversely_with_thickness():
    assert rs.roll_chill_c(1000.0, 6.0, 0.03) > rs.roll_chill_c(1000.0, 12.0, 0.03) > 0


@pytest.mark.parametrize("pk", ["A", "B", "C"])
def test_reheat_count_rises_as_thickness_falls(pk):
    counts = [rs.simulate(pk, t, "S1", thermal=COLD_SIDE).reheats for t in (10.0, 8.0, 6.0)]
    assert counts[0] <= counts[1] <= counts[2]


def test_reheat_count_strictly_higher_for_the_thinnest_target():
    for pk in ("A", "B"):
        r10 = rs.simulate(pk, 10.0, "S1", thermal=COLD_SIDE).reheats
        r6 = rs.simulate(pk, 6.0, "S1", thermal=COLD_SIDE).reheats
        assert r6 > r10


def test_every_pass_finishes_above_the_limit_or_is_flagged():
    for tf in rs.FINISH_TEMPS_C:
        for pk, t in rs.CONVERSIONS:
            run = rs.simulate(pk, t, "S1", thermal=rs.Thermal(finish_min_c=tf))
            for p in run.passes:
                assert p.exit_temp_c >= tf or (p.below_finish and not run.feasible)


def test_furnace_heating_below_burning_and_overheating_limits():
    assert max(rs.REHEAT_RANGE_C) + rs.FURNACE_MARGIN_C < rs.OVERHEATING_ONSET_C
    assert rs.OVERHEATING_ONSET_C < rs.BURNING_ONSET_C


# ---------------------------------------------------------------------------
# 6. Schedule legality
# ---------------------------------------------------------------------------
def _all_runs():
    for sc in ("S1", "S2", "S3"):
        s = rs.SCENARIOS[sc]
        for d in sorted({s.roll_d_range[0], s.roll_d_mm, s.roll_d_range[1]}):
            for kind in ("brief", "recommended"):
                for pk, t in rs.CONVERSIONS:
                    yield rs.simulate(pk, t, sc, kind, roll_d_mm=d)


def test_no_pass_exceeds_the_bite_limit_in_any_returned_schedule():
    n = 0
    for run in _all_runs():
        for p in run.passes:
            n += 1
            assert p.bite_ok
            assert p.draft <= p.bite_limit_mm + 1e-9
            assert p.mu_required <= rs.MU_RANGE[0]
    assert n > 100
    for c in rs.cold_route().values():
        assert all(p["bite_ok"] for p in c["passes"])


@pytest.mark.parametrize("sc", ["S1", "S2", "S3"])
def test_recommended_schedules_respect_reduction_limits(sc):
    s = rs.SCENARIOS[sc]
    for pk, t in rs.CONVERSIONS:
        seq = rs.design_schedule(rs.PIECES[pk].thickness_mm, t, s)
        reds = [(a - b) / a for a, b in zip(seq, seq[1:])]
        assert all(r <= s.max_reduction + 1e-9 for r in reds)
        assert reds[-1] <= s.last_pass_max_reduction + 1e-9
        assert seq[0] == rs.PIECES[pk].thickness_mm and seq[-1] == t


def test_recommended_never_uses_more_passes_than_the_brief():
    for pk, t in rs.CONVERSIONS:
        rec = rs.schedule_for(pk, t, "recommended", rs.SCENARIOS["S1"])
        assert len(rec) <= len(rs.BRIEF_S5_SCHEDULES[(pk, t)])


# ---------------------------------------------------------------------------
# 7. Option C and isolation
# ---------------------------------------------------------------------------
def test_s2_force_fraction_below_100_percent():
    oc = rs.option_c(rs.s1_nominal())
    assert 0 < oc["force_fraction"] < 1.0
    assert 0 < oc["torque_fraction"] < 1.0


def test_s2_is_recorded_as_not_operational():
    assert "NOT operational" in rs.SCENARIOS["S2"].status
    assert "PROXY" in rs.SCENARIOS["S2"].rating_basis


def test_results_do_not_depend_on_slab_line_defaults(monkeypatch):
    base = rs.simulate("B", 6.0, "S1")
    monkeypatch.setattr(sld, "ROLL_DIAMETER_MM", 999.0)
    monkeypatch.setattr(sld, "PRODUCT_WIDTH_MM", 999.0)
    monkeypatch.setattr(sld, "BARREL_LENGTH_MM", 999.0)
    monkeypatch.setattr(sld, "BEARING_OFFSET_MM", 999.0)
    monkeypatch.setattr(sld, "SLAB_EXIT_TEMP_C", 999.0)
    rs.heat_up.cache_clear()
    again = rs.simulate("B", 6.0, "S1")
    for a, b in zip(base.passes, again.passes):
        assert a == b


def test_explicit_roll_diameter_changes_force():
    small = rs.simulate("B", 6.0, "S1", roll_d_mm=350.0).peak("force_n")
    large = rs.simulate("B", 6.0, "S1", roll_d_mm=450.0).peak("force_n")
    assert large > small


# ---------------------------------------------------------------------------
# 8. Outputs and evidence discipline
# ---------------------------------------------------------------------------
def test_register_uses_only_brief_evidence_classes():
    allowed = ("FACT", "MEASUREMENT", "SUPPLIER CLAIM", "ESTIMATE", "ASSUMPTION",
               "HYPOTHESIS", "UNKNOWN", "CLAIM")
    for row in rs.INPUT_REGISTER:
        assert len(row) == 6
        assert row[3].startswith(allowed), row


def test_cli_writes_report_csv_and_inputs(tmp_path):
    rep, csv_path, inp = tmp_path / "r.md", tmp_path / "p.csv", tmp_path / "i.md"
    assert rs.main(["--report", str(rep), "--csv", str(csv_path), "--inputs", str(inp)]) == 0
    text = rep.read_text(encoding="utf-8")
    assert "خلاصهٔ فارسی" in text
    assert "Nothing here is an operating setpoint" in text
    assert "[RDR]" in text and "[SM]" in text and "[PC]" in text
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("scenario,conversion,schedule")
    assert len(lines) > 100
    assert "| Evidence class |" in inp.read_text(encoding="utf-8")


def test_s1_sizing_margins_cover_the_envelope():
    sizing = rs.s1_sizing(rs.s1_envelope(finish_temps=(800.0,)))
    for s in sizing.values():
        assert s["force_rating_n"][0] > s["force_peak_n"]
        assert s["gearbox_output_rating_nm"] >= s["torque_total_peak_nm"]
        for dv in s["drive"].values():
            assert dv["motor_kw_iec"] >= dv["motor_kw_min"]


def test_option_c_proxy_is_the_slab_line_envelope_duty_not_one_thickness():
    # Independent check 2026-09-28: the proxy was hard-coded as 3.0 MN (the slab line's
    # 30 mm case) and described as its "hot range" duty. It must be recomputed over the
    # whole 6-30 mm envelope, which is the 5.12 MN its stand RFI quotes.
    import slab_line_design as sld
    import reroll_study as rs
    env = max(sld.worst_cases(sld.build_schedule(t, "balanced", grade="S355JR"))["max_force"].force_n
              for t in sld.THICKNESS_TARGETS_MM)
    assert rs.SCENARIOS["S2"].force_rating_n == env
    assert abs(env / 1e6 - 5.12) < 0.01
