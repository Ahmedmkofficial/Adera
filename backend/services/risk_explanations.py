def build_reasons(risk_input):
    reasons = []

    if risk_input["independent_reports"] >= 2:
        reasons.append("Multiple independent fraud reports")
    if risk_input["recent_reports"] >= 1:
        reasons.append("Recent fraud reports exist")
    if risk_input["previous_scam_cases"] >= 1:
        reasons.append("Previous scam case exists")
    if risk_input["suspicious_relationships"] >= 1:
        reasons.append("Suspicious account relationship detected")
    if risk_input["repeated_scam_pattern"]:
        reasons.append("Repeated scam pattern detected")
    if risk_input["unusual_transaction"]:
        reasons.append("Unusual transaction behavior detected")

    return reasons
