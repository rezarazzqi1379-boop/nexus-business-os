from nexus_verticals.supplier_identity import (
    OutreachDecision,
    SupplierChannel,
    SupplierIdentity,
    SupplierRegistry,
    deduplicate_candidates,
)


def supplier(supplier_id: str, **kwargs) -> SupplierIdentity:
    return SupplierIdentity(
        supplier_id=supplier_id,
        legal_name=kwargs.pop("legal_name", supplier_id),
        **kwargs,
    )


def test_same_domain_is_duplicate_even_with_different_agent_name():
    registry = SupplierRegistry()
    registry.add_supplier(
        supplier("oem-1", legal_name="Wuxi Example Machinery Co Ltd", domain="example.cn")
    )

    result = registry.find_identity_match(
        supplier("lead-2", legal_name="Example Export Division", domain="www.example.cn")
    )

    assert result.decision == OutreachDecision.HOLD_DUPLICATE_SOURCE
    assert result.matched_supplier_id == "oem-1"
    assert "same_domain" in result.reasons


def test_same_legal_identity_is_duplicate_without_domain():
    registry = SupplierRegistry()
    registry.add_supplier(supplier("oem-1", legal_name="Acme Industrial Equipment"))

    result = registry.find_identity_match(
        supplier("lead-2", legal_name="  ACME   INDUSTRIAL equipment ")
    )

    assert result.decision == OutreachDecision.HOLD_DUPLICATE_SOURCE
    assert "same_legal_name" in result.reasons


def test_same_factory_name_is_duplicate():
    registry = SupplierRegistry()
    registry.add_supplier(
        supplier("oem-1", legal_name="Alpha Export Co", factory_name="Wuxi Alpha Machinery Works")
    )

    result = registry.find_identity_match(
        supplier("lead-2", legal_name="Alpha International", factory_name="wuxi alpha machinery works")
    )

    assert result.decision == OutreachDecision.HOLD_DUPLICATE_SOURCE
    assert "same_factory_name" in result.reasons


def test_same_brand_alone_requires_review_not_auto_hold():
    registry = SupplierRegistry()
    registry.add_supplier(
        supplier("oem-1", legal_name="Factory Alpha", brand="Karat", domain="alpha.example")
    )

    result = registry.find_identity_match(
        supplier("lead-2", legal_name="Factory Beta", brand="karat", domain="beta.example")
    )

    assert result.decision == OutreachDecision.REVIEW_POSSIBLE_COLLISION
    assert "same_brand" in result.reasons


def test_same_city_and_model_requires_human_review_not_auto_hold():
    registry = SupplierRegistry()
    registry.add_supplier(
        supplier(
            "oem-1",
            legal_name="Factory Alpha",
            country="China",
            city="Wuxi",
            model_families=("GSY-180",),
        )
    )

    result = registry.find_identity_match(
        supplier(
            "lead-2",
            legal_name="Factory Beta",
            country="china",
            city="wuxi",
            model_families=("GSY-180",),
        )
    )

    assert result.decision == OutreachDecision.REVIEW_POSSIBLE_COLLISION


def test_same_model_in_different_city_does_not_create_false_collision():
    registry = SupplierRegistry()
    registry.add_supplier(
        supplier(
            "oem-1",
            legal_name="Factory Alpha",
            country="China",
            city="Wuxi",
            model_families=("GSY-180",),
        )
    )

    result = registry.find_identity_match(
        supplier(
            "oem-2",
            legal_name="Factory Beta",
            country="China",
            city="Huludao",
            model_families=("GSY-180",),
        )
    )

    assert result.decision == OutreachDecision.ALLOW


def test_different_supplier_is_allowed():
    registry = SupplierRegistry()
    registry.add_supplier(
        supplier("oem-1", legal_name="Factory Alpha", domain="alpha.example")
    )

    result = registry.find_identity_match(
        supplier("oem-2", legal_name="Factory Beta", domain="beta.example")
    )

    assert result.decision == OutreachDecision.ALLOW


def test_channels_do_not_inflate_unique_oem_count():
    registry = SupplierRegistry()
    registry.add_supplier(supplier("oem-1", legal_name="Factory Alpha"))
    registry.add_channel(SupplierChannel("direct", "oem-1", "direct", "Factory Alpha"))
    registry.add_channel(SupplierChannel("agent-a", "oem-1", "agent", "Agent A"))
    registry.add_channel(SupplierChannel("agent-b", "oem-1", "agent", "Agent B"))

    assert registry.unique_oem_count() == 1
    assert registry.channel_count() == 3
    assert len(registry.channels_for_supplier("oem-1")) == 3


def test_channel_cannot_reference_unknown_supplier():
    registry = SupplierRegistry()

    try:
        registry.add_channel(SupplierChannel("agent-a", "missing", "agent", "Agent A"))
    except ValueError as exc:
        assert "existing supplier" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_deduplicate_candidates_adds_only_unique_oems():
    existing = [supplier("oem-1", legal_name="Factory Alpha", domain="alpha.example")]
    candidates = [
        supplier("lead-dup", legal_name="Alpha Sales", domain="www.alpha.example"),
        supplier("oem-2", legal_name="Factory Beta", domain="beta.example"),
    ]

    results = deduplicate_candidates(existing, candidates)

    assert results[0][1].decision == OutreachDecision.HOLD_DUPLICATE_SOURCE
    assert results[1][1].decision == OutreachDecision.ALLOW
