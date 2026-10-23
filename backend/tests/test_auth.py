import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-adera-tests-32-bytes")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from jose import jwt

from backend.database import session as session_module
from backend.main import app
from backend.rate_limiter import limiter
from backend.models.base import Base
from backend.models.user import User
from backend.auth.security import get_password_hash, verify_password
from backend.auth.security import (
    _validate_algorithm,
    _validate_secret_key,
    _validate_token_expiry,
    decode_access_token,
)

TEST_JWT_KEY = "test-secret-key-for-adera-tests-32-bytes"

Base.metadata.create_all(bind=session_module.engine)

client = TestClient(app)


def reset_db():
    limiter.reset()
    Base.metadata.drop_all(bind=session_module.engine)
    Base.metadata.create_all(bind=session_module.engine)


def create_privileged_user(phone, role):
    db = session_module.SessionLocal()
    try:
        user = User(
            phone=phone,
            name=f"Test {role.title()}",
            password_hash=get_password_hash("secret123"),
            role=role,
        )
        db.add(user)
        db.commit()
    finally:
        db.close()


def test_health_check():
    reset_db()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_configured_local_frontend_and_rejects_other_origins():
    allowed = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"

    rejected = client.options(
        "/auth/login",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert rejected.status_code == 400
    assert "access-control-allow-origin" not in rejected.headers


def test_register_success():
    reset_db()
    payload = {"phone": "0911111111", "name": "Alice", "password": "secret123"}

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["phone"] == payload["phone"]
    assert body["name"] == payload["name"]
    assert body["role"] == "USER"
    assert "password_hash" not in body


def test_duplicate_registration():
    reset_db()
    payload = {"phone": "0911111111", "name": "Alice", "password": "secret123"}
    client.post("/auth/register", json=payload)

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_registration_rejects_passwords_over_bcrypt_byte_limit():
    reset_db()
    response = client.post(
        "/auth/register",
        json={"phone": "0911111111", "name": "Alice", "password": "A" * 73},
    )
    assert response.status_code == 422
    assert "72 UTF-8 bytes" in str(response.json())


def test_login_rejects_passwords_over_bcrypt_byte_limit():
    reset_db()
    response = client.post(
        "/auth/login",
        json={"phone": "0911111111", "password": "A" * 73},
    )
    assert response.status_code == 422


def test_password_byte_limit_counts_utf8_bytes():
    reset_db()
    response = client.post(
        "/auth/register",
        json={"phone": "0911111111", "name": "Alice", "password": "é" * 37},
    )
    assert response.status_code == 422


def test_login_success():
    reset_db()
    register_payload = {"phone": "0911111111", "name": "Alice", "password": "secret123"}
    client.post("/auth/register", json=register_payload)

    response = client.post("/auth/login", json={"phone": "0911111111", "password": "secret123"})

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["phone"] == "0911111111"
    assert body["user"]["role"] == "USER"
    assert "password_hash" not in body["user"]


def test_login_incorrect_password():
    reset_db()
    client.post("/auth/register", json={"phone": "0911111111", "name": "Alice", "password": "secret123"})

    response = client.post("/auth/login", json={"phone": "0911111111", "password": "wrongpassword"})

    assert response.status_code == 401


def test_password_hash_creation_and_verification():
    password = "Synthetic-Demo-Passphrase-42!"
    password_hash = get_password_hash(password)

    assert password_hash.startswith("$2b$")
    assert verify_password(password, password_hash)
    assert not verify_password("Incorrect-Demo-Passphrase-42!", password_hash)


def test_invalid_or_missing_jwt():
    reset_db()
    response_missing = client.get("/auth/me")
    assert response_missing.status_code in {401, 403}

    response_invalid = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token"})
    assert response_invalid.status_code in {401, 403}


def test_signed_token_with_non_integer_subject_is_unauthorized():
    token = jwt.encode(
        {"sub": "not-a-user-id", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        TEST_JWT_KEY,
        algorithm="HS256",
    )
    try:
        decode_access_token(token)
    except Exception as exc:
        from fastapi import HTTPException

        assert isinstance(exc, HTTPException)
        assert exc.status_code == 401
    else:
        raise AssertionError("invalid token subject must be rejected")


def test_jwt_algorithm_only_allows_hs256():
    assert _validate_algorithm("HS256") == "HS256"
    for algorithm in ("none", "HS384", "RS256", ""):
        try:
            _validate_algorithm(algorithm)
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"unsupported JWT algorithm accepted: {algorithm!r}")


def test_jwt_expiry_requires_integer_between_one_minute_and_one_day():
    assert _validate_token_expiry("1") == 1
    assert _validate_token_expiry("30") == 30
    assert _validate_token_expiry("1440") == 1440

    for value in ("0", "-1", "1441", "abc", "1.5"):
        try:
            _validate_token_expiry(value)
        except RuntimeError:
            pass
        else:
            raise AssertionError(f"invalid JWT expiry accepted: {value!r}")


def test_jwt_secret_rejects_short_and_example_placeholder_values():
    for secret in ("short", "change-me-in-production"):
        try:
            _validate_secret_key(secret)
        except RuntimeError:
            pass
        else:
            raise AssertionError("weak JWT secrets must fail configuration validation")
    assert _validate_secret_key(TEST_JWT_KEY) == TEST_JWT_KEY


def test_authenticated_user_me():
    reset_db()
    client.post("/auth/register", json={"phone": "0911111111", "name": "Alice", "password": "secret123"})
    login_response = client.post("/auth/login", json={"phone": "0911111111", "password": "secret123"})
    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["phone"] == "0911111111"
    assert body["role"] == "USER"
    assert "password_hash" not in body


def test_user_role_authorization():
    reset_db()
    client.post("/auth/register", json={"phone": "0911111111", "name": "Alice", "password": "secret123"})
    login_response = client.post("/auth/login", json={"phone": "0911111111", "password": "secret123"})
    token = login_response.json()["access_token"]

    response = client.get("/auth/user-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["message"] == "Access granted"


def test_analyst_role_authorization():
    reset_db()
    create_privileged_user("0911111111", "ANALYST")
    login_response = client.post("/auth/login", json={"phone": "0911111111", "password": "secret123"})
    token = login_response.json()["access_token"]

    response = client.get("/auth/analyst-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["message"] == "Access granted"


def test_admin_role_authorization():
    reset_db()
    create_privileged_user("0911111111", "ADMIN")
    login_response = client.post("/auth/login", json={"phone": "0911111111", "password": "secret123"})
    token = login_response.json()["access_token"]

    response = client.get("/auth/admin-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["message"] == "Access granted"


def test_public_registration_ignores_privileged_role_values():
    reset_db()
    for role in ("ANALYST", "ADMIN"):
        phone = "0911111111" if role == "ANALYST" else "0911111112"
        response = client.post(
            "/auth/register",
            json={"phone": phone, "name": "Public User", "password": "secret123", "role": role},
        )
        assert response.status_code == 201
        assert response.json()["role"] == "USER"


def test_admin_routes_reject_anonymous_and_regular_users():
    reset_db()
    paths = ("/admin/reports", "/admin/high-risk", "/admin/alerts")
    for path in paths:
        response = client.get(path)
        assert response.status_code in {401, 403}

    client.post("/auth/register", json={"phone": "0911111111", "name": "Alice", "password": "secret123"})
    token = client.post("/auth/login", json={"phone": "0911111111", "password": "secret123"}).json()["access_token"]
    for path in paths:
        response = client.get(path, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403


def test_admin_routes_allow_existing_privileged_roles():
    reset_db()
    paths = ("/admin/reports", "/admin/high-risk", "/admin/alerts")
    for index, role in enumerate(("ANALYST", "ADMIN")):
        phone = f"091111111{index}"
        create_privileged_user(phone, role)
        token = client.post("/auth/login", json={"phone": phone, "password": "secret123"}).json()["access_token"]
        for path in paths:
            response = client.get(path, headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
