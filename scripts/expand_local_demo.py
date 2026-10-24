#!/usr/bin/env python3
"""Idempotently expand the isolated local Adera SQLite demo database.

The CLI accepts only the repository's fixed .local-demo database. Tests may call
expand_demo_dataset with a separately-created temporary SQLite fixture.
"""

from __future__ import annotations

import os
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DEMO_DIR = ROOT / ".local-demo"
DB_PATH = DEMO_DIR / "adera-demo.sqlite3"
ENV_PATH = DEMO_DIR / "demo.env"
BASE_RECIPIENT = "0912345678"
ANALYST_PHONE = "0999000001"
REPORT_MARKER = "SYNTHETIC EXPANSION REPORT"
CASE_MARKER = "SYNTHETIC EXPANSION CASE"
SCENARIOS: dict[str, dict[str, Any]] = {
    "0912345601": {"case_count": 1, "amount": 1000, "reports": ["FAKE_SELLER"] * 3},
    "0912345602": {
        "case_count": 1,
        "amount": 5000,
        "reports": ["ACCOUNT_TAKEOVER", "IMPERSONATION", "FAKE_SELLER", "INVESTMENT_SCAM", "ACCOUNT_TAKEOVER"],
    },
    "0912345603": {"case_count": 1, "amount": 1000, "reports": ["IMPERSONATION", "FAKE_SELLER"]},
    "0912345604": {
        "case_count": 2,
        "amount": 5000,
        "reports": ["IMPERSONATION", "FAKE_SELLER", "ACCOUNT_TAKEOVER", "INVESTMENT_SCAM", "IMPERSONATION", "FAKE_SELLER", "ACCOUNT_TAKEOVER"],
    },
}


def read_demo_config(demo_dir: Path = DEMO_DIR) -> tuple[Path, str]:
    """Verify the exact isolated database path and its local-only config."""
    demo_dir = demo_dir.resolve()
    if demo_dir != DEMO_DIR.resolve():
        raise RuntimeError("Demo expansion is restricted to the repository .local-demo directory")
    if DEMO_DIR.is_symlink() or not DEMO_DIR.is_dir():
        raise RuntimeError("The .local-demo directory is missing or is not a real directory")
    if DB_PATH.is_symlink() or not DB_PATH.is_file():
        raise RuntimeError("Expected existing regular demo SQLite database is missing")
    if ENV_PATH.is_symlink() or not ENV_PATH.is_file():
        raise RuntimeError("Expected existing regular demo.env file is missing")

    values: dict[str, str] = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()

    database_url = f"sqlite:///{DB_PATH.resolve()}"
    if values.get("DATABASE_URL") != database_url:
        raise RuntimeError("demo.env DATABASE_URL does not match the one allowed SQLite demo path")
    if not values.get("JWT_SECRET_KEY"):
        raise RuntimeError("demo.env is missing JWT_SECRET_KEY")
    os.chmod(DEMO_DIR, 0o700)
    os.chmod(ENV_PATH, 0o600)
    os.chmod(DB_PATH, 0o600)
    with DB_PATH.open("rb") as source:
        if source.read(16) != b"SQLite format 3\x00":
            raise RuntimeError("Configured demo database is not SQLite")
    return DB_PATH.resolve(), database_url


def _validate_connection(connection: Any, expected_path: Path) -> None:
    if connection.dialect.name != "sqlite":
        raise RuntimeError("Refusing non-SQLite demo database")
    database_list = connection.exec_driver_sql("PRAGMA database_list").fetchall()
    main_path = next((Path(row[2]).resolve() for row in database_list if row[1] == "main"), None)
    if main_path != expected_path.resolve():
        raise RuntimeError("Connected SQLite file does not match the validated demo database")


