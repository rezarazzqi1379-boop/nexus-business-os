import pytest

from market_price_snapshot import PriceSnapshot, PriceSnapshotStore, utc_now_iso


def _snapshot(**overrides):
    defaults = dict(
        snapshot_id="snap1",
        product="ferrosilicon",
        price_per_ton=1450.0,
        currency="USD",
        price_source="fastmarkets",
        classification="FACT",
        source_ref="fastmarkets:2026-09-14:fesi75",
        observed_at="2026-09-14T00:00:00+00:00",
        recorded_at=utc_now_iso(),
    )
    defaults.update(overrides)
    return PriceSnapshot(**defaults)


def test_valid_snapshot_passes_validation():
    _snapshot().validate()


def test_fact_requires_named_source_not_other():
    with pytest.raises(ValueError):
        _snapshot(price_source="other", classification="FACT").validate()


def test_claim_allowed_with_other_source():
    _snapshot(price_source="other", classification="CLAIM").validate()


def test_rejects_nonpositive_price():
    with pytest.raises(ValueError):
        _snapshot(price_per_ton=0).validate()


def test_rejects_unknown_price_source():
    with pytest.raises(ValueError):
        _snapshot(price_source="some_random_site").validate()


def test_store_records_and_retrieves_latest(tmp_path):
    store = PriceSnapshotStore(tmp_path / "prices.db")
    store.record(_snapshot(snapshot_id="s1", observed_at="2026-09-10T00:00:00+00:00"))
    store.record(_snapshot(snapshot_id="s2", observed_at="2026-09-14T00:00:00+00:00", price_per_ton=1500.0))
    latest = store.latest_for_product("ferrosilicon")
    assert latest["snapshot_id"] == "s2"
    assert latest["price_per_ton"] == 1500.0


def test_store_history_is_chronological(tmp_path):
    store = PriceSnapshotStore(tmp_path / "prices.db")
    store.record(_snapshot(snapshot_id="s1", observed_at="2026-09-10T00:00:00+00:00"))
    store.record(_snapshot(snapshot_id="s2", observed_at="2026-09-14T00:00:00+00:00"))
    history = store.history_for_product("ferrosilicon")
    assert [h["snapshot_id"] for h in history] == ["s1", "s2"]


def test_store_rejects_invalid_snapshot_before_writing(tmp_path):
    store = PriceSnapshotStore(tmp_path / "prices.db")
    with pytest.raises(ValueError):
        store.record(_snapshot(price_per_ton=-5))
    assert store.latest_for_product("ferrosilicon") is None
