import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from fastapi.testclient import TestClient

from backend.database import session as session_module
from backend.main import app
from backend.models.alert import Alert
from backend.models.base import Base
from backend.models.payment_account import PaymentAccount
from backend.models.relationship import AccountRelationship
from backend.models.user import User

Base.metadata.create_all(bind=session_module.engine)
client = TestClient(app)


def reset_db():
    Base.metadata.drop_all(bind=session_module.engine)
    Base.metadata.create_all(bind=session_module.engine)


def register_user(phone, name, password="secret123", role="USER"):
    return client.post(
        "/auth/register",
        json={
            "phone": phone,
            "name": name,
            "password": password,
            "role": role,
        },
    )


def login_user(phone, password="secret123"):
    response = client.post(
        "/auth/login",
        json={"phone": phone, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def create_account_for_phone(phone):
    db = session_module.SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        if user is None:
            raise ValueError(f"User {phone} does not exist")
        account = PaymentAccount(user_id=user.id, account_number=f"ACC-{phone}", provider="BANK")
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    finally:
        db.close()


def create_relation(source_phone, target_phone, relationship_type="RELATED_ACCOUNT"):
    db = session_module.SessionLocal()
    try:
        source = db.query(PaymentAccount).join(User, User.id == PaymentAccount.user_id).filter(User.phone == source_phone).first()
        target = db.query(PaymentAccount).join(User, User.id == PaymentAccount.user_id).filter(User.phone == target_phone).first()
        if source is None or target is None:
            raise ValueError("relationship accounts missing")
        relation = AccountRelationship(
            source_account_id=source.id,
            target_account_id=target.id,
            relationship_type=relationship_type,
        )
        db.add(relation)
        db.commit()
    finally:
        db.close()


def test_risk_check_high_risk_creates_alert_for_analyst():
    reset_db()
    recipient_phone = "0919000001"
    register_user(recipient_phone, "Recipient")
    create_account_for_phone(recipient_phone)

    for idx, scam_type in enumerate([
        "IMPERSONATION",
        "ACCOUNT_TAKEOVER",
        "LOAN_SCAM",
        "FAKE_PACKAGE",
        "ROMANCE_SCAM",
        "BILLING_SCAM",
        "FAKE_CALL",
    ]):
        reporter_phone = f"09180{idx:04d}"
        register_user(reporter_phone, f"Reporter {idx}")
        token = login_user(reporter_phone)
        response = client.post(
            "/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "recipient_phone": recipient_phone,
                "scam_type": scam_type,
                "description": "Urgent payment demanded by a fake authority.",
            },
        )
        assert response.status_code == 200

    for phone in ["0919000002", "0919000003"]:
        register_user(phone, f"Linked User {phone}")
        create_account_for_phone(phone)

    create_relation(recipient_phone, "0919000002", "RELATED_ACCOUNT")
    create_relation(recipient_phone, "0919000003", "TRANSACTION")

    analyst_phone = "0919100001"
    register_user(analyst_phone, "Analyst", role="ANALYST")
    analyst_token = login_user(analyst_phone)

    response = client.post(
        "/risk/check",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"recipient_phone": recipient_phone, "amount": 5200},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["level"] in {"HIGH", "CRITICAL"}

    db = session_module.SessionLocal()
    try:
        alerts = db.query(Alert).filter(Alert.recipient_phone == recipient_phone).all()
        assert len(alerts) >= 1
        assert alerts[0].severity in {"HIGH", "CRITICAL"}
    finally:
        db.close()


def test_analyst_can_investigate_alerts_and_create_case_and_decision():
    reset_db()
    recipient_phone = "0919200001"
    analyst_phone = "0919200002"
    register_user(recipient_phone, "Recipient")
    create_account_for_phone(recipient_phone)
    register_user(analyst_phone, "Analyst", role="ANALYST")
    analyst_token = login_user(analyst_phone)

    for idx, scam_type in enumerate(["IMPERSONATION", "LOAN_SCAM", "BILLING_SCAM", "FAKE_CALL", "ACCOUNT_TAKEOVER", "ROMANCE_SCAM", "IMPERSONATION"]):
        reporter_phone = f"09192{idx + 10:03d}"
        register_user(reporter_phone, f"Reporter {idx}")
        token = login_user(reporter_phone)
        client.post(
            "/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "recipient_phone": recipient_phone,
                "scam_type": scam_type,
                "description": "Urgent payment asked via impersonation.",
            },
        )

    response = client.post(
        "/risk/check",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"recipient_phone": recipient_phone, "amount": 9000},
    )
    assert response.status_code == 200
    alert_id = client.get("/alerts", headers={"Authorization": f"Bearer {analyst_token}"}).json()[0]["id"]

    alert_detail = client.get(f"/alerts/{alert_id}", headers={"Authorization": f"Bearer {analyst_token}"})
    assert alert_detail.status_code == 200
    assert alert_detail.json()["alert"]["id"] == alert_id

    case_response = client.post(
        f"/cases",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={
            "alert_id": alert_id,
            "title": "Potential impersonation fraud",
            "description": "Evidence indicates repeated scam behavior and suspicious connections.",
        },
    )
    assert case_response.status_code == 200
    case_payload = case_response.json()
    case_id = case_payload["id"]

    case_detail = client.get(f"/cases/{case_id}", headers={"Authorization": f"Bearer {analyst_token}"})
    assert case_detail.status_code == 200
    assert case_detail.json()["case"]["id"] == case_id

    decision_response = client.post(
        f"/cases/{case_id}/decision",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"decision": "FRAUD", "notes": "Independent reports confirm the pattern."},
    )
    assert decision_response.status_code == 200
    assert decision_response.json()["decision"] == "FRAUD"


def test_user_cannot_access_analyst_endpoints():
    reset_db()
    user_phone = "0919300001"
    register_user(user_phone, "Standard User")
    user_token = login_user(user_phone)

    response = client.get("/alerts", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403

    response = client.post(
        "/cases",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"title": "Unauthorized case", "description": "Should fail"},
    )
    assert response.status_code == 403
