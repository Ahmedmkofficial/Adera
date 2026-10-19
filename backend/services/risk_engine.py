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

    if independent_report_count is None:
        independent_report_count = report_count

    score = 0
    reasons = []

    if independent_report_count >= 7:
        score += 20
        reasons.append("Multiple independent fraud reports")
    elif independent_report_count >= 3:
        score += 10
        reasons.append("Several independent fraud reports")
    elif independent_report_count >= 1:
        score += 5
        reasons.append("Fraud report exists")

    if recent_report_count >= 3:
        score += 15
        reasons.append("Recent fraud reports exist")
    elif recent_report_count >= 1:
        score += 5
        reasons.append("Recent fraud report exists")

    if related_case_count >= 2:
        score += 25
        reasons.append("Previous scam case exists")
    elif related_case_count == 1:
        score += 15
        reasons.append("Previous scam case detected")

    if suspicious_connection_count >= 2:
        score += 15
        reasons.append("Suspicious account relationship detected")
    elif suspicious_connection_count == 1:
        score += 10
        reasons.append("Suspicious account relationship detected")

    if repeated_scam_pattern:
        score += 10
        reasons.append("Repeated scam pattern detected")

    if unusual_transaction or (transaction_amount is not None and transaction_amount >= 5000):
        score += 10
        reasons.append("Unusual transaction behavior detected")

    score = min(score, 100)

    if score >= 75:
        level = "CRITICAL"
        recommendation = "STOP_AND_VERIFY"
    elif score >= 50:
        level = "HIGH"
        recommendation = "VERIFY"
    elif score >= 25:
        level = "MODERATE"
        recommendation = "REVIEW"
    else:
        level = "LOW"
        recommendation = "ALLOW"

    return {
        "score": score,
        "level": level,
        "recommendation": recommendation,
        "reasons": reasons,
    }