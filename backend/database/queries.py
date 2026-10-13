"""Read-only query functions for Adera's data layer.

Member 4 (FastAPI) and the risk engine call these instead of writing SQL.
Every function takes an open SQLAlchemy session (from get_db) as `db`.

Most functions are keyed by the recipient's PHONE NUMBER, because that is how
fraud_reports, risk_assessments, alerts and transactions already identify a
recipient in this project. get_account_profile() accepts either a phone number
or an account number.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import distinct, func, or_, select
from sqlalchemy.orm import Session

from backend.models import (
    AccountRelationship,
    Alert,
    FraudReport,
    PaymentAccount,
    RiskAssessment,
    ScamCase,
    Transaction,
    scam_case_accounts,
    scam_case_reports,
)


def _utc_now() -> datetime:
    # the project stores naive UTC datetimes (datetime.utcnow), so match that
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --- accounts ---------------------------------------------------------------

def get_accounts(db: Session, identifier: str) -> list[PaymentAccount]:
    """Accounts matching a phone number OR an account number."""
    return list(
        db.scalars(
            select(PaymentAccount).where(
                or_(
                    PaymentAccount.phone_number == identifier,
                    PaymentAccount.account_number == identifier,
                )
            )
        )
    )


# --- reports ----------------------------------------------------------------

def count_reports(db: Session, phone: str) -> int:
    """How many fraud reports does this recipient have?"""
    return db.scalar(
        select(func.count()).select_from(FraudReport)
        .where(FraudReport.recipient_phone == phone)
    ) or 0


def count_recent_reports(db: Session, phone: str, days: int = 7) -> int:
    """How many reports were submitted in the last `days` days?"""
    cutoff = _utc_now() - timedelta(days=days)
    return db.scalar(
        select(func.count()).select_from(FraudReport)
        .where(FraudReport.recipient_phone == phone, FraudReport.created_at >= cutoff)
    ) or 0


def count_independent_reporters(db: Session, phone: str) -> int:
    """How many DIFFERENT people reported this recipient?"""
    return db.scalar(
        select(func.count(distinct(FraudReport.reporter_id)))
        .where(FraudReport.recipient_phone == phone)
    ) or 0


def get_reports(db: Session, phone: str) -> list[FraudReport]:
    return list(
        db.scalars(
            select(FraudReport)
            .where(FraudReport.recipient_phone == phone)
            .order_by(FraudReport.created_at.desc())
        )
    )


# --- relationships ----------------------------------------------------------

def get_related_accounts(db: Session, account_id: int) -> list[dict]:
    """Accounts connected to this account (in either direction)."""
    edges = db.scalars(
        select(AccountRelationship).where(
            or_(
                AccountRelationship.source_account_id == account_id,
                AccountRelationship.target_account_id == account_id,
            )
        )
    )
    related = []
    for edge in edges:
        other_id = (
            edge.target_account_id
            if edge.source_account_id == account_id
            else edge.source_account_id
        )
        other = db.get(PaymentAccount, other_id)
        related.append({
            "account_id": other.id,
            "account_number": other.account_number,
            "phone_number": other.phone_number,
            "relationship_type": edge.relationship_type,
        })
    return related


# --- transactions -----------------------------------------------------------

def get_transactions(db: Session, phone: str, limit: int = 100) -> list[Transaction]:
    """Payments to this recipient, plus payments sent by the account's owner."""
    owner_ids = [
        a.user_id for a in db.scalars(
            select(PaymentAccount).where(PaymentAccount.phone_number == phone)
        )
    ]
    conditions = [Transaction.recipient_phone == phone]
    if owner_ids:
        conditions.append(Transaction.sender_id.in_(owner_ids))
    return list(
        db.scalars(
            select(Transaction)
            .where(or_(*conditions))
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
        )
    )


# --- scam cases -------------------------------------------------------------

def get_cases_for_phone(db: Session, phone: str) -> list[ScamCase]:
    """Scam cases linked to this recipient, through its accounts or its reports."""
    account_ids = select(PaymentAccount.id).where(PaymentAccount.phone_number == phone)
    report_ids = select(FraudReport.id).where(FraudReport.recipient_phone == phone)
    case_ids = (
        select(scam_case_accounts.c.case_id)
        .where(scam_case_accounts.c.account_id.in_(account_ids))
        .union(
            select(scam_case_reports.c.case_id)
            .where(scam_case_reports.c.report_id.in_(report_ids))
        )
    )
    return list(
        db.scalars(
            select(ScamCase)
            .where(ScamCase.id.in_(case_ids))
            .order_by(ScamCase.created_at.desc())
        )
    )


# --- risk and alerts --------------------------------------------------------

def get_risk_history(db: Session, phone: str) -> list[RiskAssessment]:
    """Every risk assessment for this recipient, oldest first."""
    return list(
        db.scalars(
            select(RiskAssessment)
            .where(RiskAssessment.recipient_phone == phone)
            .order_by(RiskAssessment.created_at.asc(), RiskAssessment.id.asc())
        )
    )


def has_open_alert(db: Session, phone: str) -> bool:
    """Does this recipient currently have an OPEN alert?"""
    return db.scalar(
        select(func.count()).select_from(Alert)
        .where(Alert.recipient_phone == phone, Alert.status == "OPEN")
    ) > 0


# --- everything in one call -------------------------------------------------

def get_account_profile(db: Session, identifier: str) -> dict:
    """'Tell me everything Adera knows about <phone or account number>'.

    Returns plain dicts and numbers so FastAPI can return it as JSON.
    """
    accounts = get_accounts(db, identifier)
    # if the identifier was an account number, use that account's phone
    phone = accounts[0].phone_number if accounts and accounts[0].phone_number else identifier

    related = []
    for acct in accounts:
        related.extend(get_related_accounts(db, acct.id))

    return {
        "identifier": identifier,
        "phone_number": phone,
        "accounts": [
            {"id": a.id, "account_number": a.account_number,
             "provider": a.provider, "phone_number": a.phone_number}
            for a in accounts
        ],
        "report_count": count_reports(db, phone),
        "recent_report_count": count_recent_reports(db, phone),
        "independent_reporter_count": count_independent_reporters(db, phone),
        "reports": [
            {"id": r.id, "scam_type": r.scam_type, "status": r.status,
             "created_at": r.created_at}
            for r in get_reports(db, phone)
        ],
        "scam_cases": [
            {"id": c.id, "title": c.title, "status": c.status, "priority": c.priority}
            for c in get_cases_for_phone(db, phone)
        ],
        "related_accounts": related,
        "transactions": [
            {"id": t.id, "amount": float(t.amount), "status": t.status,
             "timestamp": t.timestamp}
            for t in get_transactions(db, phone)
        ],
        "risk_history": [
            {"score": r.score, "level": r.level, "recommendation": r.recommendation,
             "created_at": r.created_at}
            for r in get_risk_history(db, phone)
        ],
        "has_open_alert": has_open_alert(db, phone),
    }
