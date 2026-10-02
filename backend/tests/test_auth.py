"""
Authentication & Authorization Security Tests
Owner: Tigiste (Member 6) - Backend Support, Alerts, Integration & Security
Covers:
  - Missing token (401)
  - Malformed / invalid token (401)
  - Expired token (401)
  - Broken Access Control: Normal USER attempting analyst endpoints (403)
  - Authorized access: ANALYST and ADMIN roles (200)
"""
from backend.models.alert import Alert
from backend.models.scam_case import ScamCase


def test_missing_token_on_alerts_rejected(client, unauth_headers):
    response = client.get("/alerts", headers=unauth_headers)
    assert response.status_code == 401
    assert "Missing authentication credentials" in response.json()["detail"]


def test_missing_token_on_cases_rejected(client, unauth_headers):
    response = client.get("/cases", headers=unauth_headers)
    assert response.status_code == 401


def test_invalid_bearer_format_rejected(client):
    response = client.get("/alerts", headers={"Authorization": "Token not-a-bearer"})
    assert response.status_code == 401
    assert "Invalid authorization header format" in response.json()["detail"]


def test_unrecognized_token_rejected(client):
    response = client.get("/alerts", headers={"Authorization": "Bearer non-existent-token"})
    assert response.status_code == 401
    assert "Invalid or unrecognized" in response.json()["detail"]


def test_expired_token_rejected(client):
    response = client.get("/alerts", headers={"Authorization": "Bearer expired-token"})
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


def test_broken_access_control_user_cannot_access_alerts(client, user_headers):
    response = client.get("/alerts", headers=user_headers)
    assert response.status_code == 403
    assert "lacks required permissions" in response.json()["detail"]


def test_broken_access_control_user_cannot_patch_alert(client, db_session, user_headers):
    alert = Alert(
        recipient_phone="0911223344",
        message="Suspicious report",
        severity="HIGH",
        status="OPEN",
    )
    db_session.add(alert)
    db_session.commit()

    response = client.patch(
        f"/alerts/{alert.id}",
        json={"status": "RESOLVED"},
        headers=user_headers,
    )
    assert response.status_code == 403


def test_broken_access_control_user_cannot_access_cases(client, user_headers):
    response = client.get("/cases", headers=user_headers)
    assert response.status_code == 403


def test_broken_access_control_user_cannot_submit_decision(client, db_session, user_headers):
    case = ScamCase(
        title="Unauthorized test case",
        description="Testing that users cannot submit decisions",
        scam_type="OTHER",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()

    response = client.post(
        f"/cases/{case.id}/decision",
        json={"decision": "FRAUD", "notes": "Hacker attempt"},
        headers=user_headers,
    )
    assert response.status_code == 403


def test_analyst_role_permitted(client, analyst_headers):
    response = client.get("/alerts", headers=analyst_headers)
    assert response.status_code == 200


def test_admin_role_permitted(client, admin_headers):
    response = client.get("/alerts", headers=admin_headers)
    assert response.status_code == 200
