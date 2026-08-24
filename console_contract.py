from __future__ import annotations


APP_VERSION = "1.9.0"


def build_console_bootstrap() -> dict:
    """Read-only pilot data contract, independent from the web framework."""
    return {
        "schema_version": "nexus.console.v1",
        "mode": "read_only_pilot",
        "external_writes_enabled": False,
        "summary": {"active_projects": 7, "waiting_approvals": 2, "open_unknowns": 11, "tests_passed": 96},
        "projects": [
            {"id": "hydrostatic_tester", "name": "Hydrostatic Tester", "status": "active", "progress": 62},
            {"id": "kcl_mop", "name": "KCl / MOP", "status": "active", "progress": 48},
            {"id": "can_forming", "name": "Can Forming", "status": "active", "progress": 74},
            {"id": "heat_treatment", "name": "Heat Treatment", "status": "hold", "progress": 35},
        ],
        "connectors": [
            {"name": "Gmail", "state": "read_ready", "scope": "read"},
            {"name": "HubSpot", "state": "available", "scope": "read"},
            {"name": "Notion", "state": "available", "scope": "review_required"},
            {"name": "Apollo", "state": "auth_broken", "scope": "optional"},
        ],
    }