def expand_demo_dataset(engine: Any, expected_path: Path = DB_PATH) -> dict[str, int]:
    """Add missing deterministic demo rows, retaining all existing records."""
    from passlib.context import CryptContext
    from sqlalchemy.orm import Session

    from backend.models import AccountRelationship, Alert, FraudReport, PaymentAccount, RiskAssessment, ScamCase, User
    from backend.models.base import Base
    from backend.services.alert_service import create_alert
    from backend.services.fraud_intelligence import get_recipient_intelligence
    from backend.services.risk_engine import calculate_risk

    counts = {"accounts_added": 0, "reports_added": 0, "cases_added": 0, "assessments_added": 0, "alerts_added": 0}
    password_hash = CryptContext(schemes=["bcrypt"], deprecated="auto").hash
    now = datetime.utcnow()

    with engine.connect() as connection:
        _validate_connection(connection, expected_path)
        tables = set(connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'").scalars())
        required_tables = set(Base.metadata.tables)
        if not required_tables.issubset(tables):
            raise RuntimeError(f"Demo schema is incomplete; missing tables: {', '.join(sorted(required_tables - tables))}")

    with Session(engine, autoflush=False, expire_on_commit=False) as db:
        base_user = db.query(User).filter(User.phone == BASE_RECIPIENT).one_or_none()
        analyst = db.query(User).filter(User.phone == ANALYST_PHONE).one_or_none()
        if base_user is None or analyst is None or analyst.role not in {"ANALYST", "ADMIN"}:
            raise RuntimeError("Not the initialized demo DB: base recipient or analyst is missing")
        if db.query(PaymentAccount).filter(PaymentAccount.user_id == base_user.id).first() is None:
            raise RuntimeError("Base synthetic recipient has no payment account")

        reporters = [db.query(User).filter(User.phone == phone).one_or_none() for phone in ("0900000001", "0900000002", "0900000003")]
        if any(reporter is None or reporter.role != "USER" for reporter in reporters):
            raise RuntimeError("Initialized synthetic reporter users are missing")

        users: dict[str, Any] = {}
        accounts: dict[str, Any] = {}
        for index in range(1, 11):
            phone = f"09123456{index:02d}"
            name = f"Synthetic Demo Recipient {index:02d}"
            user = db.query(User).filter(User.phone == phone).one_or_none()
            if user is None:
                user = User(phone=phone, name=name, password_hash=password_hash(secrets.token_urlsafe(24)), role="USER")
                db.add(user)
                db.flush()
            elif user.name != name or user.role != "USER":
                raise RuntimeError(f"Demo recipient identity conflicts for {phone}")
            users[phone] = user

            account_number = f"DEMO-EXP-{index:04d}"
            account = db.query(PaymentAccount).filter(PaymentAccount.account_number == account_number).one_or_none()
            if account is None:
                account = PaymentAccount(user_id=user.id, account_number=account_number, provider="SYNTHETIC DEMO WALLET")
                db.add(account)
                db.flush()
                counts["accounts_added"] += 1
            elif account.user_id != user.id or account.provider != "SYNTHETIC DEMO WALLET":
                raise RuntimeError(f"Demo payment account conflicts for {account_number}")
            accounts[phone] = account

        reporter_pool = reporters + [user for phone, user in users.items() if phone not in SCENARIOS]
        for phone, scenario in SCENARIOS.items():
            recipient = users[phone]
            candidates = [user for user in reporter_pool if user.id != recipient.id]
            if len(candidates) < len(scenario["reports"]):
                raise RuntimeError(f"Not enough distinct synthetic reporters for {phone}")
            for index, (reporter, scam_type) in enumerate(zip(candidates, scenario["reports"], strict=False), start=1):
                marker = f"{REPORT_MARKER} {phone}-{index:02d}"
                report = db.query(FraudReport).filter(FraudReport.description.startswith(marker)).one_or_none()
                description = f"{marker}: illustrative {scam_type.lower()} scenario; no real person, payment, or incident is represented."
                if report is None:
                    db.add(FraudReport(
                        reporter_id=reporter.id,
                        recipient_phone=phone,
                        scam_type=scam_type,
                        description=description,
                        status="PENDING",
                        created_at=now - timedelta(days=(index - 1) % 14),
                    ))
                    counts["reports_added"] += 1
                elif report.reporter_id != reporter.id or report.recipient_phone != phone or report.scam_type != scam_type:
                    raise RuntimeError(f"Synthetic report marker conflicts: {marker}")

        db.flush()
        cases_by_phone: dict[str, list[Any]] = {phone: [] for phone in SCENARIOS}
        for phone, scenario in SCENARIOS.items():
            for index in range(1, scenario["case_count"] + 1):
                marker = f"{CASE_MARKER} {phone}-{index:02d}"
                title = f"{marker} — {scenario['reports'][0].replace('_', ' ').title()} review"
                case = db.query(ScamCase).filter(ScamCase.title == title).one_or_none()
                if case is None:
                    case = ScamCase(
                        recipient_phone=phone,
                        title=title,
                        description=f"Synthetic-only investigation for scenario {phone}-{index:02d}; illustrative, not real evidence.",
                        scam_type=scenario["reports"][0],
                        status="OPEN" if index == 1 else "INVESTIGATING",
                        analyst_id=analyst.id,
                        created_at=now - timedelta(days=3 + index),
                    )
                    db.add(case)
                    db.flush()
                    counts["cases_added"] += 1
                elif case.recipient_phone != phone or case.analyst_id != analyst.id:
                    raise RuntimeError(f"Synthetic case marker conflicts: {marker}")
                cases_by_phone[phone].append(case)

        for source_phone, target_phone, kind in (
            ("0912345602", "0912345607", "RELATED_ACCOUNT"),
            ("0912345604", "0912345605", "RELATED_ACCOUNT"),
            ("0912345604", "0912345606", "TRANSACTION"),
        ):
            source, target = accounts[source_phone], accounts[target_phone]
            relationship = db.query(AccountRelationship).filter_by(
                source_account_id=source.id,
                target_account_id=target.id,
                relationship_type=kind,
            ).first()
            if relationship is None:
                db.add(AccountRelationship(source_account_id=source.id, target_account_id=target.id, relationship_type=kind))
        db.commit()

        recipients = db.query(User).join(PaymentAccount, PaymentAccount.user_id == User.id).order_by(User.phone).all()
        if not 10 <= len(recipients) <= 15:
            raise RuntimeError(f"Expected 10-15 demo payment accounts; found {len(recipients)}")
        assessments: dict[str, Any] = {}
        for recipient in recipients:
            intelligence = get_recipient_intelligence(db, recipient.phone)
            amount = SCENARIOS.get(recipient.phone, {}).get("amount", 1000)
            result = calculate_risk(
                report_count=intelligence["total_reports"],
                recent_report_count=intelligence["recent_reports"],
                related_case_count=intelligence["previous_scam_cases"],
                suspicious_connection_count=intelligence["suspicious_relationships"],
                independent_report_count=intelligence["independent_reporters"],
                repeated_scam_pattern=intelligence["repeated_scam_pattern"],
                unusual_transaction=amount >= 5000,
                transaction_amount=float(amount),
            )
            assessment = db.query(RiskAssessment).filter(RiskAssessment.recipient_phone == recipient.phone).order_by(RiskAssessment.id.desc()).first()
            if assessment is None:
                assessment = RiskAssessment(recipient_phone=recipient.phone, score=result["score"], level=result["level"], recommendation=result["recommendation"])
                db.add(assessment)
                db.commit()
                db.refresh(assessment)
                counts["assessments_added"] += 1
            assessments[recipient.phone] = assessment
            if assessment.level in {"HIGH", "CRITICAL"}:
                prior = db.query(Alert).filter(Alert.risk_assessment_id == assessment.id).first()
                if prior is None:
                    create_alert(
                        db,
                        recipient_phone=recipient.phone,
                        severity=assessment.level,
                        message="High-risk recipient requires analyst review.",
                        risk_assessment_id=assessment.id,
                    )
                    counts["alerts_added"] += 1

        for phone, cases in cases_by_phone.items():
            alert = db.query(Alert).filter(Alert.risk_assessment_id == assessments[phone].id).first()
            if alert is not None:
                for case in cases:
                    if case.alert_id is None:
                        case.alert_id = alert.id
        db.commit()

        final = {
            "payment_accounts": db.query(PaymentAccount).count(),
            "reports": db.query(FraudReport).count(),
            "cases": db.query(ScamCase).count(),
            "assessments": db.query(RiskAssessment).count(),
            "alerts": db.query(Alert).count(),
        }

    if not 10 <= final["payment_accounts"] <= 15:
        raise RuntimeError("Final payment-account count is outside the requested range")
    if not 20 <= final["reports"] <= 30:
        raise RuntimeError("Final report count is outside the requested range")
    if not 5 <= final["cases"] <= 8:
        raise RuntimeError("Final case count is outside the requested range")
    return {**counts, **final}


def main() -> int:
    try:
        expected_path, database_url = read_demo_config()
        from sqlalchemy import create_engine

        engine = create_engine(database_url, connect_args={"check_same_thread": False})
        try:
            counts = expand_demo_dataset(engine, expected_path)
        finally:
            engine.dispose()
    except Exception as exc:
        print(f"Local demo expansion failed safely: {exc}", file=sys.stderr)
        return 1

    print("Expanded the isolated local demo database (synthetic data only).")
    added_keys = ("accounts_added", "reports_added", "cases_added", "assessments_added", "alerts_added")
    total_keys = ("payment_accounts", "reports", "cases", "assessments", "alerts")
    print("Added this run: " + ", ".join(f"{key}={counts[key]}" for key in added_keys))
    print("Final totals: " + ", ".join(f"{key}={counts[key]}" for key in total_keys))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())