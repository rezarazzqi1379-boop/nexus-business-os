"""Finite-trial transport wrapper; uses AutonomyStore, never a second scheduler.

The callback must perform exactly one bounded request with redirects/retries off.
Only the existing World Bank transport is shipped live. UNGM remains blocked.
"""
from datetime import datetime, timezone

from autonomy import AutonomyStore
from nexus_commercial_pilot import SOURCE, MAX_BYTES, get_public_notices
from nexus_router_runtime import PROJECT
from source_monitor import MonitoringRuntime

UNGM_TERMS = "https://www.ungm.org/Public/Pages/Terms"


class UNGMConnector:
    source_id = "ungm"
    activation_status = "BLOCKED_PROVIDER_PERMISSION_REQUIRED"

    def __call__(self, url):
        # No boolean or caller-claimed approval can override provider terms.
        raise PermissionError("ungm_provider_permission_required")


class TrialTransport:
    """One reservation per callback, including retries and uncertain crash reads.

    Trusted host supplies tick/time. Durable window validation is in the store.
    Injected callbacks are frozen-test adapters, never evidence of live access.
    """

    def __init__(self, store: AutonomyStore, *, trial_id: str, tick: int,
                 transport=None, clock=None):
        self.store = store
        self.trial_id = trial_id
        self.tick = tick
        self.transport = get_public_notices if transport is None else transport
        self.source_mode = "REAL_PUBLIC_HTTP" if transport is None else "FROZEN_TEST_FIXTURE"
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def __call__(self, url):
        if url != SOURCE:
            raise PermissionError("trial_source_not_allowlisted")
        if self.store.http_trial_plan(self.trial_id, PROJECT)["source_mode"] != self.source_mode:
            raise PermissionError("trial_source_mode_mismatch")
        identity = self.store.reserve_http_attempt(self.trial_id, PROJECT,
            tick=self.tick, source="worldbank", now=self.clock())
        try:
            body = self.transport(url)
            if type(body) is not bytes or len(body) > MAX_BYTES:
                raise ValueError("trial_response_bounds")
        except Exception:
            self.store.finish_http_attempt(identity, success=False)
            raise RuntimeError("bounded_trial_read_failed") from None
        self.store.finish_http_attempt(identity, success=True)
        return body


class TrialMonitoringRuntime(MonitoringRuntime):
    """Instrument the existing worker without relabelling fixture/live evidence.

    Configure the immutable trial on this same store before dispatch. The host
    retains one database/plan for the experiment; this class starts no scheduler.
    """

    def __init__(self, path, *, trial_id, tick, transport=None, clock=None):
        super().__init__(path, transport=transport)
        self.transport = TrialTransport(self.store, trial_id=trial_id, tick=tick,
                                        transport=transport, clock=clock)


def trial_report(store, trial_id):
    attempts = store.http_trial_attempts(trial_id, PROJECT)
    return {"trial_id": trial_id, "project_id": PROJECT, "max_attempts": 6, "max_ticks": 3,
            "reserved_attempts": len(attempts), "attempts": attempts,
            "uncertain_attempts": sum(a["outcome"] == "RESERVED_UNKNOWN" for a in attempts),
            "transport_failures": sum(a["outcome"] == "TRANSPORT_FAILED" for a in attempts),
            "http_delivery_exactly_once": False, "authority_status": "HOLD",
            "ungm_activation": UNGMConnector.activation_status,
            "multi_source_live_proven": False}
