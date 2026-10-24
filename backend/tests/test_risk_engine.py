import pytest

from backend.services.risk_engine import (
    calculate_risk,
    get_recommendation,
    get_risk_level,
)


@pytest.mark.parametrize(
    ("score", "level", "recommendation"),
    [
        (0, "LOW", "ALLOW"),
        (24, "LOW", "ALLOW"),
        (25, "MODERATE", "REVIEW"),
        (49, "MODERATE", "REVIEW"),
        (50, "HIGH", "VERIFY"),
        (74, "HIGH", "VERIFY"),
        (75, "CRITICAL", "STOP_AND_VERIFY"),
        (100, "CRITICAL", "STOP_AND_VERIFY"),
    ],
)
def test_risk_level_and_recommendation_boundaries(score, level, recommendation):
    assert get_risk_level(score) == level
    assert get_recommendation(level) == recommendation


def test_risk_level_rejects_invalid_score():
    for score in (-1, 101, True, 24.5):
        with pytest.raises(ValueError):
            get_risk_level(score)


def test_recommendation_rejects_invalid_level():
    with pytest.raises(ValueError):
        get_recommendation("UNKNOWN")


def test_existing_positional_call_and_report_bands_are_compatible():
    # Seven independent reports: +20; three recent: +15; one case: +15;
    # one relationship: +10; this legacy call totals 60 and remains HIGH.
    result = calculate_risk(7, 3, 1, 1)

    assert result == {
        "score": 60,
        "level": "HIGH",
        "recommendation": "VERIFY",
        "reasons": [
            "Multiple independent fraud reports",
            "Recent fraud reports exist",
            "Previous scam case detected",
            "Suspicious account relationship detected",
        ],
    }


def test_explicit_independent_report_count_overrides_legacy_report_count():
    result = calculate_risk(report_count=7, independent_report_count=1)
    assert result["score"] == 5
    assert result["reasons"] == ["Fraud report exists"]


def test_each_existing_signal_has_an_explanation_and_score():
    result = calculate_risk(
        independent_report_count=3,
        recent_report_count=1,
        related_case_count=1,
        suspicious_connection_count=1,
        repeated_scam_pattern=True,
        unusual_transaction=True,
    )

    assert result["score"] == 60
    assert result["level"] == "HIGH"
    assert result["reasons"] == [
        "Several independent fraud reports",
        "Recent fraud report exists",
        "Previous scam case detected",
        "Suspicious account relationship detected",
        "Repeated scam pattern detected",
        "Unusual transaction behavior detected",
    ]


def test_transaction_amount_threshold_is_explained():
    assert calculate_risk(transaction_amount=4999.99)["score"] == 0
    threshold_result = calculate_risk(transaction_amount=5000)
    assert threshold_result["score"] == 10
    assert threshold_result["reasons"] == ["Unusual transaction behavior detected"]


@pytest.mark.parametrize(
    ("kwargs", "field"),
    [
        ({"report_count": -1}, "independent_report_count"),
        ({"recent_report_count": 1.5}, "recent_report_count"),
        ({"related_case_count": True}, "related_case_count"),
        ({"suspicious_connection_count": -1}, "suspicious_connection_count"),
        ({"repeated_scam_pattern": 1}, "repeated_scam_pattern"),
        ({"unusual_transaction": "yes"}, "unusual_transaction"),
        ({"transaction_amount": float("nan")}, "transaction_amount"),
        ({"transaction_amount": float("inf")}, "transaction_amount"),
        ({"transaction_amount": -1}, "transaction_amount"),
    ],
)
def test_invalid_risk_inputs_are_rejected(kwargs, field):
    with pytest.raises(ValueError, match=field):
        calculate_risk(**kwargs)


def test_maximum_current_signal_combination_scores_95():
    result = calculate_risk(
        independent_report_count=100,
        recent_report_count=100,
        related_case_count=100,
        suspicious_connection_count=100,
        repeated_scam_pattern=True,
        unusual_transaction=True,
    )

    assert result["score"] == 95
    assert result["level"] == "CRITICAL"
