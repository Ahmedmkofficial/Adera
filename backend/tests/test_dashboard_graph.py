import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-adera-tests-32-bytes")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.auth.security import create_access_token
from backend.database import session as session_module
from backend.main import app
from backend.models.alert import Alert
from backend.models.base import Base
from backend.models.fraud_report import FraudReport
from backend.models.payment_account import PaymentAccount
from backend.models.relationship import AccountRelationship
from backend.models.risk_assessment import RiskAssessment
from backend.models.scam_case import ScamCase
from backend.models.transaction import Transaction
from backend.models.user import User
from backend.rate_limiter import limiter

Base.metadata.create_all(bind=session_module.engine)
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    limiter.reset()
    Base.metadata.drop_all(bind=session_module.engine)
    Base.metadata.create_all(bind=session_module.engine)
    yield


def create_user(db, phone, role="USER"):
    user = User(
        phone=phone,
        name=f"Test {phone}",
        password_hash="unused-test-password-hash",
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def bearer(user):
    token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


def test_dashboard_summary_counts_persisted_records():
    db = session_module.SessionLocal()
    try:
        analyst = create_user(db, "0910000001", "ANALYST")
        recipient = create_user(db, "0910000002")
        assessments = [
            RiskAssessment(
                recipient_phone=recipient.phone,
                score=80,
                level="CRITICAL",
                recommendation="STOP_AND_VERIFY",
            ),
            RiskAssessment(
                recipient_phone=recipient.phone,
                score=60,
                level="HIGH",
                recommendation="VERIFY",
            ),
        ]
        db.add_all(assessments)
        db.flush()
        db.add_all(
            [
                Alert(
                    recipient_phone=recipient.phone,
                    message="Critical recorded alert",
                    severity="CRITICAL",
                    status="OPEN",
                    risk_assessment_id=assessments[0].id,
                ),
                Alert(
                    recipient_phone=recipient.phone,
                    message="High recorded alert",
                    severity="HIGH",
                    status="RESOLVED",
                    risk_assessment_id=assessments[1].id,
                ),
                ScamCase(
                    recipient_phone=recipient.phone,
                    title="Open investigation",
                    description="Test case",
                    status="OPEN",
                ),
                ScamCase(
                    recipient_phone=recipient.phone,
                    title="Investigation in progress",
                    description="Test case",
                    status="INVESTIGATING",
                ),
                ScamCase(
                    recipient_phone=recipient.phone,
                    title="Resolved investigation",
                    description="Test case",
                    status="RESOLVED",
                ),
                FraudReport(
                    reporter_id=analyst.id,
                    recipient_phone=recipient.phone,
                    scam_type="IMPERSONATION",
                    description="First report",
                ),
                FraudReport(
                    reporter_id=analyst.id,
                    recipient_phone=recipient.phone,
                    scam_type="INVESTMENT",
                    description="Second report",
                ),
            ]
        )
        db.commit()
        headers = bearer(analyst)
    finally:
        db.close()

    response = client.get("/dashboard/summary", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "alerts": 2,
        "critical": 1,
        "high": 1,
        "open_cases": 2,
        "reports": 2,
    }


def test_dashboard_summary_empty_counts_are_zero():
    db = session_module.SessionLocal()
    try:
        analyst = create_user(db, "0910000003", "ANALYST")
        db.commit()
        headers = bearer(analyst)
    finally:
        db.close()

    response = client.get("/dashboard/summary", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "alerts": 0,
        "critical": 0,
        "high": 0,
        "open_cases": 0,
        "reports": 0,
    }


def test_recipient_graph_contains_only_recorded_relationships_transactions_and_reports():
    db = session_module.SessionLocal()
    try:
        analyst = create_user(db, "0910000004", "ANALYST")
        recipient = create_user(db, "0910000005")
        sender = create_user(db, "0910000006")
        root_account = PaymentAccount(
            user_id=recipient.id,
            account_number="GRAPH-ROOT",
            provider="TEST",
        )
        peer_account = PaymentAccount(
            user_id=sender.id,
            account_number="GRAPH-PEER",
            provider="TEST",
        )
        db.add_all([root_account, peer_account])
        db.flush()
        db.add(
            AccountRelationship(
                source_account_id=root_account.id,
                target_account_id=peer_account.id,
                relationship_type="SHARED_PHONE",
                created_at=datetime.utcnow(),
            )
        )
        db.add(
            Transaction(
                sender_id=sender.id,
                recipient_phone=recipient.phone,
                amount=1250,
                status="SIMULATED",
                created_at=datetime.utcnow(),
            )
        )
        db.add(
            FraudReport(
                reporter_id=analyst.id,
                recipient_phone=recipient.phone,
                scam_type="IMPERSONATION",
                description="A recorded report",
                created_at=datetime.utcnow(),
            )
        )
        db.commit()
        headers = bearer(analyst)
        recipient_phone = recipient.phone
        sender_phone = sender.phone
    finally:
        db.close()

    response = client.get(f"/recipients/{recipient_phone}/graph", headers=headers)

    assert response.status_code == 200
    graph = response.json()
    subject = next(node for node in graph["nodes"] if node["kind"] == "subject")
    account = next(node for node in graph["nodes"] if node["kind"] == "account")
    report = next(node for node in graph["nodes"] if node["kind"] == "report")
    assert graph["phone"] == recipient_phone
    assert graph["reports_total"] == 1
    assert subject["phone"] == recipient_phone
    assert account["phone"] == sender_phone
    assert report["summary"] == "A recorded report"
    assert {edge["type"] for edge in graph["edges"]} == {
        "SHARED_PHONE",
        "TRANSACTION",
        "REPORT",
    }
    relationship_edge = next(edge for edge in graph["edges"] if edge["type"] == "SHARED_PHONE")
    transaction_edge = next(edge for edge in graph["edges"] if edge["type"] == "TRANSACTION")
    assert relationship_edge["source"] == subject["id"]
    assert transaction_edge["target"] == subject["id"]
    assert len(graph["edges"]) == 3


def test_recipient_graph_for_existing_recipient_without_records_is_subject_only():
    db = session_module.SessionLocal()
    try:
        analyst = create_user(db, "0910000007", "ANALYST")
        recipient = create_user(db, "0910000008")
        db.commit()
        headers = bearer(analyst)
        recipient_phone = recipient.phone
    finally:
        db.close()

    response = client.get(f"/recipients/{recipient_phone}/graph", headers=headers)

    assert response.status_code == 200
    graph = response.json()
    assert graph["phone"] == recipient_phone
    assert graph["reports_total"] == 0
    assert [node["kind"] for node in graph["nodes"]] == ["subject"]
    assert graph["edges"] == []


def test_recipient_graph_returns_404_for_missing_recipient():
    db = session_module.SessionLocal()
    try:
        analyst = create_user(db, "0910000009", "ANALYST")
        db.commit()
        headers = bearer(analyst)
    finally:
        db.close()

    response = client.get("/recipients/0909999999/graph", headers=headers)

    assert response.status_code == 404


def test_dashboard_and_recipient_graph_reject_customer_role():
    db = session_module.SessionLocal()
    try:
        customer = create_user(db, "0910000010")
        recipient = create_user(db, "0910000011")
        db.commit()
        headers = bearer(customer)
        recipient_phone = recipient.phone
    finally:
        db.close()

    dashboard = client.get("/dashboard/summary", headers=headers)
    profile = client.get(f"/recipients/{recipient_phone}", headers=headers)
    graph = client.get(f"/recipients/{recipient_phone}/graph", headers=headers)

    assert dashboard.status_code == 403
    assert profile.status_code == 403
    assert graph.status_code == 403


def test_alert_list_and_detail_include_frontend_compatible_investigation_data():
    db = session_module.SessionLocal()
    try:
        analyst = create_user(db, "0910000012", "ANALYST")
        recipient = create_user(db, "0910000013")
        sender = create_user(db, "0910000014")
        assessment = RiskAssessment(
            recipient_phone=recipient.phone,
            score=65,
            level="HIGH",
            recommendation="VERIFY",
        )
        db.add(assessment)
        db.flush()
        alert = Alert(
            recipient_phone=recipient.phone,
            message="Persisted investigation reason",
            severity="HIGH",
            status="OPEN",
            risk_assessment_id=assessment.id,
        )
        db.add(alert)
        db.flush()
        db.add_all(
            [
                FraudReport(
                    reporter_id=sender.id,
                    recipient_phone=recipient.phone,
                    scam_type="IMPERSONATION",
                    description="A persisted report description.",
                ),
                Transaction(
                    sender_id=sender.id,
                    recipient_phone=recipient.phone,
                    amount=500,
                    status="SIMULATED",
                ),
            ]
        )
        db.commit()
        alert_id = alert.id
        recipient_phone = recipient.phone
        headers = bearer(analyst)
    finally:
        db.close()

    listed = client.get("/alerts", headers=headers)
    detail = client.get(f"/alerts/{alert_id}", headers=headers)

    assert listed.status_code == 200
    assert listed.json()[0]["message"] == "Persisted investigation reason"
    assert listed.json()[0]["risk_score"] == 65
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["alert"]["recipient_phone"] == recipient_phone
    assert payload["risk_assessment"]["recommendation"] == "VERIFY"
    assert payload["reasons"] == ["Persisted investigation reason"]
    assert payload["reports_total"] == 1
    assert payload["reports"][0]["summary"] == "A persisted report description."
    assert payload["transactions"][0]["counterparty"] == "0910000014"
    assert payload["transactions"][0]["amount"] == 500
    assert payload["case_id"] is None


def test_alert_backed_case_creation_and_decisions_update_alert_status():
    db = session_module.SessionLocal()
    try:
        analyst = create_user(db, "0910000015", "ANALYST")
        recipient = create_user(db, "0910000016")
        assessment = RiskAssessment(
            recipient_phone=recipient.phone,
            score=80,
            level="CRITICAL",
            recommendation="STOP_AND_VERIFY",
        )
        db.add(assessment)
        db.flush()
        alert = Alert(
            recipient_phone=recipient.phone,
            message="Recorded alert statement",
            severity="CRITICAL",
            status="OPEN",
            risk_assessment_id=assessment.id,
        )
        db.add(alert)
        db.commit()
        alert_id = alert.id
        headers = bearer(analyst)
    finally:
        db.close()

    created = client.post("/cases", headers=headers, json={"alert_id": alert_id})

    assert created.status_code == 200
    case_payload = created.json()
    assert case_payload["recipient_phone"] == "0910000016"
    case_id = case_payload["id"]

    db = session_module.SessionLocal()
    try:
        case = db.query(ScamCase).filter(ScamCase.id == case_id).one()
        alert = db.query(Alert).filter(Alert.id == alert_id).one()
        assert case.title == "Recorded alert statement"
        assert case.description == "Recorded alert statement"
        assert alert.status == "INVESTIGATING"
    finally:
        db.close()

    detail = client.get(f"/cases/{case_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["subject"] == "0910000016"
    assert detail.json()["score"] == 80
    assert detail.json()["payment"] is None
    assert detail.json()["evidence"]["reports"] == 0

    needs_info = client.post(
        f"/cases/{case_id}/decision",
        headers=headers,
        json={"decision": "NEEDS_MORE_INFORMATION"},
    )
    assert needs_info.status_code == 200

    db = session_module.SessionLocal()
    try:
        assert db.query(ScamCase).filter(ScamCase.id == case_id).one().status == "INVESTIGATING"
        assert db.query(Alert).filter(Alert.id == alert_id).one().status == "INVESTIGATING"
    finally:
        db.close()

    final = client.post(
        f"/cases/{case_id}/decision",
        headers=headers,
        json={"decision": "FRAUD"},
    )
    assert final.status_code == 200

    db = session_module.SessionLocal()
    try:
        assert db.query(ScamCase).filter(ScamCase.id == case_id).one().status == "RESOLVED"
        assert db.query(Alert).filter(Alert.id == alert_id).one().status == "RESOLVED"
    finally:
        db.close()


def test_case_creation_rejects_missing_alert_context_without_fabrication():
    db = session_module.SessionLocal()
    try:
        analyst = create_user(db, "0910000017", "ANALYST")
        db.commit()
        headers = bearer(analyst)
    finally:
        db.close()

    response = client.post("/cases", headers=headers, json={"alert_id": 999})

    assert response.status_code == 404

    response = client.post("/cases", headers=headers, json={"title": "", "description": ""})
    assert response.status_code == 422
