import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from fastapi.testclient import TestClient

from backend.database import session as session_module
from backend.main import app
from backend.models.base import Base
from backend.models.fraud_report import FraudReport
from backend.models.payment_account import PaymentAccount
from backend.models.risk_assessment import RiskAssessment
from backend.models.transaction import Transaction
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
        return account
    finally:
        db.close()


def test_risk_check_with_valid_recipient_and_save():
    reset_db()
    register_user("0911000001", "Recipient")
    create_account_for_phone("0911000001")

    for idx in range(2):
        phone = f"09120000{idx + 10}"
        register_user(phone, f"Reporter {idx}")
        token = login_user(phone)
        response = client.post(
            "/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "recipient_phone": "0911000001",
                "scam_type": "IMPERSONATION",
                "description": "This recipient requested urgent payment from a fake bank team.",
            },
        )
        assert response.status_code == 200

    sender = register_user("0913000001", "Checker")
    assert sender.status_code == 201
    token = login_user("0913000001")

    response = client.post(
        "/risk/check",
        headers={"Authorization": f"Bearer {token}"},
        json={"recipient_phone": "0911000001", "amount": 5000},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["score"] >= 0
    assert payload["level"] in {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    assert payload["recommendation"] in {"ALLOW", "REVIEW", "VERIFY", "STOP_AND_VERIFY"}

    db = session_module.SessionLocal()
    try:
        assessments = db.query(RiskAssessment).filter(RiskAssessment.recipient_phone == "0911000001").all()
        assert len(assessments) >= 1
    finally:
        db.close()


def test_risk_check_invalid_amount():
    reset_db()
    register_user("0911111111", "Recipient")
    create_account_for_phone("0911111111")
    token = login_user("0911111111")

    response = client.post(
        "/risk/check",
        headers={"Authorization": f"Bearer {token}"},
        json={"recipient_phone": "0911111111", "amount": 0},
    )

    assert response.status_code == 422


def test_risk_check_missing_recipient():
    reset_db()
    register_user("0911111111", "Recipient")
    create_account_for_phone("0911111111")
    token = login_user("0911111111")

    response = client.post(
        "/risk/check",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": 5000},
    )

    assert response.status_code == 422


def test_risk_check_recipient_not_found():
    reset_db()
    token = login_user("0911111111") if False else None
    register_user("0911111111", "User")
    token = login_user("0911111111")

    response = client.post(
        "/risk/check",
        headers={"Authorization": f"Bearer {token}"},
        json={"recipient_phone": "0919999999", "amount": 5000},
    )

    assert response.status_code == 404


def test_transaction_simulation_and_retrieval():
    reset_db()
    register_user("0911111111", "Sender")
    token = login_user("0911111111")

    response = client.post(
        "/transactions/simulate",
        headers={"Authorization": f"Bearer {token}"},
        json={"recipient_phone": "0912222222", "amount": 1500},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "SIMULATED"
    assert payload["amount"] == 1500
    assert payload["recipient_phone"] == "0912222222"

    transaction_id = payload["id"]
    get_response = client.get(
        f"/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == transaction_id


def test_transaction_unauthorized_access_rejected():
    reset_db()
    register_user("0911111111", "Sender")
    register_user("0911111112", "Other")
    sender_token = login_user("0911111111")
    other_token = login_user("0911111112")

    created = client.post(
        "/transactions/simulate",
        headers={"Authorization": f"Bearer {sender_token}"},
        json={"recipient_phone": "0912222222", "amount": 1000},
    )
    transaction_id = created.json()["id"]

    response = client.get(
        f"/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403


def test_submit_and_list_reports():
    reset_db()
    register_user("0911111111", "Reporter")
    token = login_user("0911111111")

    response = client.post(
        "/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "recipient_phone": "0912222222",
            "scam_type": "IMPERSONATION",
            "description": "This recipient claimed to be a bank employee and demanded an urgent payment.",
        },
    )

    assert response.status_code == 200
    assert response.json()["recipient_phone"] == "0912222222"

    list_response = client.get(
        "/reports",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1


def test_reports_submission_requires_authentication():
    reset_db()
    response = client.post(
        "/reports",
        json={
            "recipient_phone": "0912222222",
            "scam_type": "IMPERSONATION",
            "description": "This recipient claimed to be a bank employee and demanded an urgent payment.",
        },
    )

    assert response.status_code == 401


def test_recipient_summary_returns_data_for_existing_phone():
    reset_db()
    register_user("0917777777", "Recipient")
    create_account_for_phone("0917777777")
    reporter_phone = "0918888888"
    register_user(reporter_phone, "Reporter")
    token = login_user(reporter_phone)

    client.post(
        "/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "recipient_phone": "0917777777",
            "scam_type": "IMPERSONATION",
            "description": "This recipient requested a payment after impersonating a bank official.",
        },
    )

    recipient_token = login_user("0917777777")
    response = client.get(
        "/recipients/0917777777",
        headers={"Authorization": f"Bearer {recipient_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["phone"] == "0917777777"
    assert payload["fraud_report_count"] >= 1
    assert payload["risk_level"] in {"LOW", "MODERATE", "HIGH", "CRITICAL"}


def test_recipient_summary_missing_phone_returns_404():
    reset_db()
    register_user("0911111111", "User")
    token = login_user("0911111111")

    response = client.get(
        "/recipients/0919999999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
