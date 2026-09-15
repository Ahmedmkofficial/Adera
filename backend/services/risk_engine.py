def calculate_risk(
    report_count: int,
    recent_report_count: int,
    related_case_count: int,
    suspicious_connection_count: int,
) -> dict:

    score = 0
    reasons = []

    # Reports from different users
    if report_count >= 7:
        score += 35
        reasons.append("Multiple independent fraud reports")
    elif report_count >= 3:
        score += 20
        reasons.append("Several fraud reports")
    elif report_count >= 1:
        score += 10
        reasons.append("Fraud report exists")

    # Recent reports
    if recent_report_count >= 3:
        score += 20
        reasons.append("Multiple recent reports")

    # Related scam cases
    if related_case_count >= 2:
        score += 20
        reasons.append("Related scam cases detected")
    elif related_case_count == 1:
        score += 10
        reasons.append("Related scam case detected")

    # Suspicious relationships
    if suspicious_connection_count >= 2:
        score += 15
        reasons.append("Suspicious connections detected")

    score = min(score, 100)

    if score >= 75:
        level = "CRITICAL"
        recommendation = "STOP_AND_VERIFY"
    elif score >= 50:
        level = "HIGH"
        recommendation = "VERIFY_RECIPIENT"
    elif score >= 25:
        level = "MODERATE"
        recommendation = "PROCEED_WITH_CAUTION"
    else:
        level = "LOW"
        recommendation = "PROCEED"

    return {
        "score": score,
        "level": level,
        "recommendation": recommendation,
        "reasons": reasons,
    }