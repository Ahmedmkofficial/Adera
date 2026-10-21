"""Pure scoring rules for the backward-compatible Adera risk engine."""

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RiskSignal:
    key: str
    points: int


REPORT_BANDS = (
    (7, 20, "multiple_independent_reports"),
    (3, 10, "several_independent_reports"),
    (1, 5, "fraud_report_exists"),
)
RECENT_REPORT_BANDS = (
    (3, 15, "multiple_recent_reports"),
    (1, 5, "recent_report_exists"),
)
CASE_BANDS = (
    (2, 25, "previous_scam_cases"),
    (1, 15, "previous_scam_case"),
)
RELATIONSHIP_BANDS = (
    (2, 15, "multiple_suspicious_relationships"),
    (1, 10, "suspicious_relationship"),
)


def _band_signal(
    value: int,
    bands: tuple[tuple[int, int, str], ...],
) -> RiskSignal | None:
    for minimum, points, key in bands:
        if value >= minimum:
            return RiskSignal(key=key, points=points)
    return None


def evaluate_risk_signals(risk_input: Mapping[str, Any]) -> tuple[RiskSignal, ...]:
    """Evaluate the existing Adera signals without applying risk levels."""
    signals: list[RiskSignal] = []

    banded_values = (
        (risk_input["independent_reports"], REPORT_BANDS),
        (risk_input["recent_reports"], RECENT_REPORT_BANDS),
        (risk_input["previous_scam_cases"], CASE_BANDS),
        (risk_input["suspicious_relationships"], RELATIONSHIP_BANDS),
    )
    for value, bands in banded_values:
        signal = _band_signal(value, bands)
        if signal is not None:
            signals.append(signal)

    if risk_input["repeated_scam_pattern"]:
        signals.append(RiskSignal("repeated_scam_pattern", 10))

    if (
        risk_input["unusual_transaction"]
        or risk_input["transaction_amount"] >= 5000
    ):
        signals.append(RiskSignal("unusual_transaction", 10))

    return tuple(signals)


def calculate_score(risk_input: Mapping[str, Any]) -> int:
    """Return the capped total using the existing develop scoring weights."""
    return min(sum(signal.points for signal in evaluate_risk_signals(risk_input)), 100)
