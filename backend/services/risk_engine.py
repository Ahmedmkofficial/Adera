from typing import Any, Dict, Mapping

from .risk_explanations import build_reasons
from .risk_rules import calculate_score, validate_risk_input


def get_risk_level(score: int) -> str:
    if score <= 24:
        return "LOW"
    if score <= 49:
        return "MODERATE"
    if score <= 74:
        return "HIGH"
    return "CRITICAL"


def get_recommendation(level: str) -> str:
    return {
        "LOW": "ALLOW",
        "MODERATE": "REVIEW",
        "HIGH": "VERIFY",
        "CRITICAL": "STOP_AND_VERIFY",
    }[level]


def assess_risk(risk_input: Mapping[str, Any]) -> Dict[str, Any]:
    
    validate_risk_input(risk_input)

    score = calculate_score(risk_input)
    level = get_risk_level(score)
    recommendation = get_recommendation(level)
    reasons = build_reasons(risk_input)

    return {
        "score": score,
        "level": level,
        "recommendation": recommendation,
        "reasons": reasons,
    }
