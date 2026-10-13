"""Pure readiness evaluation for a persistent Windows NEXUS-LAB runner.

Does not create scheduled tasks, services, credentials or filesystem changes.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class WindowsLabReadiness:
    isolated_directory_verified: bool = False
    local_dirty_repo_preserved: bool = False
    source_commit_pinned: bool = False
    runtime_dependencies_verified: bool = False
    credentials_isolated: bool = False
    backups_tested: bool = False
    restart_tested: bool = False
    stop_switch_tested: bool = False
    zero_cost_confirmed: bool = False
    exact_host_approval: bool = False

def readiness_errors(s: WindowsLabReadiness) -> tuple[str, ...]:
    checks = {
        "isolated_directory_unverified": s.isolated_directory_verified,
        "dirty_repo_preservation_unverified": s.local_dirty_repo_preserved,
        "source_commit_unpinned": s.source_commit_pinned,
        "runtime_dependencies_unverified": s.runtime_dependencies_verified,
        "credential_isolation_unverified": s.credentials_isolated,
        "backup_restore_untested": s.backups_tested,
        "restart_untested": s.restart_tested,
        "stop_switch_untested": s.stop_switch_tested,
        "cost_unconfirmed": s.zero_cost_confirmed,
        "host_approval_missing": s.exact_host_approval,
    }
    if any(type(value) is not bool for value in checks.values()):
        return ("invalid_readiness_evidence",)
    return tuple(error for error, passed in checks.items() if not passed)
