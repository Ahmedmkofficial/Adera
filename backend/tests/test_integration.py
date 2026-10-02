"""
End-to-End Integration Flow Tests
Owner: Tigiste (Member 6) - Backend Support, Alerts, Integration & Security
Validates the Critical Flow:
  Risk Engine -> Alert -> Investigation -> Case -> Analyst Decision
"""
from backend.models.fraud_report import FraudReport
from backend.models.risk_assessment import RiskAssessment
from backend.services.risk_engine import calculate_risk
from backend.services.case_service import CaseService


def test_complete_investigation_and_decision_lifecycle(
    client, db_session, analyst_headers
):
    recipient_phone = "0912345678"

    for i in range(1, 8):
        db_session.add(
            FraudReport(
                reporter_id=i,
                recipient_phone=recipient_phone,
                description=f"Demanded urgent deposit for fake job fee #{i}",
                status="VERIFIED",
            )
        )
    db_session.commit()

    report_count = (
        db_session.query(FraudReport.reporter_id)
        .filter(FraudReport.recipient_phone == recipient_phone)
        .distinct()
        .count()
    )
    risk_output = calculate_risk(
        report_count=report_count,
        recent_report_count=3,
        related_case_count=2,
        suspicious_connection_count=1,
    )
    assert risk_output["score"] >= 75
    assert risk_output["level"] == "CRITICAL"

    assessment = RiskAssessment(
        recipient_phone=recipient_phone,
        score=risk_output["score"],
        level=risk_output["level"],
        recommendation=risk_output["recommendation"],
    )
    db_session.add(assessment)
    db_session.commit()

    alert = CaseService.create_alert_from_risk(
        db=db_session,
        recipient_phone=recipient_phone,
        risk_score=risk_output["score"],
        severity=risk_output["level"],
        message=f"Critical scam risk detected: {', '.join(risk_output['reasons'])}",
    )
    assert alert.id is not None
    assert alert.status == "OPEN"

    alerts_response = client.get("/alerts", headers=analyst_headers)
    assert alerts_response.status_code == 200
    alerts_data = alerts_response.json()
    assert len(alerts_data) >= 1
    found_alert = next(a for a in alerts_data if a["id"] == alert.id)
    assert found_alert["recipient_phone"] == recipient_phone
    assert found_alert["risk_score"] == risk_output["score"]
    assert found_alert["severity"] == "CRITICAL"

    detail_response = client.get(f"/alerts/{alert.id}", headers=analyst_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == alert.id

    patch_response = client.patch(
        f"/alerts/{alert.id}",
        json={"status": "INVESTIGATING"},
        headers=analyst_headers,
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "INVESTIGATING"

    case_payload = {
        "title": f"Investigation for recipient {recipient_phone}",
        "description": "7 independent reports of fake job scam fees with Telegram links.",
        "scam_type": "IMPERSONATION",
        "status": "OPEN",
    }
    create_case_resp = client.post("/cases", json=case_payload, headers=analyst_headers)
    assert create_case_resp.status_code == 201
    case_id = create_case_resp.json()["id"]

    decision_payload = {
        "decision": "FRAUD",
        "notes": "Multiple independent reports and related scam activity support the case.",
    }
    decision_resp = client.post(
        f"/cases/{case_id}/decision",
        json=decision_payload,
        headers=analyst_headers,
    )
    assert decision_resp.status_code == 200
    decision_data = decision_resp.json()
    assert decision_data["case_id"] == case_id
    assert decision_data["decision"] == "FRAUD"
    assert decision_data["status"] == "RESOLVED"

    final_case_resp = client.get(f"/cases/{case_id}", headers=analyst_headers)
    assert final_case_resp.status_code == 200
    final_data = final_case_resp.json()
    assert final_data["status"] == "RESOLVED"
    assert final_data["decision"] == "FRAUD"
    assert final_data["notes"] == decision_payload["notes"]

    resolve_alert_resp = client.patch(
        f"/alerts/{alert.id}",
        json={"status": "RESOLVED"},
        headers=analyst_headers,
    )
    assert resolve_alert_resp.status_code == 200
    assert resolve_alert_resp.json()["status"] == "RESOLVED"
