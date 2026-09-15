from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.fraud_report import FraudReport
from backend.schemas.risk import RiskCheckRequest, RiskCheckResponse
from backend.services.risk_engine import calculate_risk

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.post("/check", response_model=RiskCheckResponse)
def check_risk(
    request: RiskCheckRequest,
    db: Session = Depends(get_db),
):
    report_count = (
    db.query(FraudReport.reporter_id)
    .filter(FraudReport.recipient_phone == request.recipient_phone)
    .distinct()
    .count()
    )

    result = calculate_risk(
        report_count=report_count,
        recent_report_count=0,
        related_case_count=0,
        suspicious_connection_count=0,
    )

    return result
