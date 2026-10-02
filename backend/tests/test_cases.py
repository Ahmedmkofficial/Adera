"""
Case & Analyst Decision API Tests
Owner: Tigiste (Member 6) - Backend Support, Alerts, Integration & Security
Covers:
  - GET /cases
  - POST /cases
  - GET /cases/{id}
  - POST /cases/{id}/decision (FRAUD, FALSE_POSITIVE, NEEDS_MORE_INFORMATION)
  - Decision validation, missing notes, 404 handling
"""
from backend.models.scam_case import ScamCase


def test_get_cases_empty(client, analyst_headers):
    response = client.get("/cases", headers=analyst_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_case_success(client, analyst_headers):
    payload = {
        "title": "Impersonation scam targeting seniors",
        "description": "Victim reported being called by someone claiming to be bank manager",
        "scam_type": "IMPERSONATION",
        "status": "OPEN",
    }
    response = client.post("/cases", json=payload, headers=analyst_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == payload["title"]
    assert data["scam_type"] == "IMPERSONATION"
    assert data["status"] == "OPEN"


def test_get_case_by_id_success(client, db_session, analyst_headers):
    case = ScamCase(
        title="Lottery Scam",
        description="Fake lottery prize claiming fee required",
        scam_type="ADVANCE_FEE",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()

    response = client.get(f"/cases/{case.id}", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == case.id
    assert data["title"] == "Lottery Scam"


def test_get_case_by_id_not_found(client, analyst_headers):
    response = client.get("/cases/9999", headers=analyst_headers)
    assert response.status_code == 404


def test_record_decision_fraud(client, db_session, analyst_headers):
    case = ScamCase(
        title="High-risk investment syndicate",
        description="Victims reported Telegram investment group scam",
        scam_type="INVESTMENT",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()

    decision_payload = {
        "decision": "FRAUD",
        "notes": "Multiple independent reports and related scam activity support the case.",
    }
    response = client.post(
        f"/cases/{case.id}/decision",
        json=decision_payload,
        headers=analyst_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case.id
    assert data["decision"] == "FRAUD"
    assert data["status"] == "RESOLVED"

    case_resp = client.get(f"/cases/{case.id}", headers=analyst_headers)
    assert case_resp.status_code == 200
    assert case_resp.json()["status"] == "RESOLVED"
    assert case_resp.json()["decision"] == "FRAUD"
    assert case_resp.json()["notes"] == decision_payload["notes"]


def test_record_decision_false_positive(client, db_session, analyst_headers):
    case = ScamCase(
        title="Family transfer flagged erroneously",
        description="Transfer between verified family members",
        scam_type="OTHER",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()

    decision_payload = {
        "decision": "FALSE_POSITIVE",
        "notes": "Account verified as legitimate family transfer after contacting sender.",
    }
    response = client.post(
        f"/cases/{case.id}/decision",
        json=decision_payload,
        headers=analyst_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case.id
    assert data["decision"] == "FALSE_POSITIVE"
    assert data["status"] == "RESOLVED"


def test_record_decision_needs_more_information(client, db_session, analyst_headers):
    case = ScamCase(
        title="Unclear relationship transaction",
        description="Single unconfirmed report with high transaction amount",
        scam_type="UNKNOWN",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()

    decision_payload = {
        "decision": "NEEDS_MORE_INFORMATION",
        "notes": "Requested transaction history and additional details from reporting party.",
    }
    response = client.post(
        f"/cases/{case.id}/decision",
        json=decision_payload,
        headers=analyst_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case.id
    assert data["decision"] == "NEEDS_MORE_INFORMATION"
    assert data["status"] == "INVESTIGATING"


def test_record_decision_invalid_type(client, db_session, analyst_headers):
    case = ScamCase(
        title="Testing invalid decision",
        description="Testing validation rejection",
        scam_type="OTHER",
        status="OPEN",
    )
    db_session.add(case)
    db_session.commit()

    response = client.post(
        f"/cases/{case.id}/decision",
        json={"decision": "NOT_A_VALID_DECISION", "notes": "Some notes"},
        headers=analyst_headers,
    )
    assert response.status_code == 422


def test_record_decision_missing_notes(client, db_session, analyst_headers):
    case = ScamCase(
        title="Testing missing notes",
        description="Testing validation rejection",
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


def test_record_decision_case_not_found(client, analyst_headers):
    response = client.post(
        "/cases/9999/decision",
        json={"decision": "FRAUD", "notes": "Valid notes"},
        headers=analyst_headers,
    )
    assert response.status_code == 404
