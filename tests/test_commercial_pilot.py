from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import json

import pytest

import nexus_commercial_pilot as pilot


def row(**changes):
    values = dict(id="OP00476469", bid_description="Steel bridge supply invitation",
        project_ctry_name="Example country", project_id="P172225", contact_organization="Public works department",
        submission_deadline_date="2026-12-07T00:00:00Z", noticedate="22-Oct-2026",
        notice_type="Invitation for Bids", notice_status="Published", procurement_method_name="Request for Bids")
    values.update(changes)
    return values


def body(*rows):
    return json.dumps(dict(rows=len(rows), os="0", page="1", total=str(len(rows)), procnotices=list(rows))).encode()


NOW = "2026-10-27T20:00:00+00:00"


def test_unknown_and_unverified_are_not_qualified_or_zero_value():
    result = pilot.assess(body(row()), NOW)
    item = result["assessments"][0]
    assert item["evidence_class"] == "CLAIM"
    assert item["quantity"] == item["price_or_budget"] == item["estimated_value"] == "UNKNOWN"
    assert item["score"]["dimensions"]["economic_value"] == "UNKNOWN"
    assert item["score"]["dimensions"]["entity_verification"] == "UNKNOWN"
    assert item["score"]["dimensions"]["commercial_feasibility"] == "UNKNOWN"
    assert item["score"]["known_weight"] == pytest.approx(0.4)
    assert item["score"]["dimensions"]["technical_fit"] == "UNKNOWN"
    assert item["technical_relevance"] is True
    assert item["technical_match"] == "UNKNOWN"
    assert item["score"]["dimensions"]["completeness"] == 0.5
    assert not item["actionable"] and not item["human_review_ready"]
    assert result["opportunities_verified"] == result["actionable_opportunities"] == 0
    assert result["authority_status"] == "HOLD"


def test_reproducible_dedup_scoring_and_notice_not_entity_identity():
    first = row()
    second = row(id="OP00476470")  # same organization, different procurement
    result = pilot.assess(body(first, first, second), NOW)
    assert result == pilot.assess(body(first, first, second), NOW)
    assert result["records_received"] == 3 and result["opportunities_discovered"] == 2
    assert result["duplicates_removed"] == 1
    score = result["assessments"][0]["score"]
    expected = sum(score["weights"][k] * v for k, v in score["dimensions"].items() if v != "UNKNOWN") / score["known_weight"]
    assert score["priority"] == pytest.approx(expected, abs=1e-6)


def test_conflict_preserved_and_order_independent():
    one, two = row(), row(project_ctry_name="Conflicting country")
    result = pilot.assess(body(one, two), NOW)
    assert result == pilot.assess(body(two, one), NOW)
    assert result["duplicates_removed"] == 1
    assert result["assessments"][0]["conflict"]
    assert "conflicting_source_records" in result["assessments"][0]["risks"]


@pytest.mark.parametrize("changes,reason", [
    ({"submission_deadline_date": "2026-10-01T00:00:00Z"}, "expired"),
    ({"notice_type": "Contract Award"}, "not_current_invitation"),
    ({"notice_status": "Cancelled"}, "not_current_invitation"),
    ({"noticedate": "01-Jan-2025"}, "publication_stale_or_unknown"),
    ({"noticedate": "01-Jan-2027"}, "publication_stale_or_unknown"),
    ({"bid_description": "School construction"}, "technical_relevance_not_supported"),
])
def test_unsupported_currentness_or_fit(changes, reason):
    result = pilot.assess(body(row(**changes)), NOW)
    assert reason in result["assessments"][0]["risks"]
    assert result["opportunities_rejected"] == 1


def test_missing_fields_and_empty_sample_are_explicit():
    result = pilot.assess(body({"id": "OP00476469"}), NOW)
    item = result["assessments"][0]
    assert len(item["missing_information"]) == 8
    assert item["source_age_days"] == "UNKNOWN"
    assert item["score"]["dimensions"]["time_sensitivity"] == "UNKNOWN"
    empty = pilot.assess(body(), NOW)
    assert empty["opportunities_discovered"] == 0
    assert empty["result_scope"] == "BOUNDED_SOURCE_SAMPLE_ONLY_NOT_MARKET_ABSENCE"


@pytest.mark.parametrize("change", [
    {"id": "../../etc/passwd"}, {"project_id": "WRONG"}, {"contact_email": "private@example.com"},
    {"bid_description": "<script>alert(1)</script>"}, {"bid_description": "private@example.com"},
    {"bid_description": "Bearer unsafecredential"}, {"bid_description": "password=unsafe"},
    {"bid_description": "\x1b[31m"}, {"bid_description": "x" * 2001}, {"bid_description": 3},
])
def test_source_and_safe_artifact_validation(change):
    with pytest.raises(ValueError):
        pilot.assess(body(row(**change)), NOW)


