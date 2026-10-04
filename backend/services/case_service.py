from sqlalchemy.orm import Session

from backend.models.scam_case import ScamCase


def list_cases(db: Session, status: str | None = None):
    query = db.query(ScamCase)
    if status:
        query = query.filter(ScamCase.status == status)
    return query.order_by(ScamCase.created_at.desc()).all()


def get_case(db: Session, case_id: int):
    return db.query(ScamCase).filter(ScamCase.id == case_id).first()


def create_case(
    db: Session,
    *,
    title: str,
    description: str,
    recipient_phone: str,
    alert_id: int | None = None,
    analyst_id: int | None = None,
):
    case = ScamCase(
        title=title,
        description=description,
        recipient_phone=recipient_phone,
        scam_type="INVESTIGATION",
        status="OPEN",
        alert_id=alert_id,
        analyst_id=analyst_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def update_case_status(db: Session, case: ScamCase, status: str):
    if status not in {"OPEN", "INVESTIGATING", "RESOLVED", "CLOSED"}:
        raise ValueError("Invalid case status")
    case.status = status
    db.commit()
    db.refresh(case)
    return case


def record_decision(db: Session, case: ScamCase, decision: str, notes: str | None = None):
    if decision not in {"FRAUD", "FALSE_POSITIVE", "NEEDS_MORE_INFORMATION"}:
        raise ValueError("Invalid case decision")
    case.decision = decision
    case.decision_notes = notes
    case.status = "RESOLVED" if decision in {"FRAUD", "FALSE_POSITIVE"} else "INVESTIGATING"
    db.commit()
    db.refresh(case)
    return case
