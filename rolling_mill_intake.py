"""Fail-closed readiness assessment for a hot-rolling engineering study.

This module collects evidence and exposes gaps. It does not calculate a pass schedule,
recommend setpoints, or authorize operation of a rolling mill.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path


REQUIRED_PATHS = (
    "project_id",
    "product.input_billet.cross_section_mm",
    "product.input_billet.length_mm",
    "product.input_billet.steel_grade",
    "product.target.width_options_mm",
    "product.target.thickness_range_mm",
    "product.target.standard",
    "mill.layout",
    "mill.rolls.reported_diameter_around",
    "mill.rolls.barrel_length",
    "mill.rolls.groove_drawing_locator",
    "drive.motor.nameplate_photo_locator",
    "drive.motor.rated_power_kw",
    "drive.motor.rated_speed_rpm",
    "drive.motor.rated_voltage_v",
    "drive.motor.rated_current_a",
    "drive.gearbox.ratio",
    "drive.gearbox.rated_output_torque_nm",
    "drive.gearbox.nameplate_photo_locator",
    "limits.maximum_roll_force_n",
    "limits.maximum_spindle_torque_nm",
    "limits.maximum_motor_current_a",
    "process.reheating_temperature_degC",
    "process.pass_schedule",
    "process.historical_successful_run_locator",
    "safety.guards_verified",
    "safety.emergency_stops_verified",
    "safety.loto_procedure_locator",
)

AMBIGUOUS_CLAIM_IDS = (
    "claim_billet_220x220x3000",
    "claim_target_widths_300_400_600",
    "claim_target_thickness_8_20",
    "claim_roughing_three_high",
    "claim_roll_diameter_550",
    "claim_barrel_length_1350",
    "claim_gearbox_15ton_ratio_10to1",
    "claim_existing_150x150_products",
    "claim_grade_st37",
)

POSITIVE_NUMERIC_PATHS = frozenset({
    "product.input_billet.length_mm", "drive.motor.rated_power_kw",
    "drive.motor.rated_speed_rpm", "drive.motor.rated_voltage_v",
    "drive.motor.rated_current_a", "drive.gearbox.rated_output_torque_nm",
    "limits.maximum_roll_force_n", "limits.maximum_spindle_torque_nm",
    "limits.maximum_motor_current_a", "process.reheating_temperature_degC",
})
TRUE_PATHS = frozenset({"safety.guards_verified", "safety.emergency_stops_verified"})
MEASUREMENT_PATHS = frozenset({"mill.rolls.reported_diameter_around", "mill.rolls.barrel_length"})


def _at(payload: dict, path: str):
    value = payload
    for segment in path.split("."):
        if not isinstance(value, dict) or segment not in value:
            return None
        value = value[segment]
    return value


def _meaningful(value) -> bool:
    if value is None or isinstance(value, bool) and value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.upper() not in {"UNKNOWN", "TBD", "PLACEHOLDER"}
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


@dataclass(frozen=True)
class RollingReadiness:
    status: str
    missing_paths: tuple[str, ...]
    unresolved_claims: tuple[str, ...]
    calculation_allowed: bool
    operation_change_allowed: bool
    next_gate: str


def assess(payload: dict) -> RollingReadiness:
    missing_list = []
    for path in REQUIRED_PATHS:
        value = _at(payload, path)
        if not _meaningful(value):
            missing_list.append(path)
        elif path in POSITIVE_NUMERIC_PATHS and (
            isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0
        ):
            missing_list.append(f"{path}:positive_number_required")
        elif path in TRUE_PATHS and value is not True:
            missing_list.append(f"{path}:explicit_true_required")
        elif path in MEASUREMENT_PATHS and (
            not isinstance(value, dict)
            or isinstance(value.get("value"), bool)
            or not isinstance(value.get("value"), (int, float))
            or value["value"] <= 0
            or value.get("unit") not in {"mm", "cm", "m"}
        ):
            missing_list.append(f"{path}:positive_value_and_metric_unit_required")
    section = _at(payload, "product.input_billet.cross_section_mm")
    if _meaningful(section) and (
        not isinstance(section, dict)
        or any(isinstance(section.get(axis), bool) or not isinstance(section.get(axis), (int, float))
               or section[axis] <= 0 for axis in ("width", "height"))
    ):
        missing_list.append("product.input_billet.cross_section_mm:width_height_required")
    ratio = _at(payload, "drive.gearbox.ratio")
    if _meaningful(ratio) and (
        not isinstance(ratio, dict)
        or any(isinstance(ratio.get(side), bool) or not isinstance(ratio.get(side), (int, float))
               or ratio[side] <= 0 for side in ("input", "output"))
    ):
        missing_list.append("drive.gearbox.ratio:input_output_required")
    widths = _at(payload, "product.target.width_options_mm")
    if _meaningful(widths) and (
        not isinstance(widths, list) or not widths
        or any(isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0 for value in widths)
    ):
        missing_list.append("product.target.width_options_mm:positive_number_list_required")
    thickness = _at(payload, "product.target.thickness_range_mm")
    if _meaningful(thickness) and (
        not isinstance(thickness, dict)
        or any(isinstance(thickness.get(bound), bool) or not isinstance(thickness.get(bound), (int, float))
               or thickness[bound] <= 0 for bound in ("min", "max"))
        or thickness["min"] > thickness["max"]
    ):
        missing_list.append("product.target.thickness_range_mm:min_max_required")
    missing = tuple(dict.fromkeys(missing_list))
    claims = payload.get("initial_claims", [])
    resolved = {
        item.get("claim_id") for item in claims
        if isinstance(item, dict) and item.get("verification_state") == "VERIFIED"
        and _meaningful(item.get("meaning")) and _meaningful(item.get("unit"))
        and _meaningful(item.get("evidence_locator"))
    }
    unresolved = tuple(claim_id for claim_id in AMBIGUOUS_CLAIM_IDS if claim_id not in resolved)
    ready = not missing and not unresolved
    return RollingReadiness(
        status="READY_FOR_RETROSPECTIVE_CALCULATION" if ready else "READY_FOR_ENGINEER_INTERVIEW",
        missing_paths=missing,
        unresolved_claims=unresolved,
        calculation_allowed=ready,
        operation_change_allowed=False,
        next_gate="independent engineer review of measured historical pass data" if ready
        else "answer questionnaire and attach nameplates, drawings, and one historical run",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    result = assess(json.loads(args.input.read_text(encoding="utf-8")))
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
