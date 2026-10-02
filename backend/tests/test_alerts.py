"""
Alert API Tests
Owner: Tigiste (Member 6) - Backend Support, Alerts, Integration & Security
Covers:
  - GET /alerts
  - GET /alerts/{id}
  - PATCH /alerts/{id}
  - Status filtering, not found (404), input validation (422)
"""
from backend.models.alert import Alert
from backend.models.risk_assessment import RiskAssessment


def test_get_alerts_empty(client, analyst_headers):
    response = client.get("/alerts", headers=analyst_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_alerts_populated_with_risk_score(client, db_session, analyst_headers):
    alert = Alert(
        recipient_phone="0912345678",
        message="Critical risk: multiple scam reports",
        severity="CRITICAL",
        status="OPEN",
    )
    assessment = RiskAssessment(
        recipient_phone="0912345678",
        score=82,
        level="CRITICAL",
        recommendation="STOP_AND_VERIFY",
    )
    db_session.add_all([alert, assessment])
    db_session.commit()

    response = client.get("/alerts", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == alert.id
    assert data[0]["recipient_phone"] == "0912345678"
    assert data[0]["severity"] == "CRITICAL"
    assert data[0]["status"] == "OPEN"
    assert data[0]["risk_score"] == 82


def test_get_alerts_filter_by_status(client, db_session, analyst_headers):
    alert_open = Alert(
        recipient_phone="0911111111",
        message="Alert 1",
        severity="HIGH",
        status="OPEN",
    )
    alert_resolved = Alert(
        recipient_phone="0922222222",
        message="Alert 2",
        severity="LOW",
        status="RESOLVED",
    )
    db_session.add_all([alert_open, alert_resolved])
    db_session.commit()

    response = client.get("/alerts?status=OPEN", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "OPEN"
    assert data[0]["recipient_phone"] == "0911111111"

    response_resolved = client.get("/alerts?status=RESOLVED", headers=analyst_headers)
    assert response_resolved.status_code == 200
    data_resolved = response_resolved.json()
    assert len(data_resolved) == 1
    assert data_resolved[0]["status"] == "RESOLVED"
    assert data_resolved[0]["recipient_phone"] == "0922222222"


def test_get_alert_by_id_success(client, db_session, analyst_headers):
    alert = Alert(
        recipient_phone="0933333333",
        message="Investigate recipient",
        severity="MODERATE",
        status="OPEN",
    )
    db_session.add(alert)
    db_session.commit()

    response = client.get(f"/alerts/{alert.id}", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == alert.id
    assert data["recipient_phone"] == "0933333333"
    assert data["severity"] == "MODERATE"


def test_get_alert_by_id_not_found(client, analyst_headers):
    response = client.get("/alerts/9999", headers=analyst_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_patch_alert_status_valid(client, db_session, analyst_headers):
    alert = Alert(
        recipient_phone="0944444444",
        message="Suspicious transaction flow",
        severity="HIGH",
        status="OPEN",
    )
    db_session.add(alert)
    db_session.commit()

    response1 = client.patch(
        f"/alerts/{alert.id}",
        json={"status": "INVESTIGATING"},
        headers=analyst_headers,
    )
    assert response1.status_code == 200
    assert response1.json()["status"] == "INVESTIGATING"

    response2 = client.patch(
        f"/alerts/{alert.id}",
        json={"status": "RESOLVED"},
        headers=analyst_headers,
    )
    assert response2.status_code == 200
    assert response2.json()["status"] == "RESOLVED"


def test_patch_alert_status_invalid_enum(client, db_session, analyst_headers):
    alert = Alert(
        recipient_phone="0955555555",
        message="Testing invalid status",
        severity="LOW",
        status="OPEN",
    )
    db_session.add(alert)
    db_session.commit()

    response = client.patch(
        f"/alerts/{alert.id}",
        json={"status": "INVALID_STATUS"},
        headers=analyst_headers,
    )
    assert response.status_code == 422


def test_patch_alert_not_found(client, analyst_headers):
    response = client.patch(
        "/alerts/9999",
        json={"status": "INVESTIGATING"},
        headers=analyst_headers,
    )
    assert response.status_code == 404
