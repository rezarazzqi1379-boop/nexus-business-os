import json
from pathlib import Path

from nexus_verticals.supplier_identity import SupplierChannel, SupplierIdentity, SupplierRegistry


REGISTRY_PATH = Path("data/procurement/hydrotester_registry_v0_1.json")


def load_data():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def build_registry(data):
    registry = SupplierRegistry()
    for item in data["suppliers"]:
        registry.add_supplier(
            SupplierIdentity(
                supplier_id=item["supplier_id"],
                legal_name=item["legal_name"],
                brand=item.get("brand", ""),
                domain=item.get("domain", ""),
                country=item.get("country", ""),
                city=item.get("city", ""),
                factory_name=item.get("factory_name", ""),
                model_families=tuple(item.get("model_families", [])),
            )
        )
    for item in data["channels"]:
        registry.add_channel(
            SupplierChannel(
                channel_id=item["channel_id"],
                supplier_id=item["supplier_id"],
                channel_type=item["channel_type"],
                organization=item["organization"],
                contact_name=item.get("contact_name", ""),
                email=item.get("email", ""),
            )
        )
    return registry


def test_registry_file_parses_and_has_expected_version():
    data = load_data()
    assert data["registry_version"] == "0.1"
    assert data["project"]
    assert data["as_of"] == "2026-08-21"


def test_verified_supplier_records_have_identity_and_evidence():
    data = load_data()
    for supplier in data["suppliers"]:
        assert supplier["supplier_id"]
        assert supplier["legal_name"]
        assert supplier["domain"]
        assert supplier["identity_status"]
        assert supplier["evidence"]


def test_registry_builds_without_duplicate_supplier_or_channel_ids():
    data = load_data()
    registry = build_registry(data)
    assert registry.unique_oem_count() == 3
    assert registry.channel_count() == 3


def test_all_direct_channels_reference_known_supplier():
    data = load_data()
    supplier_ids = {item["supplier_id"] for item in data["suppliers"]}
    assert all(item["supplier_id"] in supplier_ids for item in data["channels"])


def test_unresolved_intermediaries_cannot_be_counted_as_unique_oems():
    data = load_data()
    registry = build_registry(data)
    assert len(data["unresolved_channels"]) == 3
    assert all(item["underlying_supplier_id"] is None for item in data["unresolved_channels"])
    assert registry.unique_oem_count() == 3


def test_unresolved_intermediaries_are_held_until_oem_identity_is_known():
    data = load_data()
    assert all(
        item["status"] == "hold_until_oem_identity_disclosed"
        for item in data["unresolved_channels"]
    )


def test_current_direct_channels_are_distinct_routes():
    data = load_data()
    registry = build_registry(data)
    domains = {supplier.domain for supplier in registry.suppliers.values()}
    assert len(domains) == registry.unique_oem_count()
