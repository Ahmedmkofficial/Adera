from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.fraud_report import FraudReport
from backend.schemas.fraud_report import FraudReportCreate

router = APIRouter(prefix="/reports", tags=["Fraud Reports"])


@router.post("")
def create_report(
    report: FraudReportCreate,
    db: Session = Depends(get_db),
):
    new_report = FraudReport(
        reporter_id=report.reporter_id,
        recipient_phone=report.recipient_phone,
        description=report.description,
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return {
        "message": "Fraud report submitted",
        "report_id": new_report.id,
    }