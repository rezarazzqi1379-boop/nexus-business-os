import pytest
from caliber_spread_model import PassMeasurement, SYNTHETIC_PREFIX, diagnose_width_mechanism
from steel_measurement_intake import (
    MIN_BILLETS_FOR_TIMING, BilletRun, CampaignFacts, EventKind, MeasurementCampaign,
    TimingEvent, campaign_completeness, pass_measurements, timing_summary,
)


def ev(kind, t, p=None):
    return TimingEvent(kind=kind, t_seconds=t, pass_index=p)


def make_run(bid="B-001", n_passes=3, pass_s=3.0, handle_s=6.0, src="video:shift-A", synth=False):
    events, t = [ev(EventKind.FURNACE_EXIT, 0.0)], 5.0
    passes = []
    h, b = 150.0, 150.0
    for i in range(1, n_passes + 1):
        events.append(ev(EventKind.PASS_START, t, i)); t += pass_s
        events.append(ev(EventKind.PASS_END, t, i)); t += handle_s
        events.append(ev(EventKind.MANIPULATION, t, i))
        nh, nb = h * 0.85, b * 1.10
        passes.append(PassMeasurement(
            pass_index=i, entry_thickness_mm=h, exit_thickness_mm=nh,
            entry_width_mm=b, exit_width_mm=nb, roll_diameter_mm=518.0,
            source=(f"{SYNTHETIC_PREFIX}test" if synth else "video:shift-A frame 100"),
            temperature_c=1120.0))
        h, b = nh, nb
    events.append(ev(EventKind.PIECE_CLEAR, t + 2.0))
    return BilletRun(billet_id=bid, events=tuple(events), passes=tuple(passes),
                     source=(f"{SYNTHETIC_PREFIX}{src}" if synth else src))


def campaign(n=MIN_BILLETS_FOR_TIMING, facts=None, synth=False):
    runs = tuple(make_run(f"B-{i:03d}", synth=synth) for i in range(n))
    return MeasurementCampaign("M1", runs, facts or CampaignFacts())


# --- timing / P-1 ---------------------------------------------------------

def test_cycle_and_rolling_time_are_separated():
    r = make_run(n_passes=3, pass_s=3.0, handle_s=6.0)
    assert r.rolling_seconds == pytest.approx(9.0)
    assert r.non_rolling_seconds > r.rolling_seconds
    assert 0 < r.handling_fraction < 1


def test_handling_fraction_is_the_headline_number():
    r = make_run(n_passes=7, pass_s=2.5, handle_s=6.0)
    assert r.handling_fraction > 0.6, "handling should dominate - that is the finding"


def test_small_sample_is_refused_as_a_capacity_figure():
    s = timing_summary(campaign(n=5))
    assert s["sufficient_sample"] is False
    assert s["capacity_grade"] is False
    assert "must not be used as a capacity figure" in s["note"]


def test_sufficient_sample_is_accepted():
    s = timing_summary(campaign(n=MIN_BILLETS_FOR_TIMING))
    assert s["sufficient_sample"] is True
    assert "may be used to replace the assumed" in s["note"]


def test_sample_threshold_matches_the_independent_review_condition():
    assert MIN_BILLETS_FOR_TIMING == 20


# --- evidence discipline --------------------------------------------------

def test_anonymous_billet_run_is_rejected():
    r = make_run()
    with pytest.raises(ValueError, match="no anonymous data"):
        BilletRun(r.billet_id, r.events, r.passes, "  ").validate()


def test_synthetic_campaign_is_flagged_everywhere():
    c = campaign(synth=True)
    assert c.is_synthetic is True
    assert timing_summary(c)["illustrative_only"] is True
    assert campaign_completeness(c)["illustrative_only"] is True


def test_real_campaign_is_not_flagged():
    assert campaign(synth=False).is_synthetic is False


def test_events_must_be_time_ordered():
    bad = (ev(EventKind.FURNACE_EXIT, 10.0), ev(EventKind.PIECE_CLEAR, 1.0))
    with pytest.raises(ValueError, match="ascending time order"):
        BilletRun("B", bad, (), "video:x").validate()


def test_duplicate_billet_ids_are_rejected():
    r = make_run("SAME")
    with pytest.raises(ValueError, match="duplicate billet_id"):
        MeasurementCampaign("M1", (r, r), CampaignFacts()).validate()


def test_negative_time_is_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        ev(EventKind.PASS_START, -1.0).validate()


def test_empty_campaign_is_rejected():
    with pytest.raises(ValueError, match="at least one billet run"):
        MeasurementCampaign("M1", (), CampaignFacts()).validate()


# --- facts: None means NOT COLLECTED, never a default ---------------------

def test_uncollected_facts_are_reported_missing_not_defaulted():
    f = CampaignFacts()
    assert "roll_material" in f.missing()
    assert "stand_rated_force_kn" in f.missing()
    assert f.collected() == ()


def test_collected_facts_move_from_missing_to_collected():
    f = CampaignFacts(roll_material="forged steel", stand_rated_force_kn=2600.0)
    assert "roll_material" in f.collected()
    assert "roll_material" not in f.missing()


# --- completeness ---------------------------------------------------------

def test_bare_campaign_is_incomplete_and_names_what_is_missing():
    c = campaign_completeness(campaign())
    assert c["complete"] is False
    for expected in ("P-3 roll material", "BM-1 stand force rating", "IR-2 stator/rotor split"):
        assert expected in c["outstanding"]


def test_stand_force_rating_is_a_campaign_obligation():
    """Added after the Ternium-Siderar benchmark: an old stand pushed past its
    original force rating fails at the bearings and roll necks."""
    assert "BM-1 stand force rating" in campaign_completeness(campaign())["outstanding"]


def test_fully_equipped_campaign_reports_complete():
    facts = CampaignFacts(
        stand_rated_force_kn=2600.0, roll_material="forged steel", roll_hardness="55 HSD",
        st2_motor_rpm=750.0, st2_motor_kw=800.0,
        motor_nameplate_stator_v=6000.0, motor_nameplate_stator_a=140.0,
        motor_nameplate_rotor_v=420.0, motor_nameplate_rotor_a=2300.0,
        gearbox_rated_torque_nm=150000.0, bearing_rating_locator="oem:sheet-12",
        groove_drawing_locator="cad:grooves.pdf", nameplate_photo_locators=("photo:st2",))
    c = campaign_completeness(campaign(facts=facts))
    assert c["complete"] is True
    assert c["percent_complete"] == 100


def test_completeness_never_claims_to_open_a_gate():
    c = campaign_completeness(campaign())
    assert "does NOT by itself open any fabrication" in c["note"]


# --- handoff to IC-02 -----------------------------------------------------

def test_pass_measurements_feed_the_caliber_model():
    passes = pass_measurements(campaign(n=2))
    assert len(passes) >= 2
    result = diagnose_width_mechanism(passes[:3])
    assert "mechanism" in result


def test_pass_measurements_needs_at_least_two():
    run = BilletRun("B-1", (ev(EventKind.FURNACE_EXIT, 0.0), ev(EventKind.PIECE_CLEAR, 1.0)),
                    (), "video:x")
    with pytest.raises(ValueError, match="at least two measured passes"):
        pass_measurements(MeasurementCampaign("M1", (run,), CampaignFacts()))
