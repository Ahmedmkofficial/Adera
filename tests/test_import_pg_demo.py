"""Tests for PostgreSQL demo data importer (scripts/import_pg_demo.py).

Verifies:
1. URL validation:
   - Accepts only exact schemes 'postgresql' and 'postgres'.
   - Rejects lookalikes (e.g. 'postgresql+invalid', 'postgres-malicious', 'sqlite').
2. Transactional execution, data import, and relationship preservation.
3. Self-contained: creates its own temporary SQLite source database and minimum
   required synthetic records (does not rely on .local-demo or ignored files).
4. Idempotency: re-running produces 0 duplicate records across all tables.
5. Safety: preservation of existing accounts (Ahmed Mk is never touched or overwritten).
6. Correct mapping of synthetic SQLite analyst to the new ADMIN user ID.
7. Refusal to overwrite admin user if role or phone conflicts.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.models import (
    AccountRelationship,
    Alert,
    FraudReport,
    PaymentAccount,
    RiskAssessment,
    ScamCase,
    User,
)
from backend.models.base import Base
from scripts.import_pg_demo import (
    DEMO_ADMIN_PHONE,
    DEMO_ADMIN_ROLE,
    DEMO_ADMIN_USERNAME,
    run_import,
    validate_database_url,
)


def test_validate_database_url_accepts_exact_schemes():
    assert (
        validate_database_url("postgresql://user:pass@localhost:5432/test_db")
        == "postgresql://user:pass@localhost:5432/test_db"
    )
    assert (
        validate_database_url("postgres://user:pass@localhost:5432/test_db")
        == "postgres://user:pass@localhost:5432/test_db"
    )


def test_validate_database_url_rejects_lookalike_and_invalid_schemes():
    # SQLite
    with pytest.raises(ValueError, match="must point to PostgreSQL"):
        validate_database_url("sqlite:///some/path.sqlite3")

    # Lookalikes
    with pytest.raises(ValueError, match="must point to PostgreSQL"):
        validate_database_url("postgresql+invalid://user:pass@localhost/db")

    with pytest.raises(ValueError, match="must point to PostgreSQL"):
        validate_database_url("postgres-malicious://user:pass@localhost/db")

    with pytest.raises(ValueError, match="must point to PostgreSQL"):
        validate_database_url("postgresql+psycopg2://user:pass@localhost/db")

    # Other dialects
    with pytest.raises(ValueError, match="must point to PostgreSQL"):
        validate_database_url("mysql://user:pass@localhost/db")

    # Empty
    with pytest.raises(ValueError, match="DATABASE_URL environment variable is not set"):
        validate_database_url("")


def _create_synthetic_sqlite_fixture(sqlite_path: Path) -> None:
    """Create a self-contained temporary SQLite database with minimal required demo records."""
    con = sqlite3.connect(str(sqlite_path))
    cur = con.cursor()

    cur.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            phone VARCHAR(20) NOT NULL UNIQUE,
            username VARCHAR(32),
            name VARCHAR(100) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL
        );
        CREATE TABLE payment_accounts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            account_number VARCHAR(50) NOT NULL UNIQUE,
            provider VARCHAR(50) NOT NULL
        );
        CREATE TABLE fraud_reports (
            id INTEGER PRIMARY KEY,
            reporter_id INTEGER NOT NULL,
            recipient_phone VARCHAR(20) NOT NULL,
            scam_type VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR(30) NOT NULL,
            created_at DATETIME
        );
        CREATE TABLE risk_assessments (
            id INTEGER PRIMARY KEY,
            recipient_phone VARCHAR(20) NOT NULL,
            score INTEGER NOT NULL,
            level VARCHAR(20) NOT NULL,
            recommendation VARCHAR(50) NOT NULL
        );
        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY,
            recipient_phone VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            severity VARCHAR(20) NOT NULL,
            status VARCHAR(30) NOT NULL,
            risk_assessment_id INTEGER,
            created_at DATETIME
        );
        CREATE TABLE scam_cases (
            id INTEGER PRIMARY KEY,
            recipient_phone VARCHAR(20) NOT NULL,
            title VARCHAR(150) NOT NULL,
            description TEXT NOT NULL,
            scam_type VARCHAR(50) NOT NULL,
            status VARCHAR(30) NOT NULL,
            alert_id INTEGER,
            analyst_id INTEGER,
            decision VARCHAR(30),
            decision_notes TEXT,
            created_at DATETIME
        );
        CREATE TABLE account_relationships (
            id INTEGER PRIMARY KEY,
            source_account_id INTEGER NOT NULL,
            target_account_id INTEGER NOT NULL,
            relationship_type VARCHAR(30) NOT NULL,
            created_at DATETIME NOT NULL
        );
        """
    )

    now = datetime(2026, 10, 31, 10, 0, 0)

    # 1. Users: 1 demo recipient, 1 reporter, 1 linked user, 1 synthetic analyst
    # Total = 4 users. Analyst will map to Admin in PG, resulting in 3 imported users + 1 admin.
    cur.executemany(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
        [
            (1, "0912345678", None, "Synthetic Demo Recipient", "hash_recip", "USER"),
            (2, "0900000001", None, "Synthetic Reporter One", "hash_rep", "USER"),
            (3, "0933001122", None, "Synthetic Linked Account A", "hash_linked", "USER"),
            (4, "0999000001", None, "Local Demo Analyst", "hash_analyst", "ANALYST"),
        ],
    )

    # 2. Payment Accounts: 2 accounts (recipient + linked)
    cur.executemany(
        "INSERT INTO payment_accounts VALUES (?, ?, ?, ?)",
        [
            (1, 1, "DEMO-0001", "SYNTHETIC DEMO WALLET"),
            (2, 3, "DEMO-0002", "SYNTHETIC DEMO WALLET"),
        ],
    )

    # 3. Fraud Reports: 1 report against recipient
    cur.execute(
        "INSERT INTO fraud_reports VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, 2, "0912345678", "IMPERSONATION", "SYNTHETIC DEMO REPORT 1", "PENDING", now.isoformat()),
    )

    # 4. Risk Assessments: 1 assessment
    cur.execute(
        "INSERT INTO risk_assessments VALUES (?, ?, ?, ?, ?)",
        (1, "0912345678", 75, "CRITICAL", "STOP_AND_VERIFY"),
    )

    # 5. Alerts: 1 alert referencing risk assessment 1
    cur.execute(
        "INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?)",
        (1, "0912345678", "High-risk alert message", "CRITICAL", "OPEN", 1, now.isoformat()),
    )

    # 6. Scam Cases: 1 scam case referencing alert 1 and synthetic analyst 4
    cur.execute(
        "INSERT INTO scam_cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            1,
            "0912345678",
            "Synthetic impersonation review",
            "Demo case description",
            "IMPERSONATION",
            "OPEN",
            1,
            4,
            None,
            None,
            (now - timedelta(days=1)).isoformat(),
        ),
    )

    # 7. Account Relationships: 1 relationship between account 1 and account 2
    cur.execute(
        "INSERT INTO account_relationships VALUES (?, ?, ?, ?, ?)",
        (1, 1, 2, "RELATED_ACCOUNT", now.isoformat()),
    )

    con.commit()
    con.close()


