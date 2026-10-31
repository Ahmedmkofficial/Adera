#!/usr/bin/env python3
"""Dedicated, manually invoked, idempotent PostgreSQL demo-seeding utility.

Imports synthetic demo records from the isolated local SQLite demo database
into the PostgreSQL database specified by DATABASE_URL.

Strict Safety Constraints:
- Connects strictly to PostgreSQL (refuses SQLite or unexpected dialects).
- Idempotent: avoids duplicate records when run repeatedly.
- Wraps entire import in a transaction; rolls back on any error.
- Never overwrites existing credentials, roles, usernames, or phone numbers.
- Preserves Ahmed Mk (phone 0984746051) and all existing database records.
- Creates local-demo administrator (username 'admin', password 'admin', role 'ADMIN').
- Does NOT create an extra analyst account. Maps synthetic SQLite analyst ID to the ADMIN ID.
- Lets PostgreSQL generate primary keys (no manual sequence manipulation or forced IDs).
- Preserves all valid foreign-key relationships and source timestamps.
"""

from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from passlib.context import CryptContext
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.models import (
    AccountRelationship,
    Alert,
    FraudReport,
    PaymentAccount,
    RiskAssessment,
    ScamCase,
    User,
)

DEFAULT_SQLITE_PATH = ROOT / ".local-demo" / "adera-demo.sqlite3"
DEMO_ADMIN_USERNAME = "admin"
DEMO_ADMIN_PHONE = "0999000000"
DEMO_ADMIN_NAME = "Demo Administrator"
DEMO_ADMIN_ROLE = "ADMIN"
DEMO_ADMIN_PASSWORD = "admin"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_database_url(url: str | None) -> str:
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in {"postgresql", "postgres"}:
        raise ValueError(
            f"Refusing execution: DATABASE_URL must point to PostgreSQL, but got scheme '{scheme}'"
        )
    return url


def parse_datetime(val: Any) -> datetime | None:
    if val is None or isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val))
    except Exception:
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(str(val), fmt)
            except ValueError:
                pass
    return None


