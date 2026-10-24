"""Human-readable explanations corresponding to Adera risk rule signals."""

from typing import Any, Mapping

from backend.services.risk_rules import evaluate_risk_signals


REASONS = {
    "multiple_independent_reports": "Multiple independent fraud reports",
    "several_independent_reports": "Several independent fraud reports",
    "fraud_report_exists": "Fraud report exists",
    "multiple_recent_reports": "Recent fraud reports exist",
    "recent_report_exists": "Recent fraud report exists",
    "previous_scam_cases": "Previous scam case exists",
    "previous_scam_case": "Previous scam case detected",
    "multiple_suspicious_relationships": "Suspicious account relationship detected",
    "suspicious_relationship": "Suspicious account relationship detected",
    "repeated_scam_pattern": "Repeated scam pattern detected",
    "unusual_transaction": "Unusual transaction behavior detected",
}


def build_reasons(risk_input: Mapping[str, Any]) -> list[str]:
    """Build stable, human-readable reasons for the evaluated risk signals."""
    return [
        REASONS[signal.key]
        for signal in evaluate_risk_signals(risk_input)
    ]
