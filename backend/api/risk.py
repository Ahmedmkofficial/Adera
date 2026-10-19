from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.security import get_current_user
from backend.database.session import get_db
from backend.models.payment_account import PaymentAccount
from backend.models.risk_assessment import RiskAssessment
from backend.models.user import User
from backend.schemas.risk import RiskCheckRequest, RiskCheckResponse
from backend.services.alert_service import create_alert
from backend.services.fraud_intelligence import get_recipient_intelligence
from backend.services.risk_engine import calculate_risk

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.post("/check", response_model=RiskCheckResponse)
def check_risk(
    request: RiskCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recipient_user = db.query(User).filter(User.phone == request.recipient_phone).first()
    if recipient_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found",
        )

    account = (
        db.query(PaymentAccount)
        .filter(PaymentAccount.user_id == recipient_user.id)
        .first()
    )
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient account not found",
        )

    intelligence = get_recipient_intelligence(db, request.recipient_phone)

    result = calculate_risk(
        report_count=intelligence["total_reports"],
        recent_report_count=intelligence["recent_reports"],
        related_case_count=intelligence["previous_scam_cases"],
        suspicious_connection_count=intelligence["suspicious_relationships"],
        independent_report_count=intelligence["independent_reporters"],
        repeated_scam_pattern=intelligence["repeated_scam_pattern"],
        unusual_transaction=(request.amount >= 5000),
        transaction_amount=float(request.amount),
    )

    assessment = RiskAssessment(
        recipient_phone=request.recipient_phone,
        score=result["score"],
        level=result["level"],
        recommendation=result["recommendation"],
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    if result["level"] in {"HIGH", "CRITICAL"}:
        create_alert(
            db,
            recipient_phone=request.recipient_phone,
            severity=result["level"],
            message="High-risk recipient requires analyst review.",
            risk_assessment_id=assessment.id,
        )

    return {
        "score": result["score"],
        "level": result["level"],
        "recommendation": result["recommendation"],
        "reasons": result["reasons"],
    }
