"""Fail-closed bridge from existing NEXUS planning to synthetic pilot execution.

Not a production runner. Never resolves credentials or performs external actions.
"""
from __future__ import annotations

from project_control_plane import WorkRequest as PlannedWork, build_coordination_plan
from nexus_agent_router_pilot import WorkRequest as PilotWork, run_parallel, synthetic_worker


def run_planned_synthetic(work_id: str, project_id: str, objective: str,
                          *, problem_tags: tuple[str, ...],
                          required_capabilities: tuple[str, ...],
                          lane: str = 'qa') -> dict:
    """Require qualified existing catalog agent and no blocked/approval work."""
    if not work_id or not project_id or not objective:
        raise ValueError('missing identity')
    request = PlannedWork(work_id=work_id, project_id=project_id,
                          objective=objective, problem_tags=problem_tags,
                          required_capabilities=required_capabilities,
                          lane=lane, risk='read', reversible=True)
    plan = build_coordination_plan((request,), (), concurrency=3)
    if plan.blocked or plan.approval_required or not plan.assignments:
        raise PermissionError(f'control_plane_blocked: {plan.blocked}')
    # These are synthetic roles, not external agent invocations.
    pilot = PilotWork(project_id, work_id, objective, action_kind='SYNTHETIC_TEST')
    output = run_parallel(pilot, {role: synthetic_worker(role)
                                  for role in ('research', 'reconciliation', 'qa')})
    output['control_plane_version'] = plan.version
    output['catalog_assignment'] = plan.assignments[0].agent_id
    output['maturity'] = 'SYNTHETIC_NOT_PRODUCTION'
    return output
