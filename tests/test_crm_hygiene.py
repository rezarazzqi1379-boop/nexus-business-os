from nexus_core.crm_hygiene import CRMRecordCandidate, classify_crm_record, commercial_pipeline_candidates


def _candidate(**overrides):
    data = dict(
        record_id="c1",
        record_type="contact",
        display_name="Procurement Contact",
        email_or_domain="buyer@example.com",
        category_hint=None,
        project_refs=("project:octg",),
        commercial_evidence_refs=("gmail:rfq-thread",),
        contact_path_refs=("hubspot:contact:c1",),
        excluded_reason=None,
    )
    data.update(overrides)
    return CRMRecordCandidate(**data)


def test_commercial_requires_project_evidence_and_contact_path() -> None:
    result = classify_crm_record(_candidate())
    assert result.category == "commercial"
    assert result.promote_to_commercial_pipeline


def test_imported_contact_without_commercial_evidence_is_not_promoted() -> None:
    result = classify_crm_record(_candidate(commercial_evidence_refs=(), category_hint="commercial"))
    assert result.category == "unknown"
    assert not result.promote_to_commercial_pipeline


def test_personal_education_finance_hints_do_not_enter_pipeline() -> None:
    for hint in ("personal", "education", "finance"):
        result = classify_crm_record(_candidate(category_hint=hint))
        assert result.category == hint
        assert not result.promote_to_commercial_pipeline


def test_excluded_noise_wins_over_other_evidence() -> None:
    result = classify_crm_record(_candidate(excluded_reason="known non-commercial import"))
    assert result.category == "noise"
    assert not result.promote_to_commercial_pipeline


def test_pipeline_deduplicates_same_address() -> None:
    first = _candidate(record_id="c1")
    duplicate = _candidate(record_id="c2")
    assert commercial_pipeline_candidates((first, duplicate)) == (first,)
