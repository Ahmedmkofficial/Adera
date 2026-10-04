from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RiskRule:
    key: str
    weight: int
    explanation: str


RULES = (
    RiskRule(
        key="multiple_independent_reports",
        weight=20,
        explanation="Multiple independent fraud reports",
    ),
    RiskRule(
        key="recent_reports",
        weight=15,
        explanation="Recent fraud reports exist",
    ),
    RiskRule(
        key="previous_scam_case",
        weight=25,
        explanation="Previous scam case exists",
    ),
    RiskRule(
        key="suspicious_relationship",
        weight=15,
        explanation="Suspicious account relationship detected",
    ),
    RiskRule(
        key="repeated_scam_pattern",
        weight=10,
        explanation="Repeated scam pattern detected",
    ),
    RiskRule(
        key="unusual_transaction",
        weight=15,
        explanation="Unusual transaction behavior detected",
    ),
)


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} cannot be negative")
    return value


def validate_risk_input(risk_input: Mapping[str, Any]) -> None:
    required = {
        "transaction_amount",
        "independent_reports",
        "recent_reports",
        "previous_scam_cases",
        "suspicious_relationships",
        "repeated_scam_pattern",
        "unusual_transaction",
    }
    missing = required - set(risk_input)
    if missing:
        raise ValueError(f"Missing risk input fields: {sorted(missing)}")

    amount = risk_input["transaction_amount"]
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("transaction_amount must be numeric")
    if amount < 0:
        raise ValueError("transaction_amount cannot be negative")

    for field in (
        "independent_reports",
        "recent_reports",
        "previous_scam_cases",
        "suspicious_relationships",
    ):
        _positive_int(risk_input[field], field)

    for field in ("repeated_scam_pattern", "unusual_transaction"):
        if not isinstance(risk_input[field], bool):
            raise ValueError(f"{field} must be boolean")


def calculate_score(risk_input: Mapping[str, Any]) -> int:
    validate_risk_input(risk_input)

    score = 0
    if risk_input["independent_reports"] >= 2:
        score += 20
    if risk_input["recent_reports"] >= 1:
        score += 15
    if risk_input["previous_scam_cases"] >= 1:
        score += 25
    if risk_input["suspicious_relationships"] >= 1:
        score += 15
    if risk_input["repeated_scam_pattern"]:
        score += 10
    if risk_input["unusual_transaction"]:
        score += 15

    return min(score, 100)
