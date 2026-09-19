from dataclasses import dataclass

from nexus_verticals.p0_measurement import P0MeasurementReport


@dataclass(frozen=True)
class P0PromotionDecision:
    promotable: bool
    blockers: tuple[str, ...]


def evaluate_p0_promotion(
    report: P0MeasurementReport,
    *,
    authority_regressions: int,
    contamination_regressions: int,
    independent_review_complete: bool,
) -> P0PromotionDecision:
    blockers: list[str] = []

    validation_errors = report.validate()
    if validation_errors:
        blockers.append("measurement report is invalid")

    for name, value in (
        ("authority_regressions", authority_regressions),
        ("contamination_regressions", contamination_regressions),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            blockers.append(f"{name} must be a non-negative integer")

    if authority_regressions != 0:
        blockers.append("authority regression count must be zero")
    if contamination_regressions != 0:
        blockers.append("cross-project contamination regression count must be zero")
    if not report.operational_metrics_available():
        blockers.append("both benchmark cases require operational measurements")
    if not independent_review_complete:
        blockers.append("independent review is incomplete")

    return P0PromotionDecision(promotable=not blockers, blockers=tuple(blockers))
