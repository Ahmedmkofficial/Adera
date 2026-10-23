"""Safety, idempotency, and integrity tests for local demo expansion."""

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import AccountRelationship, Alert, FraudReport, PaymentAccount, RiskAssessment, ScamCase, User
from backend.models.base import Base
from scripts.expand_local_demo import BASE_RECIPIENT, expand_demo_dataset, read_demo_config


def make_initialized_demo(tmp_path):
    database_path = tmp_path / "adera-demo.sqlite3"
    engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    with factory.begin() as db:
        users = [
            User(phone=BASE_RECIPIENT, name="Synthetic Demo Recipient", password_hash="hash", role="USER"),
            User(phone="0900000001", name="Synthetic Reporter One", password_hash="hash", role="USER"),
            User(phone="0900000002", name="Synthetic Reporter Two", password_hash="hash", role="USER"),
            User(phone="0900000003", name="Synthetic Reporter Three", password_hash="hash", role="USER"),
            User(phone="0933001122", name="Synthetic Linked Account A", password_hash="hash", role="USER"),
            User(phone="0933001123", name="Synthetic Linked Account B", password_hash="hash", role="USER"),
            User(phone="0999000001", name="Local Demo Analyst", password_hash="preserve-this-hash", role="ANALYST"),
        ]
        db.add_all(users)
        db.flush()
        by_phone = {user.phone: user for user in users}
        accounts = {
            phone: PaymentAccount(user_id=by_phone[phone].id, account_number=f"BASE-{index}", provider="SYNTHETIC DEMO WALLET")
            for index, phone in enumerate((BASE_RECIPIENT, "0933001122", "0933001123"), start=1)
        }
        db.add_all(accounts.values())
        db.flush()
        now = datetime.utcnow()
        specs = [
            ("0900000001", "IMPERSONATION"), ("0900000002", "IMPERSONATION"),
            ("0900000003", "FAKE_SELLER"), ("0900000001", "FAKE_SELLER"),
            ("0900000002", "ACCOUNT_TAKEOVER"), ("0900000003", "ACCOUNT_TAKEOVER"),
            ("0900000001", "IMPERSONATION"),
        ]
        for index, (reporter, scam_type) in enumerate(specs):
            db.add(FraudReport(
                reporter_id=by_phone[reporter].id,
                recipient_phone=BASE_RECIPIENT,
                scam_type=scam_type,
                description=f"SYNTHETIC LOCAL DEMO report {index + 1}: safe fixture.",
                status="PENDING",
                created_at=now - timedelta(days=index),
            ))
        db.add_all([
            ScamCase(recipient_phone=BASE_RECIPIENT, title="Synthetic base case one", description="Synthetic fixture", scam_type="IMPERSONATION", status="OPEN"),
            ScamCase(recipient_phone=BASE_RECIPIENT, title="Synthetic base case two", description="Synthetic fixture", scam_type="FAKE_SELLER", status="INVESTIGATING"),
        ])
        db.add_all([
            AccountRelationship(source_account_id=accounts[BASE_RECIPIENT].id, target_account_id=accounts["0933001122"].id, relationship_type="RELATED_ACCOUNT"),
            AccountRelationship(source_account_id=accounts[BASE_RECIPIENT].id, target_account_id=accounts["0933001123"].id, relationship_type="TRANSACTION"),
        ])
    return engine, factory


def test_expansion_is_idempotent_and_preserves_base_rows(tmp_path):
    engine, factory = make_initialized_demo(tmp_path)
    try:
        with factory() as db:
            analyst = db.query(User).filter(User.phone == "0999000001").one()
            analyst_id, analyst_hash = analyst.id, analyst.password_hash
            original_report_ids = {row.id for row in db.query(FraudReport).all()}
        first = expand_demo_dataset(engine, expected_path=tmp_path / "adera-demo.sqlite3")
        with factory() as db:
            first_ids = {
                "accounts": db.query(PaymentAccount).count(),
                "reports": db.query(FraudReport).count(),
                "cases": db.query(ScamCase).count(),
                "assessments": db.query(RiskAssessment).count(),
                "alerts": db.query(Alert).count(),
            }
            assert original_report_ids.issubset({row.id for row in db.query(FraudReport).all()})
            analyst = db.query(User).filter(User.phone == "0999000001").one()
            assert (analyst.id, analyst.password_hash, analyst.role) == (analyst_id, analyst_hash, "ANALYST")

        second = expand_demo_dataset(engine, expected_path=tmp_path / "adera-demo.sqlite3")
        with factory() as db:
            second_ids = {
                "accounts": db.query(PaymentAccount).count(),
                "reports": db.query(FraudReport).count(),
                "cases": db.query(ScamCase).count(),
                "assessments": db.query(RiskAssessment).count(),
                "alerts": db.query(Alert).count(),
            }
            assert second_ids == first_ids
            assert db.query(RiskAssessment.level).distinct().count() == 4
            assert {row.level for row in db.query(RiskAssessment).all()} == {"LOW", "MODERATE", "HIGH", "CRITICAL"}
            for report in db.query(FraudReport).all():
                assert db.query(User.id).filter(User.id == report.reporter_id).one_or_none() is not None
                assert db.query(User.id).filter(User.phone == report.recipient_phone).one_or_none() is not None
            for case in db.query(ScamCase).all():
                assert db.query(User.id).filter(User.phone == case.recipient_phone).one_or_none() is not None
                if case.alert_id is not None:
                    assert db.query(Alert.id).filter(Alert.id == case.alert_id).one_or_none() is not None
            for alert in db.query(Alert).all():
                assessment = db.query(RiskAssessment).filter(RiskAssessment.id == alert.risk_assessment_id).one()
                assert alert.recipient_phone == assessment.recipient_phone
        assert first["payment_accounts"] == 13
        assert first["reports"] == 24
        assert first["cases"] == 7
        assert first["assessments"] == 13
        assert first["alerts"] == 3
        assert second["accounts_added"] == 0
        assert second["reports_added"] == 0
        assert second["cases_added"] == 0
        assert second["assessments_added"] == 0
        assert second["alerts_added"] == 0
    finally:
        engine.dispose()


def test_demo_config_rejects_any_non_repository_directory(tmp_path):
    try:
        read_demo_config(tmp_path)
    except RuntimeError as error:
        assert "restricted" in str(error)
    else:
        raise AssertionError("non-demo directory must be rejected")
