"""Real-source deterministic research worker; explicitly not an LLM agent.

Only two fixed public GitHub GETs, no authentication, redirects or credentials.
Shares the router queue, fences, checkpoints and supervisor. Commercial HOLD
cannot be lifted here. Provider fields remain CLAIM evidence.
"""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import http.client
import json
from time import monotonic

from agent_supervisor import AcceptanceContract, ArtifactClaim, Supervisor, TaskRecord
from contracts import canonical_digest
from nexus_router_runtime import SyntheticRuntime, PROJECT
from project_control_plane import WorkRequest, build_coordination_plan
from src.nexus_core.agent_catalog import AgentCatalogEntry

REPO = "openai/openai-agents-python"
URLS = (f"https://api.github.com/repos/{REPO}", f"https://api.github.com/repos/{REPO}/releases/latest")
MAX_BYTES = 65536


class AcquisitionError(RuntimeError):
    pass


def public_get(url):
    if url not in URLS:
        raise PermissionError("source_not_allowlisted")
    started = monotonic()
    try:
        with closing(http.client.HTTPSConnection("api.github.com", timeout=5)) as connection:
            connection.request("GET", url.removeprefix("https://api.github.com"),
                headers={"User-Agent": "NEXUS-bounded-research", "Accept": "application/vnd.github+json",
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
                    break
            return bytes(body)
    except AcquisitionError:
        raise
    except Exception:
        # No raw transport/provider errors in logs or checkpoints.
        raise AcquisitionError("transport_failed") from None


def extract(bodies, observed_at):
    if len(bodies) != 2 or any(type(body) is not bytes or len(body) > MAX_BYTES for body in bodies):
        raise ValueError("invalid_response_bounds")
    repo, release = [json.loads(body) for body in bodies]
    if repo.get("full_name") != REPO or type(repo.get("archived")) is not bool:
        raise ValueError("wrong_repository_identity")
    if release.get("html_url", "").startswith(f"https://github.com/{REPO}/releases/tag/") is False:
        raise ValueError("wrong_release_identity")
    values = {"full_name": repo["full_name"], "archived": repo["archived"],
              "pushed_at": repo.get("pushed_at"), "license_spdx": (repo.get("license") or {}).get("spdx_id"),
              "release_tag": release.get("tag_name"), "release_published_at": release.get("published_at")}
    for key, value in values.items():
        if key != "archived" and (not isinstance(value, str) or not value or len(value) > 200 or
                                    any(ord(char) < 32 for char in value)):
            raise ValueError("missing_or_malformed_field")
    current = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    if current.tzinfo is None:
        raise ValueError("naive_timestamp")
    for field in ("pushed_at", "release_published_at"):
        date = datetime.fromisoformat(values[field].replace("Z", "+00:00"))
        if date.tzinfo is None or date > current:
            raise ValueError("future_or_naive_source_date")
    values["maintenance_claim"] = ("RECENT_ACTIVITY" if not values["archived"] and
        (current-datetime.fromisoformat(values["pushed_at"].replace("Z", "+00:00"))).days <= 180
        else "REVIEW_REQUIRED")
    return values


class PublicResearchRuntime(SyntheticRuntime):
    action = "router.public-research.v1"
    roles = ("repository_research",)
    submission_action = "PUBLIC_RESEARCH_READ"
    submission_authority = "UNVERIFIED_PUBLIC"

    def __init__(self, path, *, transport=public_get):
        super().__init__(path)
        self.transport = transport  # trusted injection for frozen tests, never source-controlled

    def coordination(self, task_id):
        observed = datetime.now(timezone.utc).isoformat()
        entry = AgentCatalogEntry("AGT-NEXUS-PUBLIC-RESEARCH", "NEXUS bounded public repository researcher",
            "RESEARCH_AGENT", "https://github.com/rezarazzqi1379-boop/nexus-business-os", observed,
            "EXPERIMENT", ("public-research",), ("fixed-github-metadata", "read-only"),
            ("real-source-benchmark",), "Frozen extraction, isolation, replay and bounded live GET",
            "Return to synthetic router; keep journal")
        request = WorkRequest(task_id, PROJECT, "Assess official repository maintenance metadata",
            ("public-research",), ("fixed-github-metadata", "read-only"), lane="engineering", risk="read")
        # Catalog eligibility only. Remote health stays UNKNOWN until bounded GETs
        # actually succeed; no installed/available connector is presumed healthy.
        return build_coordination_plan((request,), (), catalog=(entry,), concurrency=1)

    def execute(self, payload):
        if payload["project_id"] != PROJECT or payload["role"] != self.roles[0]:
            raise PermissionError("scope_mismatch")
        started = monotonic()
        try:
            bodies = [self.transport(url) for url in URLS]
        except Exception:
            raise AcquisitionError("bounded_source_read_failed") from None
        observed = datetime.now(timezone.utc).isoformat()
        values = extract(bodies, observed)
        if monotonic() - started > 20:
            raise AcquisitionError("task_timeout")
        documents = [{"url": url, "sha256": hashlib.sha256(body).hexdigest(),
                      "body": body.decode("utf-8")} for url, body in zip(URLS, bodies)]
        return {"worker": self.roles[0], "project_id": PROJECT, "task_id": payload["task_id"],
                "status": "COMPLETE", "observed_at": observed, "query": f"repository:{REPO}",
                "evidence_class": "CLAIM", "documents": documents, "values": values,
                "evidence": [f'{d["url"]}#sha256={d["sha256"]}' for d in documents],
                "model_tokens": 0, "api_cost_usd": 0, "http_reads": 2}

    def validate_result(self, payload, result):
        if result.get('query') != f'repository:{REPO}':
            raise ValueError('query_binding_mismatch')
        for key, expected in (('model_tokens', 0), ('api_cost_usd', 0), ('http_reads', 2)):
            if type(result.get(key)) is not int or result[key] != expected:
                raise ValueError('execution_metrics_mismatch')
        if (result.get("project_id"), result.get("task_id"), result.get("worker"),
            result.get("status"), result.get("evidence_class")) != (
                PROJECT, payload["task_id"], self.roles[0], "COMPLETE", "CLAIM"):
            raise ValueError("invalid_evidence_scope")
        docs = result["documents"]
        if len(docs) != 2 or [d["url"] for d in docs] != list(URLS):
            raise ValueError("invalid_source_provenance")
        bodies = [d["body"].encode("utf-8") for d in docs]
        if any(hashlib.sha256(body).hexdigest() != doc["sha256"] for body,doc in zip(bodies,docs)):
            raise ValueError("digest_mismatch")
        age = (datetime.now(timezone.utc)-datetime.fromisoformat(result["observed_at"])).total_seconds()
        if not 0 <= age <= 300 or result["values"] != extract(bodies, result["observed_at"]):
            raise ValueError("stale_or_inaccurate_evidence")
        if result["evidence"] != [f'{d["url"]}#sha256={d["sha256"]}' for d in docs]:
            raise ValueError("evidence_binding_mismatch")

    @classmethod
    def read_snapshot(cls, path):
        snapshot = super().read_snapshot(path)
        snapshot["maturity"] = "REAL_SOURCE_DETERMINISTIC_EXPERIMENT"
        snapshot["provider_health"] = "UNKNOWN"
        for event in snapshot["events"]:
            if event["kind"] != "checkpoint":
                continue
            result = json.loads(event["body"])
            if result.get("worker") == cls.roles[0]:
                age = (datetime.now(timezone.utc)-datetime.fromisoformat(result["observed_at"])).total_seconds()
                snapshot["provider_health"] = "OBSERVED_READ_OK" if 0 <= age <= 300 else "STALE"
                break
        return snapshot

    def review(self, task_id):
        self._identity(task_id)
        with closing(self.store._connect()) as db:
            rows = db.execute("SELECT body FROM router_events WHERE project=? AND task=? AND kind='checkpoint'",
                              (PROJECT, task_id)).fetchall()
        if len(rows) != 1:
            return "rejected"
        result = json.loads(rows[0][0])
        self.validate_result({"task_id": task_id}, result)
        digest = canonical_digest({"task": task_id, "action": self.action})
        contract = AcceptanceContract(PROJECT, digest, (), tuple(result["evidence"]))
        task = TaskRecord(task_id, contract)
        supervisor = Supervisor()
        supervisor.observe(task, observation_id="real-source-review", runner_state="done")
        return supervisor.verify(task, ArtifactClaim(PROJECT, digest,
            json.dumps(result["values"]).encode(), tuple(result["evidence"]), ())).value
