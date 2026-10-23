from sqlalchemy.orm import Session

from backend.models.alert import Alert


def create_alert(db: Session, recipient_phone: str, severity: str, message: str, risk_assessment_id: int | None = None):
    existing = (
        db.query(Alert)
        .filter(
            Alert.recipient_phone == recipient_phone,
            Alert.severity == severity,
            Alert.status.in_({"OPEN", "INVESTIGATING"}),
        )
        .first()
    )
    if existing:
        if existing.risk_assessment_id != risk_assessment_id:
            existing.risk_assessment_id = risk_assessment_id
            existing.message = message
            db.commit()
            db.refresh(existing)
        return existing

    alert = Alert(
        recipient_phone=recipient_phone,
        message=message,
        severity=severity,
        status="OPEN",
        risk_assessment_id=risk_assessment_id,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def list_alerts(db: Session):
    return db.query(Alert).order_by(Alert.created_at.desc()).all()


def get_alert(db: Session, alert_id: int):
    return db.query(Alert).filter(Alert.id == alert_id).first()


def update_alert_status(db: Session, alert: Alert, status: str):
    if status not in {"OPEN", "INVESTIGATING", "RESOLVED", "DISMISSED"}:
        raise ValueError("Invalid alert status")
    alert.status = status
    db.commit()
    db.refresh(alert)
    return alert
