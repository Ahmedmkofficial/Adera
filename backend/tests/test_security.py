"""
Security & Hardening Test Suite
Owner: Tigiste (Member 6) - Backend Support, Alerts, Integration & Security
Covers:
  - OWASP Top 10 API Security Risks:
    1. Broken Object Level Authorization / Broken Access Control
    2. SQL Injection Resistance
    3. Input Validation & Strict Typing
    4. Information Leakage Prevention
"""
from backend.models.alert import Alert


def test_sql_injection_in_path_parameter_rejected(client, analyst_headers):
    sqli_payload = "1' OR '1'='1"
    response = client.get(f"/alerts/{sqli_payload}", headers=analyst_headers)
    assert response.status_code == 422


def test_sql_injection_in_query_parameter(client, analyst_headers):
    sqli_payload = "' OR 1=1;--"
    response = client.get(f"/alerts?status={sqli_payload}", headers=analyst_headers)
    assert response.status_code == 422


def test_sql_injection_in_decision_body(client, db_session, analyst_headers):
    from backend.models.scam_case import ScamCase

    case = ScamCase(
        title="Security Case",
        description="Testing injection safety",
        scam_type="OTHER",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()

    sqli_notes = "'); DROP TABLE alerts; --"
    response = client.post(
        f"/cases/{case.id}/decision",
        json={"decision": "FRAUD", "notes": sqli_notes},
        headers=analyst_headers,
    )
    assert response.status_code == 200

    alert_check = client.get("/alerts", headers=analyst_headers)
    assert alert_check.status_code == 200


def test_input_validation_empty_case_fields(client, analyst_headers):
    response = client.post(
        "/cases",
        json={"title": "", "description": "", "scam_type": "IMPERSONATION"},
        headers=analyst_headers,
    )
    assert response.status_code == 422


def test_input_validation_empty_notes(client, db_session, analyst_headers):
    from backend.models.scam_case import ScamCase

    case = ScamCase(
        title="Case For Notes Validation",
        description="Testing notes validation",
        scam_type="OTHER",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()

    response = client.post(
        f"/cases/{case.id}/decision",
        json={"decision": "FRAUD", "notes": ""},
        headers=analyst_headers,
    )
    assert response.status_code == 422


def test_broken_access_control_direct_object_reference(client, db_session, user_headers):
    alert = Alert(
        recipient_phone="0911000000",
        message="Sensitive investigation details",
        severity="CRITICAL",
        status="OPEN",
    )
    db_session.add(alert)
    db_session.commit()

    response = client.get(f"/alerts/{alert.id}", headers=user_headers)
    assert response.status_code == 403