@pytest.mark.parametrize("raw", [b"bad json", b"[]", b"x" * 65537,
    body(row(), row(), row(), row()), b'{"procnotices":[],"secret":"hidden"}'],
    ids=["not-json", "wrong-root", "oversized", "too-many-rows", "unexpected-metadata"])
def test_response_limits(raw):
    with pytest.raises((ValueError, TypeError)):
        pilot.assess(raw, NOW)


def test_duplicate_json_keys_and_unsafe_metadata_not_exported():
    raw = body(row()).replace(b'"id": "OP00476469"', b'"id":"password=hidden", "id": "OP00476469"')
    with pytest.raises(ValueError, match="duplicate_json_key"):
        pilot.parse_source(raw)
    raw = json.loads(body(row()))
    raw["total"] = "password=hidden"
    with pytest.raises(ValueError, match="invalid_source_metadata"):
        pilot.parse_source(json.dumps(raw).encode())


def test_real_transport_allowlist_rejects_before_network():
    with pytest.raises(PermissionError):
        pilot.get_public_notices("https://127.0.0.1/secret")


def test_live_mode_transport_failure_is_redacted(monkeypatch):
    def fail(url):
        raise RuntimeError("password=never-export-this")
    monkeypatch.setattr(pilot, "get_public_notices", fail)
    summary, evidence = pilot.run()
    assert summary["status"] == "BLOCKED" and summary["source_mode"] == "REAL_PUBLIC_HTTP"
    assert summary["http_requests"] == 1 and evidence is None
    assert "never-export" not in json.dumps(summary)
    assert summary["failure_categories"] == ["ACQUISITION_OR_VALIDATION_FAILED"]


def test_queue_checkpoint_supervisor_and_restart_replay(tmp_path):
    calls = []
    runtime = pilot.CommercialRuntime(tmp_path / "queue.db", transport=lambda url: calls.append(url) or body(row()))
    assert runtime.submit("task", budget_units=3)
    assert runtime.drain(concurrency=3) == 1
    assert runtime.review("task") == "accepted"
    again = pilot.CommercialRuntime(tmp_path / "queue.db", transport=lambda url: pytest.fail("duplicate GET"))
    assert not again.submit("task", budget_units=3)
    assert again.drain(concurrency=3) == 0
    assert again.review("task") == "accepted" and calls == [pilot.SOURCE]


def test_parallel_submission_executes_once(tmp_path):
    runtime = pilot.CommercialRuntime(tmp_path / "queue.db", transport=lambda url: body(row()))
    with ThreadPoolExecutor(max_workers=3) as pool:
        submitted = list(pool.map(lambda _: runtime.submit("same", budget_units=3), range(6)))
    assert submitted.count(True) == 1
    assert runtime.drain(concurrency=3) == 1
    assert runtime.review("same") == "accepted"


def test_wrapper_bounds_replay_and_fixture_label():
    calls = []
    summary, evidence = pilot.run(transport=lambda url: calls.append(url) or body(row()), commit_sha="a" * 40)
    assert summary["status"] == "VERIFIED" and summary["source_mode"] == "FROZEN_TEST_FIXTURE"
    assert summary["http_requests"] == 1 and calls == [pilot.SOURCE]
    assert summary["checkpoint_integrity"] and summary["duplicate_execution_prevented"]
    assert summary["supervisor"] == "accepted" and summary["external_writes"] == 0
    assert evidence["sha256"] == hashlib.sha256(evidence["body"].encode()).hexdigest()
    report = pilot.management_report(summary)
    assert "Steel bridge" in report and "توان شرکت" in report and "نیازمند بررسی بیشتر" in report


@pytest.mark.parametrize("mutation", ["hash", "scope", "value", "metric", "future", "stale", "url", "binding"])
def test_checkpoint_tampering_rejected(tmp_path, mutation):
    runtime = pilot.CommercialRuntime(tmp_path / "queue.db", transport=lambda url: body(row()))
    payload = dict(project_id=pilot.PROJECT, role=runtime.roles[0], task_id="task")
    result = runtime.execute(payload)
    if mutation == "hash":
        result["documents"][0]["sha256"] = "0" * 64
    elif mutation == "scope":
        result["project_id"] = "other"
    elif mutation == "value":
        result["values"]["opportunities_verified"] = 1
    elif mutation == "metric":
        result["http_reads"] = True
    elif mutation in {"future", "stale"}:
        result["observed_at"] = (datetime.now(timezone.utc) + timedelta(seconds=600 if mutation == "future" else -600)).isoformat()
    elif mutation == "url":
        result["documents"][0]["url"] = "https://evil.invalid/"
    else:
        result["evidence"] = []
    with pytest.raises(ValueError):
        runtime.validate_result(payload, result)


def test_budget_and_authority_inputs_remain_blocked(tmp_path):
    runtime = pilot.CommercialRuntime(tmp_path / "queue.db", transport=lambda url: pytest.fail("unexpected GET"))
    with pytest.raises(ValueError, match="budget"):
        runtime.submit("task", budget_units=2)
    with pytest.raises(PermissionError):
        runtime.submit("task", approval_id="invented")
    with pytest.raises(PermissionError):
        runtime.submit("task", project_id="steel")
    with pytest.raises(PermissionError):
        runtime.submit("task", action="send_email")


