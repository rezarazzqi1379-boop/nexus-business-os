"""Bounded, read-only industrial tender assessment over the existing queue.

Publication is CLAIM evidence, never verified demand or permission to trade.
Only public business metadata is retained; contact details are not requested.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import http.client
import json
import math
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from time import monotonic, process_time

from contracts import canonical_digest
from deep_search_fabric import run_recursive_search
from discovery_pipeline import NormalizedDiscoveryResult, QueryExpansionPlan, group_duplicates
from nexus_public_research_agent import PublicResearchRuntime, AcquisitionError
from nexus_router_runtime import PROJECT
from project_control_plane import WorkRequest, build_coordination_plan
from research_lab import score_opportunity
from src.nexus_core.agent_catalog import AgentCatalogEntry

LANE = "industrial-tender-pilot"
FIELDS = ("id", "bid_description", "project_ctry_name", "project_id", "contact_organization",
          "submission_deadline_date", "noticedate", "notice_type", "notice_status",
          "procurement_method_name")
SOURCE = ("https://search.worldbank.org/api/v2/procnotices?format=json&qterm=steel&rows=3&fl="
          + ",".join(FIELDS))
MAX_BYTES = 65536
UNKNOWN = "UNKNOWN"
WEIGHTS = {"source_credibility": 0.2, "entity_verification": 0.15, "technical_fit": 0.2,
           "commercial_feasibility": 0.1, "completeness": 0.1, "time_sensitivity": 0.1,
           "economic_value": 0.1, "operational_complexity": 0.05}


def validated_weights(weights=None):
    result = dict(WEIGHTS if weights is None else weights)
    if set(result) != set(WEIGHTS) or any(type(v) not in (int, float) or not math.isfinite(v)
        or not 0 < v <= 1 for v in result.values()) or not math.isclose(sum(result.values()), 1, abs_tol=1e-9):
        raise ValueError("invalid_score_weights")
    return result


def source_quality_gate(row, *, age_days, expired, relevant, conflict):
    """Conservative prequalification of a notice; never establishes demand or technical fit."""
    reasons = []
    if conflict:
        reasons.append("conflicting_source_records")
    if not row.get("submission_deadline_date"):
        reasons.append("deadline_missing")
    if expired:
        reasons.append("expired")
    if row.get("notice_type") != "Invitation for Bids" or row.get("notice_status") != "Published":
        reasons.append("not_current_invitation")
    if age_days is None or not 0 <= age_days <= 30:
        reasons.append("publication_stale_or_unknown")
    if not relevant:
        reasons.append("technical_relevance_not_supported")
    return {"eligible_for_investigation": not reasons, "rejection_reasons": reasons}


def recommend_decision(item):
    """Recommendation only. Scores cannot override mandatory evidence/authority gates."""
    hard_reject = {"conflicting_source_records", "expired", "deadline_missing", "not_current_invitation",
                   "publication_stale_or_unknown", "technical_relevance_not_supported"}
    if hard_reject.intersection(item["risks"]):
        return "REJECT"
    if (item["verification_status"] == "VERIFIED" and item["evidence_class"] == "FACT"
        and item.get("technical_match") == "VERIFIED" and item.get("commercial_feasibility") == "VERIFIED"
        and item.get("authority_status") == "ADMITTED" and not item["missing_information"]):
        return "PROCEED"
    return "INVESTIGATE"


def utc():
    return datetime.now(timezone.utc).isoformat()


def get_public_notices(url):
    if url != SOURCE:
        raise PermissionError("source_not_allowlisted")
    started = monotonic()
    try:
        with closing(http.client.HTTPSConnection("search.worldbank.org", timeout=5)) as connection:
            connection.request("GET", url.removeprefix("https://search.worldbank.org"), headers={
                "User-Agent": "NEXUS-bounded-read-only-pilot", "Accept": "application/json",
                "Accept-Encoding": "identity"})
            response = connection.getresponse()
            if response.status != 200 or "application/json" not in response.getheader("Content-Type", ""):
                raise AcquisitionError("source_unavailable")
            body = bytearray()
            while True:
                remaining = 8 - (monotonic() - started)
                if remaining <= 0:
                    raise AcquisitionError("timeout")
                if connection.sock is not None:
                    connection.sock.settimeout(min(5, remaining))
                chunk = response.read1(min(8192, MAX_BYTES + 1 - len(body)))
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise AcquisitionError("response_too_large")
                if not chunk:
                    return bytes(body)
    except Exception:
        raise AcquisitionError("bounded_source_read_failed") from None


def parse_source(body):
    if type(body) is not bytes or len(body) > MAX_BYTES:
        raise ValueError("invalid_response_bounds")
    # Strict schema and text policy before retaining exact source bytes as an artifact.
    def unique_keys(pairs):
        result = {}
        for key, val in pairs:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = val
        return result
    data = json.loads(body, object_pairs_hook=unique_keys)
    if not isinstance(data, dict) or set(data) - {"rows", "os", "page", "total", "procnotices"}:
        raise ValueError("invalid_source_schema")
    for key in ("rows", "os", "page", "total"):
        val = data.get(key)
        if type(val) not in (str, int) or not re.fullmatch(r"[0-9]{1,12}", str(val)):
            raise ValueError("invalid_source_metadata")
    rows = data.get("procnotices")
    if not isinstance(rows, list) or len(rows) > 3:
        raise ValueError("invalid_result_limit")
    for row in rows:
        if not isinstance(row, dict) or set(row) - set(FIELDS):
            raise ValueError("unexpected_source_field")
        for value in row.values():
            if not isinstance(value, str) or len(value) > 2000 or re.search(
                r"[<>\x00-\x1f\x7f]|[\w.+-]+@[\w.-]+|(?i:bearer\s|password|secret|api[_-]?key|token[=:])", value):
                raise ValueError("unsafe_source_text")
        if not re.fullmatch(r"OP[0-9]{6,12}", row.get("id", "")):
            raise ValueError("invalid_notice_identity")
        if row.get("project_id") and not re.fullmatch(r"P[0-9]{6}", row["project_id"]):
            raise ValueError("invalid_source_project")
    return rows


def published(row):
    value = row.get("noticedate")
    return datetime.strptime(value, "%d-%b-%Y").replace(tzinfo=timezone.utc).isoformat() if value else None


def normalized(row, observed_at):
    title = row.get("bid_description") or UNKNOWN
    return NormalizedDiscoveryResult("worldbank", "steel World Bank", notice_url(row["id"]),
        title, title, observed_at, published(row), PROJECT, LANE,
        row.get("contact_organization"), row.get("project_ctry_name"), "procurement_authority")


def notice_url(identity):
    return "https://projects.worldbank.org/en/projects-operations/procurement-detail/" + identity


def assess(body, observed_at, *, weights=None):
    weights = validated_weights(weights)
    now = datetime.fromisoformat(observed_at)
    if now.tzinfo is None:
        raise ValueError("timezone_required")
    rows = parse_source(body)
    hits = tuple(normalized(row, observed_at) for row in rows)
    plan = QueryExpansionPlan("Assess industrial steel procurement notices", PROJECT, LANE,
        "commercial-pilot-v1", ("steel",), (), (), (), ("World Bank",), ("en",))
    search = run_recursive_search(plan, {"worldbank": lambda query, limit: hits},
        run_id="commercial-pilot", max_depth=1, query_budget=1, results_per_query=3,
        strict_provider_attribution=True)
    groups = group_duplicates(search.all_results)
    assessments = []
    for group in groups:
        identity = group.members[0].url.rsplit("/", 1)[-1]
        versions = [row for row in rows if row["id"] == identity]
        # Conflicts must survive deduplication; never select an arbitrary version.
        conflict = len({canonical_digest(row) for row in versions}) > 1
        row = sorted(versions, key=canonical_digest)[0]
        value = lambda field: row.get(field) or UNKNOWN
        pub = published(row)
        age = (now - datetime.fromisoformat(pub)).total_seconds() / 86400 if pub else None
        deadline = value("submission_deadline_date")
        expiry = datetime.fromisoformat(deadline.replace("Z", "+00:00")) if deadline != UNKNOWN else None
        if expiry is not None and expiry.tzinfo is None:
            raise ValueError("timezone_required")
        expired = expiry is not None and expiry <= now
        relevant = bool(re.search(r"\b(steel|hydrostatic|octg|industrial equipment)\b", value("bid_description"), re.I))
        reasons = ["independent_entity_and_demand_verification_missing", "commercial_terms_missing"]
        gate = source_quality_gate(row, age_days=age, expired=expired, relevant=relevant, conflict=conflict)
        reasons.extend(gate["rejection_reasons"])
        opportunity = {
            "opportunity_id": identity, "project_id": PROJECT, "lane_id": LANE,
            "source_project_id": value("project_id"), "identity": value("contact_organization"),
            "country": value("project_ctry_name"), "product_or_equipment": value("bid_description"),
            "technical_specifications": UNKNOWN, "quantity": UNKNOWN, "commercial_terms": UNKNOWN,
            "delivery_terms": UNKNOWN, "technical_match": UNKNOWN, "commercial_feasibility": UNKNOWN,
            "price_or_budget": UNKNOWN, "estimated_value": UNKNOWN, "deadline": deadline,
            "source_url": notice_url(identity), "retrieved_at": observed_at, "published_at": pub or UNKNOWN,
            "evidence_class": "CLAIM", "verification_status": "REJECTED_INSUFFICIENT_EVIDENCE",
            "actionable": False, "human_review_ready": False, "risks": reasons,
            "next_action": "READ_ONLY_PRIMARY_DOCUMENT_AND_INDEPENDENT_VERIFICATION_REQUIRED",
            "assertion_type": "SOURCE_CLAIM", "assumptions": [], "estimates": [],
            "technical_relevance": relevant, "source_quality_gate": gate, "source_age_days": round(age, 3) if age is not None else UNKNOWN,
            "deadline_precision": "SOURCE_TIMESTAMP_TIMEZONE_UNCONFIRMED",
            "source_record_sha256": canonical_digest(row), "conflict": conflict,
            "authority_status": "HOLD", "risk_classification": "HIGH_UNVERIFIED_COMMERCIAL_BASIS",
        }
        coverage_fields = ("identity", "country", "product_or_equipment", "technical_specifications",
                           "quantity", "commercial_terms", "price_or_budget", "deadline")
        opportunity["missing_information"] = [key for key in coverage_fields if opportunity[key] == UNKNOWN]
        completeness = (len(coverage_fields) - len(opportunity["missing_information"])) / len(coverage_fields)
        dimensions = {"source_credibility": 1.0, "entity_verification": UNKNOWN,
            "technical_fit": UNKNOWN, "commercial_feasibility": UNKNOWN,
            "completeness": completeness,
            "time_sensitivity": (0.0 if expired else 1.0) if expiry else UNKNOWN,
            "economic_value": UNKNOWN, "operational_complexity": UNKNOWN}
        known_weight = sum(weights[key] for key, val in dimensions.items() if val != UNKNOWN)
        # Research priority, not win probability, revenue or commercial qualification.
        opportunity["score"] = {"version": "research-priority-v2", "dimensions": dimensions,
            "weights": weights, "known_weight": known_weight,
            "priority": round(sum(weights[k] * v for k, v in dimensions.items() if v != UNKNOWN) / known_weight, 6),
            "existing_research_lab_score": score_opportunity(group.members[0].to_research_run_record(
                run_id="commercial-pilot", query_set_version="commercial-pilot-v1", source_type="official_portal"))}
        opportunity["decision"] = recommend_decision(opportunity)
        assessments.append(opportunity)
    assessments.sort(key=lambda item: (-item["score"]["priority"], item["opportunity_id"]))
    count = len(assessments)
    return {"assessments": assessments, "opportunities_discovered": count,
        "records_received": len(rows), "duplicates_removed": len(rows) - count,
        "duplicate_rate": round((len(rows) - count) / len(rows), 4) if rows else 0,
        "opportunities_verified": 0, "opportunities_rejected": sum(item["decision"] == "REJECT" for item in assessments),
        "opportunities_pending_investigation": sum(item["decision"] == "INVESTIGATE" for item in assessments),
        "source_gate_passed": sum(item["source_quality_gate"]["eligible_for_investigation"] for item in assessments),
        "source_gate_rejected": sum(not item["source_quality_gate"]["eligible_for_investigation"] for item in assessments),
        "actionable_opportunities": 0, "human_review_ready": 0,
        "decisions": {key: sum(item["decision"] == key for item in assessments)
                      for key in ("PROCEED", "INVESTIGATE", "REJECT")},
        "evidence_completeness": round(sum(o["score"]["dimensions"]["completeness"] for o in assessments) / count, 4) if count else 0,
        "commercial_relevance_count": sum(o["technical_relevance"] for o in assessments),
        "fresh_source_count": sum(isinstance(o["source_age_days"], (int, float)) and 0 <= o["source_age_days"] <= 30 for o in assessments),
        "estimated_opportunity_value": UNKNOWN, "time_to_actionable_report_seconds": UNKNOWN,
        "search_stop_reason": search.stop_reason, "authority_status": "HOLD",
        "result_scope": "BOUNDED_SOURCE_SAMPLE_ONLY_NOT_MARKET_ABSENCE"}


class CommercialRuntime(PublicResearchRuntime):
    action = "router.commercial-read.v1"
    roles = ("commercial-assessment",)

    def __init__(self, path, *, transport=get_public_notices, weights=None):
        self.weights = validated_weights(weights)
        super().__init__(path, transport=transport)

    def submit(self, task_id, **kwargs):
        # Bind scoring configuration into the existing durable task manifest.
        if "thread_id" in kwargs:
            raise PermissionError("caller_thread_override_blocked")
        return super().submit(task_id, thread_id="weights_" + canonical_digest(self.weights)[:24], **kwargs)

    def coordination(self, task_id):
        entry = AgentCatalogEntry("AGT-NEXUS-COMMERCIAL-PILOT", "Bounded tender assessor",
            "RESEARCH_AGENT", "https://github.com/rezarazzqi1379-boop/nexus-business-os", utc(),
            "EXPERIMENT", ("commercial-read",), ("fixed-tender-metadata", "read-only"),
            ("commercial-pilot",), "Bounded claim assessment and replay", "Disable pilot workflow")
        request = WorkRequest(task_id, PROJECT, "Assess public industrial notices without trading",
            ("commercial-read",), ("fixed-tender-metadata", "read-only"), lane="engineering", risk="read")
        return build_coordination_plan((request,), (), catalog=(entry,), concurrency=1)

    def execute(self, payload):
        if payload["project_id"] != PROJECT or payload["role"] != self.roles[0]:
            raise PermissionError("scope_mismatch")
        body = self.transport(SOURCE)
        observed = utc()
        values = assess(body, observed, weights=self.weights)
        digest = hashlib.sha256(body).hexdigest()
        return {"project_id": PROJECT, "task_id": payload["task_id"], "worker": self.roles[0],
            "status": "COMPLETE", "evidence_class": "CLAIM", "observed_at": observed,
            "score_weights": self.weights,
            "documents": [{"url": SOURCE, "sha256": digest, "body": body.decode("utf-8")}],
            "evidence": [SOURCE + "#sha256=" + digest], "values": values,
            "model_tokens": 0, "api_cost_usd": 0, "http_reads": 1}

    def validate_result(self, payload, result):
        if (result.get("project_id"), result.get("task_id"), result.get("worker"), result.get("status"),
            result.get("evidence_class")) != (PROJECT, payload["task_id"], self.roles[0], "COMPLETE", "CLAIM"):
            raise ValueError("invalid_evidence_scope")
        docs = result["documents"]
        if len(docs) != 1 or docs[0]["url"] != SOURCE:
            raise ValueError("invalid_source_provenance")
        body = docs[0]["body"].encode("utf-8")
        digest = hashlib.sha256(body).hexdigest()
        if digest != docs[0]["sha256"] or result["evidence"] != [SOURCE + "#sha256=" + digest]:
            raise ValueError("digest_mismatch")
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(result["observed_at"])).total_seconds()
        if (not 0 <= age <= 300 or result.get("score_weights") != self.weights
            or result["values"] != assess(body, result["observed_at"], weights=self.weights)):
            raise ValueError("stale_or_inaccurate_evidence")
        for key, expected in (("model_tokens", 0), ("api_cost_usd", 0), ("http_reads", 1)):
            if type(result.get(key)) is not int or result[key] != expected:
                raise ValueError("invalid_metrics")


def management_report(summary):
    # Escape validated source text as plain Markdown, never links/HTML/instructions.
    def plain(value):
        if value == UNKNOWN:
            return "نامعلوم"
        return re.sub(r"([\\`*_{}\[\]()#+.!|>~-])", r"\\\1", str(value)).replace("\n", " ")
    report = ("# گزارش پایلوت تجاری NEXUS\n\n"
        f"وضعیت اجرا: {summary['status']}؛ نوع منبع: {summary['source_mode']}\n\n"
        f"فرصت‌های ارزیابی‌شده: {summary.get('opportunities_discovered', 0)}؛ "
        f"تأییدشده: {summary.get('opportunities_verified', 0)}؛ "
        f"قابل اقدام: {summary.get('actionable_opportunities', 0)}؛ "
        f"تکراری حذف‌شده: {summary.get('duplicates_removed', 0)}\n\n"
        "انتشار آگهی، تأیید خریدار یا امکان معامله نیست. قیمت و ارزش اقتصادی نامعلوم است. "
        "HOLD حفظ شده؛ ایمیل، پیشنهاد تجاری و پرداخت انجام نشده است. "
        "نتیجه فقط دربارهٔ نمونهٔ محدود این اجراست.\n")
    labels = {"INVESTIGATE": "نیازمند بررسی بیشتر", "REJECT": "رد برای پیگیری فعلی", "PROCEED": "پیشنهاد ادامه پس از کنترل مجوزها"}
    gap_labels = {"identity": "هویت طرف معامله", "country": "کشور", "product_or_equipment": "موضوع درخواست",
        "technical_specifications": "مشخصات فنی معتبر", "quantity": "مقدار", "commercial_terms": "شرایط تجاری و تحویل",
        "price_or_budget": "قیمت یا بودجه", "deadline": "مهلت معتبر"}
    risk_labels = {"independent_entity_and_demand_verification_missing": "هویت و تقاضا مستقلاً تأیید نشده",
        "commercial_terms_missing": "شرایط معامله ناقص است", "conflicting_source_records": "داده‌های منبع متناقض‌اند",
        "expired": "مهلت گذشته است", "not_current_invitation": "آگهی دعوت جاری به ارائه پیشنهاد نیست",
        "publication_stale_or_unknown": "تازگی انتشار قابل اتکا نیست",
        "technical_relevance_not_supported": "ارتباط فنی با موضوع پایلوت پشتیبانی نشده است"}
    for item in summary.get("assessments", []):
        report += (f"\n## ارزیابی {plain(item['opportunity_id'])}\n\n"
            f"طرف معرفی‌شده در منبع: {plain(item['identity'])}؛ کشور: {plain(item['country'])}.\n\n"
            f"موضوع درخواست: {plain(item['product_or_equipment'])}\n\n"
            "توان شرکت برای تأمین: نامعلوم؛ تطبیق فنی و ظرفیت اجرایی احراز نشده است.\n\n"
            "مشخصات دقیق، مقدار، قیمت، شرایط تحویل و امکان پرداخت هنوز قابل تأیید نیست.\n\n"
            f"اطلاعات مفقود: {'، '.join(gap_labels[key] for key in item['missing_information']) or 'ندارد'}\n\n"
            f"ریسک تجاری بالا: {'؛ '.join(risk_labels[key] for key in item['risks'])}.\n\n"
            f"مهلت ثبت‌شده در منبع: {plain(item['deadline'])}؛ منطقه زمانی محلی تأیید نشده است.\n\n"
            f"تصمیم: {labels[item['decision']]}؛ امتیاز فقط اولویت پژوهش است.\n\n"
            "اقدام بعدی: بررسی فقط‌خواندنی سند اصلی و هویت مستقل؛ بدون تماس، ارسال پیشنهاد یا تعهد.\n\n"
            f"منبع: {plain(item['source_url'])}؛ بازیابی: {plain(item['retrieved_at'])}\n")
    return report


def run(*, transport=None, commit_sha=UNKNOWN, weights=None):
    weights = validated_weights(weights)
    started = monotonic()
    cpu_started = process_time()
    reads = 0
    summary = {"schema_version": "nexus.commercial-pilot.v1", "status": "BLOCKED",
        "source_mode": "REAL_PUBLIC_HTTP" if transport is None else "FROZEN_TEST_FIXTURE",
        "project_id": PROJECT, "lane_id": LANE, "commit_sha": commit_sha, "executed_at": utc(),
        "http_read_budget": 1, "estimated_api_cost_usd": 0, "model_tokens": 0,
        "external_writes": 0, "authority_promoted": False, "authority_status": "HOLD",
        "failure_categories": [], "duplicate_execution_prevented": False,
        "checkpoint_integrity": False, "supervisor": "NOT_VERIFIED",
        "cost_scope": "NO_PAID_API_OR_MODEL; ACTIONS_QUOTA_AND_HOST_COST_UNKNOWN"}
    evidence = None

    def bounded_get(url):
        nonlocal reads
        if url != SOURCE or reads >= 1:
            raise PermissionError("read_budget_exhausted_or_invalid_source")
        reads += 1
        return (get_public_notices if transport is None else transport)(url)

    try:
        with TemporaryDirectory(prefix="nexus-commercial-") as directory:
            path = Path(directory) / "queue.db"
            runtime = CommercialRuntime(path, transport=bounded_get, weights=weights)
            task = "bounded-commercial-assessment"
            if not runtime.submit(task, budget_units=3) or runtime.drain(concurrency=1) != 1:
                raise ValueError("task_not_completed")
            if runtime.review(task) != "accepted":
                raise ValueError("supervisor_rejected")
            checkpoints = [json.loads(e["body"]) for e in runtime.snapshot()["events"]
                           if e["task"] == task and e["kind"] == "checkpoint"]
            if len(checkpoints) != 1:
                raise ValueError("checkpoint_count")
            result = checkpoints[0]
            runtime.validate_result({"task_id": task}, result)
            recovered = CommercialRuntime(path, transport=bounded_get, weights=weights)
            if recovered.submit(task, budget_units=3) or recovered.drain(concurrency=1) != 0 or recovered.review(task) != "accepted":
                raise ValueError("replay_failed")
            evidence = result["documents"][0]
            summary.update(result["values"], status="VERIFIED", supervisor="accepted",
                checkpoint_integrity=True, duplicate_execution_prevented=True,
                source_url=SOURCE, source_sha256=evidence["sha256"], source_retrieved_at=result["observed_at"])
    except Exception:
        summary["failure_categories"] = ["ACQUISITION_OR_VALIDATION_FAILED"]
    summary.update(http_requests=reads, execution_duration_seconds=round(monotonic() - started, 4),
        cpu_seconds=round(process_time() - cpu_started, 4), source_bytes=len(evidence["body"].encode()) if evidence else 0)
    return summary, evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--weights-json", type=Path, help="Reviewed local JSON weights; never loaded from source data")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{40}", args.commit_sha):
        parser.error("exact commit SHA required")
    if args.output.exists() and (not args.output.is_dir() or any(args.output.iterdir())):
        parser.error("output must be a new or empty directory; preserve prior evidence")
    weights = json.loads(args.weights_json.read_text(encoding="utf-8")) if args.weights_json else None
    summary, evidence = run(commit_sha=args.commit_sha, weights=weights)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output / "management-fa.md").write_text(management_report(summary), encoding="utf-8")
    if evidence:
        (args.output / "public-source.json").write_bytes(evidence["body"].encode("utf-8"))
    print(json.dumps({k: summary[k] for k in ("status", "source_mode", "http_requests",
        "execution_duration_seconds", "failure_categories", "external_writes")}))
    return 0 if summary["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
