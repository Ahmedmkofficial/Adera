from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.models.fraud_report import FraudReport
from backend.models.payment_account import PaymentAccount
from backend.models.relationship import AccountRelationship
from backend.models.scam_case import ScamCase
from backend.models.user import User


def get_recipient_intelligence(db: Session, recipient_phone: str):
    recent_cutoff = datetime.utcnow() - timedelta(days=30)

    reports = (
        db.query(FraudReport)
        .filter(FraudReport.recipient_phone == recipient_phone)
        .order_by(FraudReport.created_at.desc())
        .all()
    )

    total_reports = len(reports)
    recent_reports = sum(
        1 for report in reports if report.created_at and report.created_at >= recent_cutoff
    )

    independent_reporters = (
        db.query(FraudReport.reporter_id)
        .filter(FraudReport.recipient_phone == recipient_phone)
        .distinct()
        .count()
    )

    previous_scam_cases = 0
    scam_case_columns = getattr(ScamCase, "recipient_phone", None)
    if scam_case_columns is not None:
        previous_scam_cases = (
            db.query(ScamCase)
            .filter(ScamCase.recipient_phone == recipient_phone)
            .count()
        )
    else:
        previous_scam_cases = db.query(ScamCase).count()

    recipient_account = (
        db.query(PaymentAccount)
        .join(User, User.id == PaymentAccount.user_id)
        .filter(User.phone == recipient_phone)
        .first()
    )

    suspicious_relationships = 0
    if recipient_account is not None:
        suspicious_relationships = (
            db.query(AccountRelationship)
            .filter(
                AccountRelationship.relationship_type.in_(
                    [
                        "SHARED_PHONE",
                        "SHARED_DEVICE",
                        "TRANSACTION",
                        "RELATED_ACCOUNT",
                    ]
                ),
                or_(
                    AccountRelationship.source_account_id == recipient_account.id,
                    AccountRelationship.target_account_id == recipient_account.id,
                ),
            )
            .count()
        )

    scam_types = [report.scam_type for report in reports if report.scam_type]
    repeated_scam_pattern = len(set(scam_types)) > 1 and total_reports >= 2

    return {
        "total_reports": total_reports,
        "recent_reports": recent_reports,
        "independent_reporters": independent_reporters,
        "previous_scam_cases": previous_scam_cases,
        "suspicious_relationships": suspicious_relationships,
        "repeated_scam_pattern": repeated_scam_pattern,
    }
