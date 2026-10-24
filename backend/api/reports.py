from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.security import get_current_user
from backend.database.session import get_db
from backend.models.fraud_report import FraudReport
from backend.models.user import User
from backend.schemas.fraud_report import FraudReportCreate, FraudReportRead

router = APIRouter(prefix="/reports", tags=["Fraud Reports"])


@router.post("", response_model=FraudReportRead)
def create_report(
    report: FraudReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_report = FraudReport(
        reporter_id=current_user.id,
        recipient_phone=report.recipient_phone,
        scam_type=report.scam_type,
        description=report.description,
        status="PENDING",
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return new_report


@router.get("", response_model=list[FraudReportRead])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role in {"ANALYST", "ADMIN"}:
        reports = db.query(FraudReport).order_by(FraudReport.created_at.desc()).all()
    else:
        reports = (
            db.query(FraudReport)
            .filter(FraudReport.reporter_id == current_user.id)
            .order_by(FraudReport.created_at.desc())
            .all()
        )

    return reports