import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-adera-tests-32-bytes")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from fastapi.testclient import TestClient

from backend.database import session as session_module
from backend.main import app
from backend.rate_limiter import limiter
from backend.auth.security import create_access_token, get_password_hash
from backend.models.alert import Alert
from backend.models.base import Base
from backend.models.fraud_report import FraudReport
from backend.models.payment_account import PaymentAccount
from backend.models.risk_assessment import RiskAssessment
from backend.models.transaction import Transaction
from backend.models.user import User

Base.metadata.create_all(bind=session_module.engine)
client = TestClient(app)


def reset_db():
    limiter.reset()
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


def make_analyst(phone):
    db = session_module.SessionLocal()
    try:
        user = db.query(User).filter(User.phone == phone).first()
        user.role = "ANALYST"
        db.commit()
    finally:
        db.close()
    return login_user(phone)


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


def test_repeated_high_risk_checks_reuse_active_alert():
    reset_db()
    recipient_phone = "0911000001"
    register_user(recipient_phone, "Synthetic Recipient")
    create_account_for_phone(recipient_phone)

    reporter_tokens = []
    db = session_module.SessionLocal()
    try:
        for index in range(7):
            reporter_phone = f"09120001{index:02d}"
            reporter = User(
                phone=reporter_phone,
                name=f"Synthetic Reporter {index}",
                password_hash=get_password_hash("secret123"),
                role="USER",
            )
            db.add(reporter)
            db.flush()
            reporter_tokens.append(create_access_token(reporter.id, reporter.role))
        db.commit()
    finally:
        db.close()

    for index, token in enumerate(reporter_tokens):
        response = client.post(
            "/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "recipient_phone": recipient_phone,
                "scam_type": "IMPERSONATION" if index % 2 else "FAKE_SELLER",
                "description": f"Synthetic repeat-alert test report {index} with an urgent payment request.",
            },
        )
        assert response.status_code == 200, response.text

    headers = {"Authorization": f"Bearer {reporter_tokens[0]}"}
    payload = {"recipient_phone": recipient_phone, "amount": 5000}
    first = client.post("/risk/check", headers=headers, json=payload)
    second = client.post("/risk/check", headers=headers, json=payload)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()

    db = session_module.SessionLocal()
    try:
        assessments = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.recipient_phone == recipient_phone)
            .all()
        )
        alerts = (
            db.query(Alert)
            .filter(
                Alert.recipient_phone == recipient_phone,
                Alert.status == "OPEN",
            )
            .all()
        )
        assert len(assessments) == 2
        assert len(alerts) == 1
        assert alerts[0].risk_assessment_id == assessments[-1].id
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
    sender = register_user("0911111111", "Sender").json()
    other = register_user("0911111112", "Other").json()
    token = login_user("0911111111")

    response = client.post(
        "/transactions/simulate",
        headers={"Authorization": f"Bearer {token}"},
        json={"sender_id": other["id"], "recipient_phone": "0912222222", "amount": 1500},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "SIMULATED"
    assert payload["amount"] == 1500
    assert payload["recipient_phone"] == "0912222222"
    assert payload["sender_id"] == sender["id"]

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


def test_regular_users_only_list_their_own_reports():
    reset_db()
    register_user("0911111111", "Reporter One")
    register_user("0911111112", "Reporter Two")
    token_one = login_user("0911111111")
    token_two = login_user("0911111112")
    body = {
        "recipient_phone": "0912222222",
        "scam_type": "IMPERSONATION",
        "description": "Synthetic access-control fixture report.",
    }

    own = client.post("/reports", headers={"Authorization": f"Bearer {token_one}"}, json=body)
    other = client.post("/reports", headers={"Authorization": f"Bearer {token_two}"}, json=body)
    assert own.status_code == other.status_code == 200

    listing = client.get("/reports", headers={"Authorization": f"Bearer {token_one}"})

    assert listing.status_code == 200
    assert [report["id"] for report in listing.json()] == [own.json()["id"]]


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
    recipient_token = make_analyst(reporter_phone)
    token = recipient_token

    client.post(
        "/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "recipient_phone": "0917777777",
            "scam_type": "IMPERSONATION",
            "description": "This recipient requested a payment after impersonating a bank official.",
        },
    )

    response = client.get(
        "/recipients/0917777777",
        headers={"Authorization": f"Bearer {recipient_token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["phone"] == "0917777777"
    assert payload["fraud_report_count"] >= 1
    assert payload["risk_level"] in {"LOW", "MODERATE", "HIGH", "CRITICAL"}

def test_recipient_summary_ignores_previous_transaction_assessment():
    reset_db()
    recipient_phone = "0917777788"
    register_user(recipient_phone, "Recipient")
    create_account_for_phone(recipient_phone)

    db = session_module.SessionLocal()
    try:
        db.add(
            RiskAssessment(
                recipient_phone=recipient_phone,
                score=99,
                level="CRITICAL",
                recommendation="STOP_AND_VERIFY",
            )
        )
        db.commit()
    finally:
        db.close()

    analyst_phone = "0917777789"
    register_user(analyst_phone, "Analyst")
    token = make_analyst(analyst_phone)
    response = client.get(
        f"/recipients/{recipient_phone}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["fraud_report_count"] == 0
    assert payload["risk_score"] < 99
    assert payload["risk_level"] != "CRITICAL"


def test_recipient_summary_missing_phone_returns_404():
    reset_db()
    register_user("0911111111", "User")
    token = make_analyst("0911111111")

    response = client.get(
        "/recipients/0919999999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