def run_import(
    engine: Any,
    sqlite_path: Path = DEFAULT_SQLITE_PATH,
    dry_run: bool = False,
) -> dict[str, int]:
    if not sqlite_path.is_file():
        raise FileNotFoundError(f"Source SQLite demo dataset not found at {sqlite_path}")

    # Read all source records from SQLite
    sqlite_con = sqlite3.connect(str(sqlite_path))
    sqlite_con.row_factory = sqlite3.Row
    sqlite_cur = sqlite_con.cursor()

    src_users = sqlite_cur.execute(
        "SELECT id, phone, username, name, password_hash, role FROM users ORDER BY id"
    ).fetchall()
    src_accounts = sqlite_cur.execute(
        "SELECT id, user_id, account_number, provider FROM payment_accounts ORDER BY id"
    ).fetchall()
    src_reports = sqlite_cur.execute(
        "SELECT id, reporter_id, recipient_phone, scam_type, description, status, created_at FROM fraud_reports ORDER BY id"
    ).fetchall()
    src_assessments = sqlite_cur.execute(
        "SELECT id, recipient_phone, score, level, recommendation FROM risk_assessments ORDER BY id"
    ).fetchall()
    src_alerts = sqlite_cur.execute(
        "SELECT id, recipient_phone, message, severity, status, risk_assessment_id, created_at FROM alerts ORDER BY id"
    ).fetchall()
    src_cases = sqlite_cur.execute(
        "SELECT id, recipient_phone, title, description, scam_type, status, alert_id, analyst_id, decision, decision_notes, created_at FROM scam_cases ORDER BY id"
    ).fetchall()
    src_relationships = sqlite_cur.execute(
        "SELECT id, source_account_id, target_account_id, relationship_type, created_at FROM account_relationships ORDER BY id"
    ).fetchall()
    sqlite_con.close()

    counts = {
        "admin_created": 0,
        "users_imported": 0,
        "accounts_imported": 0,
        "reports_imported": 0,
        "assessments_imported": 0,
        "alerts_imported": 0,
        "cases_imported": 0,
        "relationships_imported": 0,
    }

    # Execute entire import in a single transaction
    with Session(engine, autoflush=False, expire_on_commit=False) as db:
        with db.begin():
            # 1. Check existing users in PostgreSQL
            existing_users = db.query(User).all()
            user_by_phone = {u.phone: u for u in existing_users}
            user_by_username = {u.username.lower(): u for u in existing_users if u.username}

            # Verify Ahmed Mk account safety
            ahmed_user = user_by_phone.get("0984746051")
            if ahmed_user:
                if ahmed_user.name != "Ahmed Mk" or ahmed_user.role != "USER":
                    raise RuntimeError("Collision or unexpected state for existing user Ahmed Mk")

            # 2. Local-Demo ADMIN account setup
            admin_user = user_by_username.get(DEMO_ADMIN_USERNAME.lower())
            if admin_user is None:
                # Check if DEMO_ADMIN_PHONE is taken by someone else
                if DEMO_ADMIN_PHONE in user_by_phone:
                    raise RuntimeError(
                        f"Admin phone {DEMO_ADMIN_PHONE} is already assigned to {user_by_phone[DEMO_ADMIN_PHONE].name}"
                    )
                admin_user = User(
                    username=DEMO_ADMIN_USERNAME,
                    phone=DEMO_ADMIN_PHONE,
                    name=DEMO_ADMIN_NAME,
                    password_hash=pwd_context.hash(DEMO_ADMIN_PASSWORD),
                    role=DEMO_ADMIN_ROLE,
                )
                db.add(admin_user)
                db.flush()
                counts["admin_created"] = 1
                user_by_phone[DEMO_ADMIN_PHONE] = admin_user
                user_by_username[DEMO_ADMIN_USERNAME.lower()] = admin_user
            else:
                # Never overwrite admin attributes; verify it is valid demo admin
                if admin_user.role != DEMO_ADMIN_ROLE:
                    raise RuntimeError(
                        f"Existing user '{DEMO_ADMIN_USERNAME}' has conflicting role '{admin_user.role}', expected '{DEMO_ADMIN_ROLE}'"
                    )

            # Map SQLite synthetic analyst (0999000001) directly to our PostgreSQL ADMIN ID!
            # Do NOT create a separate ANALYST account.
            user_id_map: dict[int, int] = {}

            # 3. Import SQLite Users
            for row in src_users:
                src_id = row["id"]
                phone = row["phone"]
                role = row["role"]
                name = row["name"]

                if phone == "0999000001" or role == "ANALYST":
                    # Map synthetic analyst from SQLite directly to PostgreSQL ADMIN
                    user_id_map[src_id] = admin_user.id
                    continue

                existing = user_by_phone.get(phone)
                if existing is not None:
                    # Validate consistency without overwriting
                    if existing.phone == "0984746051" and existing.name == "Ahmed Mk":
                        # Untouched
                        user_id_map[src_id] = existing.id
                        continue
                    if existing.role != role:
                        raise RuntimeError(
                            f"Role conflict for existing user {phone}: {existing.role} vs {role}"
                        )
                    user_id_map[src_id] = existing.id
                else:
                    new_user = User(
                        phone=phone,
                        username=row["username"],
                        name=name,
                        password_hash=row["password_hash"],
                        role=role,
                    )
                    db.add(new_user)
                    db.flush()
                    counts["users_imported"] += 1
                    user_by_phone[phone] = new_user
                    user_id_map[src_id] = new_user.id

            # 4. Import Payment Accounts
            account_id_map: dict[int, int] = {}
            existing_accounts = db.query(PaymentAccount).all()
            account_by_num = {acc.account_number: acc for acc in existing_accounts}

            for row in src_accounts:
                src_id = row["id"]
                acc_num = row["account_number"]
                src_user_id = row["user_id"]

                if src_user_id not in user_id_map:
                    raise RuntimeError(f"Account {acc_num} references unmapped user ID {src_user_id}")
                target_user_id = user_id_map[src_user_id]

                existing = account_by_num.get(acc_num)
                if existing is not None:
                    if existing.user_id != target_user_id:
                        raise RuntimeError(
                            f"Payment account {acc_num} already exists for user {existing.user_id}, not {target_user_id}"
                        )
                    account_id_map[src_id] = existing.id
                else:
                    new_acc = PaymentAccount(
                        user_id=target_user_id,
                        account_number=acc_num,
                        provider=row["provider"],
                    )
                    db.add(new_acc)
                    db.flush()
                    counts["accounts_imported"] += 1
                    account_by_num[acc_num] = new_acc
                    account_id_map[src_id] = new_acc.id

            # 5. Import Fraud Reports
            existing_reports = db.query(FraudReport).all()
            # Match by (reporter_id, recipient_phone, description)
            report_keys = {
                (rep.reporter_id, rep.recipient_phone, rep.description): rep
                for rep in existing_reports
            }

            for row in src_reports:
                src_reporter_id = row["reporter_id"]
                if src_reporter_id not in user_id_map:
                    raise RuntimeError(f"Report references unmapped reporter ID {src_reporter_id}")
                target_reporter_id = user_id_map[src_reporter_id]
                recip_phone = row["recipient_phone"]
                desc = row["description"]

                key = (target_reporter_id, recip_phone, desc)
                if key not in report_keys:
                    new_rep = FraudReport(
                        reporter_id=target_reporter_id,
                        recipient_phone=recip_phone,
                        scam_type=row["scam_type"],
                        description=desc,
                        status=row["status"],
                        created_at=parse_datetime(row["created_at"]),
                    )
                    db.add(new_rep)
                    db.flush()
                    counts["reports_imported"] += 1
                    report_keys[key] = new_rep

            # 6. Import Risk Assessments
            # To strictly identify risk assessments, we match by (recipient_phone, score, level, recommendation)
            # plus ordering correspondence with reports/alerts.
            existing_assessments = db.query(RiskAssessment).all()
            # Map by recipient_phone -> list of existing assessments
            assessments_by_phone: dict[str, list[RiskAssessment]] = {}
            for a in existing_assessments:
                assessments_by_phone.setdefault(a.recipient_phone, []).append(a)

            assessment_id_map: dict[int, int] = {}
            for row in src_assessments:
                src_id = row["id"]
                phone = row["recipient_phone"]
                score = row["score"]
                lvl = row["level"]
                reco = row["recommendation"]

                # Find candidate match among existing assessments for this phone
                candidates = assessments_by_phone.get(phone, [])
                matched = None
                for cand in candidates:
                    if (
                        cand.score == score
                        and cand.level == lvl
                        and cand.recommendation == reco
                        and cand.id not in assessment_id_map.values()
                    ):
                        matched = cand
                        break

                if matched is not None:
                    assessment_id_map[src_id] = matched.id
                else:
                    new_a = RiskAssessment(
                        recipient_phone=phone,
                        score=score,
                        level=lvl,
                        recommendation=reco,
                    )
                    db.add(new_a)
                    db.flush()
                    counts["assessments_imported"] += 1
                    assessments_by_phone.setdefault(phone, []).append(new_a)
                    assessment_id_map[src_id] = new_a.id

            # 7. Import Alerts
            existing_alerts = db.query(Alert).all()
            alerts_by_assessment = {alt.risk_assessment_id: alt for alt in existing_alerts if alt.risk_assessment_id}
            alert_id_map: dict[int, int] = {}

            for row in src_alerts:
                src_id = row["id"]
                src_assessment_id = row["risk_assessment_id"]
                target_assessment_id = (
                    assessment_id_map.get(src_assessment_id) if src_assessment_id else None
                )

                if target_assessment_id and target_assessment_id in alerts_by_assessment:
                    alert_id_map[src_id] = alerts_by_assessment[target_assessment_id].id
                else:
                    new_alt = Alert(
                        recipient_phone=row["recipient_phone"],
                        message=row["message"],
                        severity=row["severity"],
                        status=row["status"],
                        risk_assessment_id=target_assessment_id,
                        created_at=parse_datetime(row["created_at"]),
                    )
                    db.add(new_alt)
                    db.flush()
                    counts["alerts_imported"] += 1
                    if target_assessment_id:
                        alerts_by_assessment[target_assessment_id] = new_alt
                    alert_id_map[src_id] = new_alt.id

            # 8. Import Scam Cases
            existing_cases = db.query(ScamCase).all()
            cases_by_title = {c.title: c for c in existing_cases}

            for row in src_cases:
                title = row["title"]
                src_alert_id = row["alert_id"]
                src_analyst_id = row["analyst_id"]

                target_alert_id = alert_id_map.get(src_alert_id) if src_alert_id else None
                # Map analyst_id to our mapped user (which routes to ADMIN ID)
                target_analyst_id = user_id_map.get(src_analyst_id) if src_analyst_id else None

                existing = cases_by_title.get(title)
                if existing is not None:
                    # Already exists
                    pass
                else:
                    new_case = ScamCase(
                        recipient_phone=row["recipient_phone"],
                        title=title,
                        description=row["description"],
                        scam_type=row["scam_type"],
                        status=row["status"],
                        alert_id=target_alert_id,
                        analyst_id=target_analyst_id,
                        decision=row["decision"],
                        decision_notes=row["decision_notes"],
                        created_at=parse_datetime(row["created_at"]),
                    )
                    db.add(new_case)
                    db.flush()
                    counts["cases_imported"] += 1
                    cases_by_title[title] = new_case

            # 9. Import Account Relationships
            existing_rels = db.query(AccountRelationship).all()
            rel_keys = {
                (r.source_account_id, r.target_account_id, r.relationship_type)
                for r in existing_rels
            }

            for row in src_relationships:
                src_source = row["source_account_id"]
                src_target = row["target_account_id"]
                rel_type = row["relationship_type"]

                if src_source not in account_id_map or src_target not in account_id_map:
                    raise RuntimeError(
                        f"Relationship references unmapped accounts: {src_source} -> {src_target}"
                    )
                target_source = account_id_map[src_source]
                target_target = account_id_map[src_target]

                key = (target_source, target_target, rel_type)
                if key not in rel_keys:
                    new_rel = AccountRelationship(
                        source_account_id=target_source,
                        target_account_id=target_target,
                        relationship_type=rel_type,
                        created_at=parse_datetime(row["created_at"]),
                    )
                    db.add(new_rel)
                    db.flush()
                    counts["relationships_imported"] += 1
                    rel_keys.add(key)

            if dry_run:
                # Rollback transaction in dry-run mode
                db.rollback()

    return counts


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Import synthetic demo data into PostgreSQL.")
    parser.add_argument(
        "--sqlite-path",
        type=Path,
        default=DEFAULT_SQLITE_PATH,
        help="Path to source SQLite demo database",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform all checks and migrations in a transaction then rollback",
    )
    args = parser.parse_args()

    raw_url = os.getenv("DATABASE_URL")
    try:
        validated_url = validate_database_url(raw_url)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Connecting to PostgreSQL database at: {validated_url.split('@')[-1]}")
    engine = create_engine(validated_url)

    try:
        counts = run_import(engine, sqlite_path=args.sqlite_path, dry_run=args.dry_run)
    except Exception as exc:
        print(f"Import failed safely (all operations rolled back): {exc}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    prefix = "[DRY RUN] " if args.dry_run else ""
    print(f"{prefix}Import completed successfully:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
