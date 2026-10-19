import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from fastapi.testclient import TestClient

from backend.database import session as session_module
from backend.main import app
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


def test_recipient_summary_reports_relationship_and_independent_reports():
    reset_db()
    recipient_phone = "0917000001"
    register_user(recipient_phone, "Recipient")
    recipient_account = create_account_for_phone(recipient_phone)

    other_phone = "0917000002"
    register_user(other_phone, "Related User")
    related_account = create_account_for_phone(other_phone)

    db = session_module.SessionLocal()
    try:
        db.add(
            AccountRelationship(
                source_account_id=recipient_account.id,
                target_account_id=related_account.id,
                relationship_type="RELATED_ACCOUNT",
            )
        )
        db.commit()
    finally:
        db.close()

    for reporter in ["0918000001", "0918000002"]:
        register_user(reporter, f"Reporter {reporter}")
        token = login_user(reporter)
        response = client.post(
            "/reports",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "recipient_phone": recipient_phone,
                "scam_type": "IMPERSONATION",
                "description": "This recipient impersonated a bank worker and requested urgent payment.",
            },
        )
        assert response.status_code == 200

    token = login_user(recipient_phone)
    response = client.get(
        f"/recipients/{recipient_phone}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["fraud_report_count"] == 2
    assert payload["independent_reporter_count"] == 2
    assert payload["suspicious_relationship_count"] == 1