def test_second_read_is_blocked_by_wrapper_budget(monkeypatch):
    original = pilot.CommercialRuntime.execute
    def doubled(self, payload):
        original(self, payload)
        return original(self, payload)
    monkeypatch.setattr(pilot.CommercialRuntime, "execute", doubled)
    summary, evidence = pilot.run(transport=lambda url: body(row()))
    assert summary["status"] == "BLOCKED" and summary["http_requests"] == 1
    assert evidence is None


def test_decisions_cannot_be_promoted_by_a_high_score():
    item = pilot.assess(body(row()), NOW)["assessments"][0]
    assert item["decision"] == "INVESTIGATE"
    item["score"]["priority"] = 1.0
    assert pilot.recommend_decision(item) == "INVESTIGATE"
    item.update(verification_status="VERIFIED", evidence_class="FACT", technical_match="VERIFIED",
                commercial_feasibility="VERIFIED", missing_information=[])
    assert pilot.recommend_decision(item) == "INVESTIGATE"  # HOLD still blocks PROCEED
    item["authority_status"] = "ADMITTED"  # synthetic unit input only; no live admission path
    assert pilot.recommend_decision(item) == "PROCEED"
    item["risks"].append("expired")
    assert pilot.recommend_decision(item) == "REJECT"


@pytest.mark.parametrize("bad", [{}, {**pilot.WEIGHTS, "technical_fit": -0.1},
    {**pilot.WEIGHTS, "technical_fit": True}, {**pilot.WEIGHTS, "technical_fit": float('nan')},
    {**pilot.WEIGHTS, "technical_fit": 0}, {**pilot.WEIGHTS, "extra": 0.1}])
def test_invalid_weights_fail_closed(bad):
    with pytest.raises(ValueError, match="invalid_score_weights"):
        pilot.assess(body(row()), NOW, weights=bad)


def test_configurable_weights_are_bound_to_queue_manifest(tmp_path):
    weights = {**pilot.WEIGHTS, "technical_fit": 0.1, "completeness": 0.2}
    expected = pilot.assess(body(row()), NOW, weights=weights)
    assert expected == pilot.assess(body(row()), NOW, weights=weights)
    assert expected != pilot.assess(body(row()), NOW)
    runtime = pilot.CommercialRuntime(tmp_path / "queue.db", transport=lambda url: body(row()))
    assert runtime.submit("task", budget_units=3)
    recovered = pilot.CommercialRuntime(tmp_path / "queue.db", transport=lambda url: body(row()), weights=weights)
    with pytest.raises(ValueError, match="duplicate_task_conflict"):
        recovered.submit("task", budget_units=3)


def test_per_notice_report_escapes_untrusted_markdown_and_preserves_decision():
    summary = pilot.assess(body(row(bid_description="Steel [click](https://invalid.test) **important**")), NOW)
    report = pilot.management_report({**summary, "status": "VERIFIED", "source_mode": "FROZEN_TEST_FIXTURE"})
    assert "[click](https://invalid.test)" not in report and "**important**" not in report
    assert "\\[click\\]" in report and "نیازمند بررسی بیشتر" in report
    assert "OP00476469" in report and "توان شرکت" in report and "بدون تماس" in report


def test_cli_refuses_to_mix_old_source_with_a_new_execution(tmp_path, monkeypatch):
    target = tmp_path / "previous"
    target.mkdir()
    source = target / "public-source.json"
    source.write_text("previous verified evidence")
    monkeypatch.setattr('sys.argv', ['pilot', '--output', str(target), '--commit-sha', 'a' * 40])
    monkeypatch.setattr(pilot, 'run', lambda **kw: pytest.fail('must reject before network'))
    with pytest.raises(SystemExit) as error:
        pilot.main()
    assert error.value.code == 2 and source.read_text() == 'previous verified evidence'


def test_decision_accounting_excludes_investigation_from_rejections():
    result = pilot.assess(body(row(), row(id="OP00476470", bid_description="School construction")), NOW)
    assert result["decisions"] == {"PROCEED": 0, "INVESTIGATE": 1, "REJECT": 1}
    assert result["opportunities_rejected"] == 1
    assert result["opportunities_pending_investigation"] == 1
    assert sum(result["decisions"].values()) == result["opportunities_discovered"]


def test_lexical_relevance_never_establishes_technical_fit():
    result = pilot.assess(body(row(bid_description="Steel bridge supply invitation")), NOW)
    item = result["assessments"][0]
    assert item["technical_relevance"] is True
    assert item["technical_specifications"] == "UNKNOWN"
    assert item["technical_match"] == "UNKNOWN"
    assert item["score"]["dimensions"]["technical_fit"] == "UNKNOWN"
    assert item["decision"] == "INVESTIGATE"
