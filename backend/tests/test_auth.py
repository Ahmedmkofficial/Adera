import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")

from fastapi.testclient import TestClient

from backend.database import session as session_module
from backend.main import app
from backend.models.base import Base

Base.metadata.create_all(bind=session_module.engine)

client = TestClient(app)


def reset_db():
    Base.metadata.drop_all(bind=session_module.engine)
    Base.metadata.create_all(bind=session_module.engine)


def test_health_check():
    reset_db()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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


def test_invalid_or_missing_jwt():
    reset_db()
    response_missing = client.get("/auth/me")
    assert response_missing.status_code in {401, 403}

    response_invalid = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token"})
    assert response_invalid.status_code in {401, 403}


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
    client.post("/auth/register", json={"phone": "0911111111", "name": "Analyst", "password": "secret123", "role": "ANALYST"})
    login_response = client.post("/auth/login", json={"phone": "0911111111", "password": "secret123"})
    token = login_response.json()["access_token"]

    response = client.get("/auth/analyst-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["message"] == "Access granted"


def test_admin_role_authorization():
    reset_db()
    client.post("/auth/register", json={"phone": "0911111111", "name": "Admin", "password": "secret123", "role": "ADMIN"})
    login_response = client.post("/auth/login", json={"phone": "0911111111", "password": "secret123"})
    token = login_response.json()["access_token"]

    response = client.get("/auth/admin-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["message"] == "Access granted"
