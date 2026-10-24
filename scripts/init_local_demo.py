#!/usr/bin/env python3
"""Create a fresh, local-only SQLite database populated with synthetic demo data.

This script never opens .env and refuses to replace any existing demo database
or config file. It creates schema from current SQLAlchemy models (no migrations).
"""

import os
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEMO_DIR = ROOT / ".local-demo"
DB_PATH = DEMO_DIR / "adera-demo.sqlite3"
ENV_PATH = DEMO_DIR / "demo.env"
RECIPIENT_PHONE = "0912345678"


def main() -> int:
    DEMO_DIR.mkdir(mode=0o700, exist_ok=True)
    os.chmod(DEMO_DIR, 0o700)
    if DB_PATH.exists() or DB_PATH.is_symlink():
        print(f"Refusing to overwrite existing demo database: {DB_PATH}", file=sys.stderr)
        return 1
    database_url = f"sqlite:///{DB_PATH}"
    jwt_secret = None
    if ENV_PATH.exists() or ENV_PATH.is_symlink():
        if ENV_PATH.is_symlink() or not ENV_PATH.is_file():
            print(f"Refusing unexpected demo environment path: {ENV_PATH}", file=sys.stderr)
            return 1
        values = {}
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                values[key] = value
        if values.get("DATABASE_URL") != database_url or not values.get("JWT_SECRET_KEY"):
            print(f"Existing demo environment is not a resumable config for {DB_PATH}", file=sys.stderr)
            return 1
        jwt_secret = values["JWT_SECRET_KEY"]
    else:
        jwt_secret = secrets.token_urlsafe(48)
        env_content = (
            f"DATABASE_URL={database_url}\n"
            f"JWT_SECRET_KEY={jwt_secret}\n"
            "JWT_ALGORITHM=HS256\n"
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60\n"
        )
        env_fd = os.open(ENV_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(env_fd, "w", encoding="utf-8") as env_file:
            env_file.write(env_content)

    from passlib.context import CryptContext
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from backend.models import (  # noqa: F401 - import registers every model table
        AccountRelationship,
        Alert,
        FraudReport,
        PaymentAccount,
        RiskAssessment,
        ScamCase,
        Transaction,
        User,
    )
    from backend.models.base import Base

    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash_password = password_context.hash
    now = datetime.utcnow()
    analyst_password = secrets.token_urlsafe(15)

    try:
        Base.metadata.create_all(bind=engine)
        os.chmod(DB_PATH, 0o600)
        with Session.begin() as db:
            users = [
                User(phone=RECIPIENT_PHONE, name="Synthetic Demo Recipient", password_hash=hash_password(secrets.token_urlsafe(24)), role="USER"),
                User(phone="0900000001", name="Synthetic Reporter One", password_hash=hash_password(secrets.token_urlsafe(24)), role="USER"),
                User(phone="0900000002", name="Synthetic Reporter Two", password_hash=hash_password(secrets.token_urlsafe(24)), role="USER"),
                User(phone="0900000003", name="Synthetic Reporter Three", password_hash=hash_password(secrets.token_urlsafe(24)), role="USER"),
                User(phone="0933001122", name="Synthetic Linked Account A", password_hash=hash_password(secrets.token_urlsafe(24)), role="USER"),
                User(phone="0933001123", name="Synthetic Linked Account B", password_hash=hash_password(secrets.token_urlsafe(24)), role="USER"),
                User(phone="0999000001", name="Local Demo Analyst", password_hash=hash_password(analyst_password), role="ANALYST"),
            ]
            db.add_all(users)
            db.flush()
            by_phone = {user.phone: user for user in users}

            accounts = {
                phone: PaymentAccount(
                    user_id=by_phone[phone].id,
                    account_number=f"DEMO-{index:04d}",
                    provider="SYNTHETIC DEMO WALLET",
                )
                for index, phone in enumerate(
                    [RECIPIENT_PHONE, "0933001122", "0933001123"],
                    start=1,
                )
            }
            db.add_all(accounts.values())
            db.flush()

            report_specs = (
                ("0900000001", "IMPERSONATION"),
                ("0900000002", "IMPERSONATION"),
                ("0900000003", "FAKE_SELLER"),
                ("0900000001", "FAKE_SELLER"),
                ("0900000002", "ACCOUNT_TAKEOVER"),
                ("0900000003", "ACCOUNT_TAKEOVER"),
                ("0900000001", "IMPERSONATION"),
            )
            for index, (reporter_phone, scam_type) in enumerate(report_specs):
                db.add(
                    FraudReport(
                        reporter_id=by_phone[reporter_phone].id,
                        recipient_phone=RECIPIENT_PHONE,
                        scam_type=scam_type,
                        description=(
                            f"SYNTHETIC LOCAL DEMO report {index + 1}: example {scam_type.lower()} "
                            "payment request; no real person or transaction is represented."
                        ),
                        status="PENDING",
                        created_at=now - timedelta(days=index),
                    )
                )

            db.add_all(
                [
                    ScamCase(
                        recipient_phone=RECIPIENT_PHONE,
                        title="Synthetic impersonation review",
                        description="Synthetic-only demonstration investigation.",
                        scam_type="IMPERSONATION",
                        status="OPEN",
                        created_at=now - timedelta(days=5),
                    ),
                    ScamCase(
                        recipient_phone=RECIPIENT_PHONE,
                        title="Synthetic payment pattern review",
                        description="Synthetic-only demonstration investigation.",
                        scam_type="FAKE_SELLER",
                        status="INVESTIGATING",
                        created_at=now - timedelta(days=2),
                    ),
                ]
            )
            db.add_all(
                [
                    AccountRelationship(
                        source_account_id=accounts[RECIPIENT_PHONE].id,
                        target_account_id=accounts["0933001122"].id,
                        relationship_type="RELATED_ACCOUNT",
                    ),
                    AccountRelationship(
                        source_account_id=accounts[RECIPIENT_PHONE].id,
                        target_account_id=accounts["0933001123"].id,
                        relationship_type="TRANSACTION",
                    ),
                ]
            )
    except Exception:
        engine.dispose()
        raise

    engine.dispose()
    print("Created isolated SQLite demo database and synthetic records.")
    print(f"DATABASE_URL={database_url}")
    print("Demo recipient: 0912345678 (synthetic; existing payment account included)")
    print("Demo analyst phone: 0999000001")
    print(f"Demo analyst password (save this now): {analyst_password}")
    print(f"Environment file (mode 0600): {ENV_PATH}")
    print("Start both services bound to 127.0.0.1 only; this database is for local demo use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
