import pytest
from steel_kernel import EpistemicClass
from steel_intake_runner import (
    UNKNOWN_UNLOCK_MAP, EngineerFact, ingest_batch, readiness_report,
)


def fact(**kw):
    base = dict(subject="roll_material", value="forged steel", unit="n/a",
                epistemic_class=EpistemicClass.MEASUREMENT,
                source_locator="roll certificate 2026-10-01")
    base.update(kw)
    return EngineerFact(**base)


def test_empty_batch_is_refused():
    with pytest.raises(ValueError, match="nothing to ingest"):
        ingest_batch([])


def test_unknown_id_not_in_the_map_is_rejected():
    with pytest.raises(ValueError, match="not in the unlock map"):
        fact(closes_unknown="something_invented").validate()


def test_a_measurement_closes_its_unknown():
    r = ingest_batch([fact(closes_unknown="roll_material")])
    assert "roll_material" in r.unknowns_closed
    assert "roll_material" not in r.unknowns_remaining


def test_a_claim_contradicting_a_measurement_does_NOT_close_the_unknown():
    """The heart of the discipline: weaker evidence does not settle a question."""
    r = ingest_batch([fact(
        subject="roll_diameter", value=550.0, unit="mm",
        epistemic_class=EpistemicClass.CLAIM, source_locator="engineer recollection",
        existing_value=518.0, existing_class=EpistemicClass.MEASUREMENT,
        closes_unknown="groove_geometry")])
    assert "groove_geometry" not in r.unknowns_closed
    assert r.contradictions
    assert any("cannot silently displace" in d for d in r.needs_owner_decision)


def test_anonymous_fact_is_rejected_and_closes_nothing():
    r = ingest_batch([fact(source_locator="  ", closes_unknown="roll_material")])
    assert r.rejected and not r.accepted
    assert "roll_material" not in r.unknowns_closed


def test_stale_calculations_are_the_union_across_the_batch():
    r = ingest_batch([
        fact(subject="motor_rpm", value=750, unit="rpm",
             epistemic_class=EpistemicClass.MEASUREMENT, source_locator="photo:ST2 plate"),
        fact(subject="temperature", value=1040, unit="C",
             epistemic_class=EpistemicClass.MEASUREMENT, source_locator="pyrometer log"),
    ])
    assert {"surface_speed", "capacity", "mass_flow"} <= set(r.stale_calculations)
    assert {"flow_stress", "roll_force", "torque", "power"} <= set(r.stale_calculations)


def test_a_gate_does_not_unlock_while_anything_feeding_it_is_still_open():
    r = ingest_batch([fact(closes_unknown="roll_material")])
    assert "fabrication_release_allowed" not in r.gates_unlocked, \
        "stand rating, gearbox torque and bearings still feed that gate"


def test_a_gate_unlocks_only_when_every_contributor_is_closed():
    everything = tuple(UNKNOWN_UNLOCK_MAP)
    r = ingest_batch([fact(closes_unknown="roll_material")], already_closed=everything)
    assert "fabrication_release_allowed" in r.gates_unlocked
    assert r.unknowns_remaining == ()


def test_remaining_unknowns_are_ranked_by_how_much_they_unlock():
    r = ingest_batch([fact(closes_unknown="p1_p10_meaning")])
    counts = [len(UNKNOWN_UNLOCK_MAP[u]["unlocks"]) for u in r.unknowns_remaining]
    assert counts == sorted(counts, reverse=True)
    assert len(r.highest_value_remaining) == 3


def test_groove_geometry_outranks_a_minor_unknown():
    rep = readiness_report()
    order = [e["unknown"] for e in rep["ranked_by_consequence"]]
    assert order.index("groove_geometry") < order.index("p1_p10_meaning")


def test_every_unknown_documents_why_it_matters_and_what_it_blocks():
    for u, e in UNKNOWN_UNLOCK_MAP.items():
        assert e["why_it_matters"].strip(), u
        assert e["blocks_today"].strip(), u
        assert e["unlocks"], u


def test_readiness_report_starts_with_everything_open():
    rep = readiness_report()
    assert rep["open_unknowns"] == len(UNKNOWN_UNLOCK_MAP)
    assert rep["closed"] == []


def test_readiness_report_never_implies_a_gate_opened():
    assert "does not by itself open any" in readiness_report()["note"]


def test_different_equipment_is_recorded_separately_not_as_a_correction():
    r = ingest_batch([fact(
        subject="roll_diameter", value=600.0, unit="mm",
        epistemic_class=EpistemicClass.CLAIM, source_locator="ST3 sketch",
        equipment_id="ST3", existing_value=518.0,
        existing_class=EpistemicClass.MEASUREMENT, same_equipment=False)])
    assert r.accepted[0][1].accepted_as == "SEPARATE_SUBJECT"
    assert not r.contradictions


def test_summary_counts_match_the_detail():
    r = ingest_batch([
        fact(closes_unknown="roll_material"),
        fact(source_locator="", subject="furnace"),
    ])
    assert "1 accepted" in r.summary and "1 rejected" in r.summary