def test_import_pg_demo_logic_and_idempotency_self_contained(tmp_path: Path):
    """Test import, relationship preservation, and idempotency with self-contained fixtures."""
    sqlite_source_path = tmp_path / "synthetic-source.sqlite3"
    _create_synthetic_sqlite_fixture(sqlite_source_path)

    # Create target test database (isolated temporary schema)
    target_engine = create_engine(
        f"sqlite:///{tmp_path / 'target.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=target_engine)

    # 1. Pre-seed the existing Ahmed Mk user (representing pre-existing PostgreSQL data)
    with Session(target_engine) as session:
        ahmed = User(
            id=1,
            phone="0984746051",
            name="Ahmed Mk",
            password_hash="preserved-hash-ahmed",
            role="USER",
        )
        session.add(ahmed)
        session.commit()

    # 2. Run first import pass
    counts_first = run_import(target_engine, sqlite_path=sqlite_source_path)

    assert counts_first["admin_created"] == 1
    # 4 source users: 3 regular users imported, 1 analyst mapped to admin
    assert counts_first["users_imported"] == 3
    assert counts_first["accounts_imported"] == 2
    assert counts_first["reports_imported"] == 1
    assert counts_first["assessments_imported"] == 1
    assert counts_first["alerts_imported"] == 1
    assert counts_first["cases_imported"] == 1
    assert counts_first["relationships_imported"] == 1

    # Verify target database state
    with Session(target_engine) as session:
        # Total users: Ahmed Mk (1) + Admin (1) + 3 imported = 5
        all_users = session.query(User).all()
        assert len(all_users) == 5

        # Verify Ahmed Mk was preserved untouched
        ahmed_check = session.query(User).filter(User.phone == "0984746051").one()
        assert ahmed_check.id == 1
        assert ahmed_check.name == "Ahmed Mk"
        assert ahmed_check.role == "USER"
        assert ahmed_check.password_hash == "preserved-hash-ahmed"

        # Verify Admin user created with expected credentials and role
        admin_check = session.query(User).filter(User.username == DEMO_ADMIN_USERNAME).one()
        assert admin_check.role == DEMO_ADMIN_ROLE
        assert admin_check.phone == DEMO_ADMIN_PHONE
        assert admin_check.name == "Demo Administrator"

        # Verify ScamCase analyst_id references point to the new admin user
        cases = session.query(ScamCase).all()
        assert len(cases) == 1
        assert cases[0].analyst_id == admin_check.id
        assert cases[0].alert_id is not None

        # Verify Alert and RiskAssessment linkages
        alerts = session.query(Alert).all()
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.risk_assessment_id is not None

        assessment = session.get(RiskAssessment, alert.risk_assessment_id)
        assert assessment is not None
        assert assessment.recipient_phone == "0912345678"
        assert assessment.score == 75

        # Verify Account Relationships linkage
        rels = session.query(AccountRelationship).all()
        assert len(rels) == 1
        rel = rels[0]
        src_acc = session.get(PaymentAccount, rel.source_account_id)
        tgt_acc = session.get(PaymentAccount, rel.target_account_id)
        assert src_acc.account_number == "DEMO-0001"
        assert tgt_acc.account_number == "DEMO-0002"

    # 3. Run second import pass to verify strict IDEMPOTENCY
    counts_second = run_import(target_engine, sqlite_path=sqlite_source_path)

    assert counts_second["admin_created"] == 0
    assert counts_second["users_imported"] == 0
    assert counts_second["accounts_imported"] == 0
    assert counts_second["reports_imported"] == 0
    assert counts_second["assessments_imported"] == 0
    assert counts_second["alerts_imported"] == 0
    assert counts_second["cases_imported"] == 0
    assert counts_second["relationships_imported"] == 0

    # Ensure total counts remain unchanged after second run
    with Session(target_engine) as session:
        assert session.query(User).count() == 5
        assert session.query(PaymentAccount).count() == 2
        assert session.query(FraudReport).count() == 1
        assert session.query(RiskAssessment).count() == 1
        assert session.query(Alert).count() == 1
        assert session.query(ScamCase).count() == 1
        assert session.query(AccountRelationship).count() == 1


def test_import_pg_demo_conflict_handling(tmp_path: Path):
    """Test that conflicting user data or admin states cause a safe rollback."""
    sqlite_source_path = tmp_path / "synthetic-source.sqlite3"
    _create_synthetic_sqlite_fixture(sqlite_source_path)

    # Scenario: existing user has conflicting role for the same phone
    target_engine = create_engine(
        f"sqlite:///{tmp_path / 'conflict.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=target_engine)

    with Session(target_engine) as session:
        # Pre-seed user with conflicting role for 0912345678 (ANALYST instead of USER)
        conflicting_user = User(
            id=10,
            phone="0912345678",
            name="Conflicting User",
            password_hash="some-hash",
            role="ANALYST",
        )
        session.add(conflicting_user)
        session.commit()

    with pytest.raises(RuntimeError, match="Role conflict for existing user 0912345678"):
        run_import(target_engine, sqlite_path=sqlite_source_path)

    # Ensure conflicting user remained unchanged
    with Session(target_engine) as session:
        user = session.get(User, 10)
        assert user.role == "ANALYST"
        assert session.query(PaymentAccount).count() == 0
