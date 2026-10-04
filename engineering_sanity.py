from __future__ import annotations

from dataclasses import dataclass


_PRESSURE_TO_MPA = {
    "mpa": 1.0,
    "bar": 0.1,
    "psi": 0.006894757293168,
}
_LENGTH_TO_MM = {
    "mm": 1.0,
    "cm": 10.0,
    "m": 1000.0,
}
_RATE_TO_PER_HOUR = {
    "per_hour": 1.0,
    "per_minute": 60.0,
}


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: str
    dimension: str


def _factor(dimension: str, unit: str) -> float:
    table = {
        "pressure": _PRESSURE_TO_MPA,
        "length": _LENGTH_TO_MM,
        "rate": _RATE_TO_PER_HOUR,
    }.get(dimension)
    if table is None:
        raise ValueError("unsupported_dimension")
    key = unit.strip().lower()
    if key not in table:
        raise ValueError("unsupported_unit")
    return table[key]


def normalize(quantity: Quantity) -> float:
    if isinstance(quantity.value, bool) or not isinstance(quantity.value, (int, float)):
        raise ValueError("invalid_quantity_value")
    if quantity.value < 0:
        raise ValueError("negative_quantity_rejected")
    return float(quantity.value) * _factor(quantity.dimension, quantity.unit)


def compare(candidate: Quantity, requirement: Quantity, *, relation: str = "at_least") -> bool:
    if candidate.dimension != requirement.dimension:
        raise ValueError("quantity_dimension_mismatch")
    left = normalize(candidate)
    right = normalize(requirement)
    if relation == "at_least":
        return left >= right
    if relation == "at_most":
        return left <= right
    if relation == "equal":
        return abs(left - right) <= 1e-9
    raise ValueError("unsupported_quantity_relation")


def validate_model(candidate_model: str, required_model: str) -> bool:
    left, right = candidate_model.strip(), required_model.strip()
    if not left or not right:
        raise ValueError("invalid_model_identifier")
    return left.casefold() == right.casefold()
