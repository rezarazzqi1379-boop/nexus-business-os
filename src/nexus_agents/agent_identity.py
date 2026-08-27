from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Risk = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass(frozen=True)
class AgentIdentityManifest:
    agent_id: str
    version: str
    purpose: str
    capabilities: tuple[str, ...]
    allowed_projects: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    data_classes: tuple[str, ...]
    risk: Risk
    rollback_ref: str

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for name in ("agent_id", "version", "purpose", "rollback_ref"):
            if not getattr(self, name).strip():
                errors.append(f"{name} required")
        if not self.capabilities:
            errors.append("capabilities required")
        if set(self.allowed_actions) & set(self.forbidden_actions):
            errors.append("action cannot be both allowed and forbidden")
        if "PRODUCTION" in self.allowed_actions or "EXTERNAL_SEND" in self.allowed_actions:
            errors.append("consequential actions require separate runtime approval gate")
        return tuple(errors)

    def can_touch_project(self, project_id: str) -> bool:
        return project_id in self.allowed_projects
