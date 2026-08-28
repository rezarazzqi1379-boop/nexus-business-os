from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Any

from runner_registry import HERDR, WorkPacket, validate_runner_packet


_SAFE_NAME = re.compile(r"[^a-z0-9_-]+")
_SUPPORTED_KINDS = frozenset({"codex", "claude"})


@dataclass(frozen=True)
class HerdrStep:
    step_id: str
    argv: tuple[str, ...]
    capture: str | None = None
    requires: tuple[str, ...] = ()


@dataclass(frozen=True)
class HerdrExecutionPlan:
    packet_digest: str
    runner_id: str
    mode: str
    project_id: str
    workspace: str
    agent_name: str
    agent_kind: str
    steps: tuple[HerdrStep, ...]
    external_action_authorized: bool = False
    approval_delegated: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _slug(value: str, *, fallback: str) -> str:
    normalized = _SAFE_NAME.sub("-", value.strip().lower()).strip("-_")
    return (normalized or fallback)[:32]


def build_herdr_plan(
    packet: WorkPacket,
    *,
    workspace_root: str,
    agent_kind: str = "codex",
    timeout_ms: int = 120_000,
) -> HerdrExecutionPlan:
    """Build a non-executing, fail-closed Herdr plan for a NEXUS read packet."""
    validation = validate_runner_packet(packet, HERDR)
    if agent_kind not in _SUPPORTED_KINDS:
        raise ValueError("unsupported_herdr_agent_kind")
    if not 5_001 <= timeout_ms <= 300_000:
        raise ValueError("invalid_herdr_timeout")
    if not workspace_root.strip():
        raise ValueError("invalid_workspace_root")

    root = PurePosixPath(workspace_root)
    if not root.is_absolute():
        raise ValueError("workspace_root_must_be_absolute")
    workspace = str(root.joinpath(PurePosixPath(packet.workspace_subpath)))
    label = _slug(packet.project_id, fallback="nexus")
    agent_name = _slug(f"nexus-{label}", fallback="nexus-agent")

    steps = (
        HerdrStep(
            "create_workspace",
            ("herdr", "workspace", "create", "--cwd", workspace, "--label", label, "--no-focus"),
            capture="root_pane_id",
        ),
        HerdrStep(
            "start_agent",
            ("herdr", "agent", "start", agent_name, "--kind", agent_kind, "--pane", "{root_pane_id}"),
            requires=("root_pane_id",),
        ),
        HerdrStep(
            "prompt_agent",
            ("herdr", "agent", "prompt", agent_name, packet.objective, "--wait", "--timeout", str(timeout_ms)),
        ),
        HerdrStep(
            "read_result",
            ("herdr", "agent", "read", agent_name, "--source", "recent-unwrapped", "--lines", "160"),
            capture="agent_result",
        ),
    )
    return HerdrExecutionPlan(
        packet_digest=validation["packet_digest"],
        runner_id=validation["runner_id"],
        mode="prepare_only",
        project_id=packet.project_id,
        workspace=workspace,
        agent_name=agent_name,
        agent_kind=agent_kind,
        steps=steps,
    )
