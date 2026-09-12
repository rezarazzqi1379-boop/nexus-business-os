"""Evidence-backed self-use loop for NEXUS systems; never auto-promotes."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal

from nexus_agents.experience_ledger import ExperienceTrajectory, eligible_for_learning
from nexus_agents.skill_compiler import SkillProposal, decide_skill_proposal
from unified_data_environment import EvidenceObservation, UnifiedDataHub

ExerciseOutcome = Literal["SUCCESS", "PARTIAL", "FAILURE"]


def _digest(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class SystemExercise:
    exercise_id: str
    system_id: str
    project_id: str
    task_id: str
    procedural_family: str
    evidence_refs: tuple[str, ...]
    actions: tuple[str, ...]
    test_commands: tuple[str, ...]
    acceptance_checks: tuple[str, ...]
    outcome: ExerciseOutcome
    human_corrections: int
    reusable_lessons: tuple[str, ...]
    observed_at: str

    def validate(self) -> tuple[str, ...]:
        errors = [f"{name} required" for name in
                  ("exercise_id", "system_id", "project_id", "task_id", "procedural_family")
                  if not getattr(self, name).strip()]
        if not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs):
            errors.append("evidence_refs required")
        if not self.actions:
            errors.append("actions required")
        if not self.test_commands or not self.acceptance_checks:
            errors.append("tests and acceptance checks required")
        if self.human_corrections < 0:
            errors.append("human_corrections must be non-negative")
        if self.outcome not in {"SUCCESS", "PARTIAL", "FAILURE"}:
            errors.append("invalid outcome")
        try:
            parsed = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                errors.append("observed_at requires timezone")
        except ValueError:
            errors.append("invalid observed_at")
        if self.outcome != "SUCCESS" and self.reusable_lessons:
            errors.append("only successful exercises may teach reusable lessons")
        return tuple(errors)

    @property
    def digest(self) -> str:
        return _digest(asdict(self))

    def to_trajectory(self) -> ExperienceTrajectory:
        if errors := self.validate():
            raise ValueError("; ".join(errors))
        return ExperienceTrajectory(self.exercise_id, "nexus-self-operator", self.project_id,
                                    self.task_id, self.evidence_refs, self.actions,
                                    self.test_commands, self.outcome, self.human_corrections,
                                    self.reusable_lessons, self.digest)


@dataclass(frozen=True)
class ImprovementCandidate:
    candidate_id: str
    procedural_family: str
    decision: Literal["REJECT", "DRAFT_SKILL", "EXPERIMENT"]
    source_exercise_ids: tuple[str, ...]
    instruction: str
    acceptance_tests: tuple[str, ...]
    rollback_ref: str


@dataclass(frozen=True)
class SelfImprovementReport:
    project_id: str
    accepted_exercises: tuple[str, ...]
    ineligible_exercises: tuple[str, ...]
    candidates: tuple[ImprovementCandidate, ...]
    production_changes_applied: bool = False


def run_self_improvement_cycle(exercises: tuple[SystemExercise, ...], *, project_id: str,
                               rollback_ref: str) -> SelfImprovementReport:
    if not project_id.strip() or not rollback_ref.strip():
        raise ValueError("project_id and rollback_ref required")
    identities: dict[str, str] = {}
    accepted: list[SystemExercise] = []
    ineligible: list[str] = []
    for item in exercises:
        if item.project_id != project_id:
            raise ValueError("cross_project_exercise_denied")
        previous = identities.setdefault(item.exercise_id, item.digest)
        if previous != item.digest:
            raise ValueError("exercise_identity_collision")
        if eligible_for_learning(item.to_trajectory()):
            accepted.append(item)
        else:
            ineligible.append(item.exercise_id)
    candidates = []
    for family in sorted({x.procedural_family for x in accepted}):
        group = tuple(x for x in accepted if x.procedural_family == family)
        ids = tuple(dict.fromkeys(x.exercise_id for x in group))
        if len(ids) < 3:
            continue
        tests = tuple(dict.fromkeys(v for x in group for v in x.acceptance_checks))
        lessons = tuple(dict.fromkeys(v for x in group for v in x.reusable_lessons))
        proposal = SkillProposal(f"experiment-{family}-{_digest(ids)[:12]}", ids, (project_id,),
                                 "; ".join(lessons), tests, rollback_ref)
        candidates.append(ImprovementCandidate(proposal.skill_id, family,
                                                decide_skill_proposal(proposal), ids,
                                                proposal.instruction, tests, rollback_ref))
    return SelfImprovementReport(project_id, tuple(x.exercise_id for x in accepted),
                                 tuple(ineligible), tuple(candidates), False)


def record_cycle(hub: UnifiedDataHub, report: SelfImprovementReport, observed_at: str) -> bool:
    refs = tuple(f"exercise:{x}" for x in (*report.accepted_exercises, *report.ineligible_exercises))
    refs = refs or ("self-improvement:no-exercises",)
    digest = _digest(asdict(report))
    return hub.record_observation(EvidenceObservation(
        f"self-improvement-{digest[:20]}", report.project_id, "SELF_IMPROVEMENT_EXPERIMENT",
        f"{len(report.accepted_exercises)} clean exercises; {len(report.candidates)} candidates; no production mutation",
        refs, observed_at, 1.0))
