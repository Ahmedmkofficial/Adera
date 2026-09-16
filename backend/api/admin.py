from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.models.alert import Alert
from backend.services.risk_engine import calculate_risk


from backend.database.session import get_db
from backend.models.fraud_report import FraudReport

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/reports")
def get_fraud_reports(
    db: Session = Depends(get_db),
):
    reports = (
        db.query(FraudReport)
        .order_by(FraudReport.created_at.desc())
        .all()
    )
from backend.services.risk_engine import calculate_risk


@router.get("/high-risk")
def get_high_risk_recipients(
    db: Session = Depends(get_db),
):
    recipients = (
        db.query(FraudReport.recipient_phone)
        .distinct()
        .all()
    )

    results = []

    for (phone,) in recipients:
        report_count = (
            db.query(FraudReport.reporter_id)
            .filter(FraudReport.recipient_phone == phone)
            .distinct()
            .count()
        )

        risk = calculate_risk(
            report_count=report_count,
            recent_report_count=0,
            related_case_count=0,
            suspicious_connection_count=0,
        )

        if risk["score"] >= 50:
            results.append({
                "recipient_phone": phone,
                "score": risk["score"],
                "level": risk["level"],
                "recommendation": risk["recommendation"],
                "reasons": risk["reasons"],
            })

    return results

    return [
        {
            "id": report.id,
            "reporter_id": report.reporter_id,
            "recipient_phone": report.recipient_phone,
            "description": report.description,
            "status": report.status,
            "created_at": report.created_at,
        }
        for report in reports
    ]
@router.get("/alerts")
def get_alerts(
    db: Session = Depends(get_db),
):
    alerts = (
        db.query(Alert)
        .order_by(Alert.id.desc())
        .all()
    )

    return [
        {
            "id": alert.id,
            "recipient_phone": alert.recipient_phone,
            "message": alert.message,
            "severity": alert.severity,
            "status": alert.status,
        }
        for alert in alerts
    ]
