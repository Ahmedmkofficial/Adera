"""Backward-compatible public API for explainable risk scoring."""

import math
from typing import Any

from backend.services.risk_explanations import build_reasons
from backend.services.risk_rules import calculate_score


def get_risk_level(score: int) -> str:
    """Map an integer risk score to its established Adera level."""
    if (
        isinstance(score, bool)
        or not isinstance(score, int)
        or not 0 <= score <= 100
    ):
        raise ValueError("score must be an integer between 0 and 100")
    if score <= 24:
        return "LOW"
    if score <= 49:
        return "MODERATE"
    if score <= 74:
        return "HIGH"
    return "CRITICAL"


def get_recommendation(level: str) -> str:
    """Return the established recommendation for a validated risk level."""
    recommendations = {
        "LOW": "ALLOW",
        "MODERATE": "REVIEW",
        "HIGH": "VERIFY",
        "CRITICAL": "STOP_AND_VERIFY",
    }
    try:
        return recommendations[level]
    except KeyError as exc:
        raise ValueError(
            "level must be LOW, MODERATE, HIGH, or CRITICAL"
        ) from exc


def _non_negative_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


def calculate_risk(
    report_count: int = 0,
    recent_report_count: int = 0,
    related_case_count: int = 0,
    suspicious_connection_count: int = 0,
    independent_report_count: int | None = None,
    repeated_scam_pattern: bool = False,
    unusual_transaction: bool = False,
    transaction_amount: float | None = None,
) -> dict:
    """Calculate an explainable risk result using the existing API contract.

    ``report_count`` and the original four positional arguments remain
    supported. When supplied, ``independent_report_count`` is authoritative;
    otherwise ``report_count`` retains its legacy independent-report meaning.
    """
    independent_reports = (
        report_count
        if independent_report_count is None
        else independent_report_count
    )
    amount = 0.0 if transaction_amount is None else transaction_amount

    risk_input = {
        "independent_reports": _non_negative_int(
            independent_reports,
            "independent_report_count",
        ),
        "recent_reports": _non_negative_int(
            recent_report_count,
            "recent_report_count",
        ),
        "previous_scam_cases": _non_negative_int(
            related_case_count,
            "related_case_count",
        ),
        "suspicious_relationships": _non_negative_int(
            suspicious_connection_count,
            "suspicious_connection_count",
        ),
        "repeated_scam_pattern": repeated_scam_pattern,
        "unusual_transaction": unusual_transaction,
        "transaction_amount": amount,
    }

    for name in ("repeated_scam_pattern", "unusual_transaction"):
        if not isinstance(risk_input[name], bool):
            raise ValueError(f"{name} must be a boolean")

    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("transaction_amount must be numeric")
    if not math.isfinite(amount) or amount < 0:
        raise ValueError("transaction_amount must be finite and non-negative")

    score = calculate_score(risk_input)
    level = get_risk_level(score)
    return {
        "score": score,
        "level": level,
        "recommendation": get_recommendation(level),
        "reasons": build_reasons(risk_input),
    }
