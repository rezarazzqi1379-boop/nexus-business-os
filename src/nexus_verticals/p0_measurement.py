from dataclasses import dataclass
from typing import Literal


MeasurementMaturity = Literal["replay_tested", "human_reviewed", "operationally_measured"]


@dataclass(frozen=True)
class ProjectMeasurement:
    project_id: str
    case_type: Literal["hydrotester", "can_forming"]
    maturity: MeasurementMaturity
    source_refs: tuple[str, ...]
    hazards_tested: int
    hazards_detected: int
    unsafe_equivalence_or_selection_blocked: int
    unresolved_blockers: int
    human_corrections: int | None = None
    elapsed_minutes_to_decision: float | None = None
    commercial_value_usd: float | None = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            errors.append("project_id is required")
        if self.case_type not in {"hydrotester", "can_forming"}:
            errors.append("unsupported case_type")
        if self.maturity not in {"replay_tested", "human_reviewed", "operationally_measured"}:
            errors.append("unsupported maturity")
        if not self.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            errors.append("at least one source_ref is required")
        for name, value in (
            ("hazards_tested", self.hazards_tested),
            ("hazards_detected", self.hazards_detected),
            ("unsafe_equivalence_or_selection_blocked", self.unsafe_equivalence_or_selection_blocked),
            ("unresolved_blockers", self.unresolved_blockers),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"{name} must be a non-negative integer")
        if isinstance(self.hazards_tested, int) and isinstance(self.hazards_detected, int):
            if self.hazards_detected > self.hazards_tested:
                errors.append("hazards_detected cannot exceed hazards_tested")
        if self.human_corrections is not None:
            if not isinstance(self.human_corrections, int) or isinstance(self.human_corrections, bool) or self.human_corrections < 0:
                errors.append("human_corrections must be a non-negative integer when present")
        if self.elapsed_minutes_to_decision is not None and self.elapsed_minutes_to_decision < 0:
            errors.append("elapsed_minutes_to_decision must be non-negative when present")
        if self.commercial_value_usd is not None and self.commercial_value_usd < 0:
            errors.append("commercial_value_usd must be non-negative when present")

        if self.maturity == "replay_tested":
            if self.human_corrections is not None or self.elapsed_minutes_to_decision is not None or self.commercial_value_usd is not None:
                errors.append("replay_tested records cannot claim human, timing, or commercial measurements")
        if self.maturity == "human_reviewed" and self.human_corrections is None:
            errors.append("human_reviewed requires human_corrections")
        if self.maturity == "operationally_measured":
            if self.human_corrections is None or self.elapsed_minutes_to_decision is None:
                errors.append("operationally_measured requires correction and elapsed-time measurements")
        return errors


@dataclass(frozen=True)
class P0MeasurementReport:
    hydrotester: ProjectMeasurement
    can_forming: ProjectMeasurement

    def validate(self) -> list[str]:
        errors = self.hydrotester.validate() + self.can_forming.validate()
        if self.hydrotester.case_type != "hydrotester":
            errors.append("hydrotester measurement has wrong case_type")
        if self.can_forming.case_type != "can_forming":
            errors.append("can_forming measurement has wrong case_type")
        return errors

    def replay_detection_rate(self) -> float | None:
        tested = self.hydrotester.hazards_tested + self.can_forming.hazards_tested
        detected = self.hydrotester.hazards_detected + self.can_forming.hazards_detected
        if tested == 0:
            return None
        return detected / tested

    def operational_metrics_available(self) -> bool:
        return (
            self.hydrotester.maturity == "operationally_measured"
            and self.can_forming.maturity == "operationally_measured"
        )

    def commercial_roi_available(self) -> bool:
        return (
            self.operational_metrics_available()
            and self.hydrotester.commercial_value_usd is not None
            and self.can_forming.commercial_value_usd is not None
        )
