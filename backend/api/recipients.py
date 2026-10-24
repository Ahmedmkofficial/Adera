from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.security import require_roles
from backend.database.session import get_db
from backend.models.user import User
from backend.schemas.recipient_graph import RecipientGraph
from backend.schemas.recipient import RecipientSummary
from backend.services.fraud_intelligence import get_recipient_intelligence
from backend.services.recipient_graph import build_recipient_graph
from backend.services.risk_engine import calculate_risk

router = APIRouter(prefix="/recipients", tags=["Recipients"])


@router.get("/{phone}/graph", response_model=RecipientGraph)
def get_recipient_graph(
    phone: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ANALYST", "ADMIN")),
):
    recipient = db.query(User).filter(User.phone == phone).first()
    if recipient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found",
        )
    return build_recipient_graph(db, recipient)


@router.get("/{phone}", response_model=RecipientSummary)
def get_recipient_summary(
    phone: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ANALYST", "ADMIN")),
):
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient phone is required",
        )

    user = db.query(User).filter(User.phone == phone).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found",
        )

    intelligence = get_recipient_intelligence(db, phone)

    risk_result = calculate_risk(
        report_count=intelligence["total_reports"],
        recent_report_count=intelligence["recent_reports"],
        related_case_count=intelligence["previous_scam_cases"],
        suspicious_connection_count=intelligence["suspicious_relationships"],
        independent_report_count=intelligence["independent_reporters"],
        repeated_scam_pattern=intelligence["repeated_scam_pattern"],
        unusual_transaction=False,
        transaction_amount=0,
    )

    return {
        "phone": phone,
        "risk_score": risk_result["score"],
        "risk_level": risk_result["level"],
        "fraud_report_count": intelligence["total_reports"],
        "independent_reporter_count": intelligence["independent_reporters"],
        "recent_report_count": intelligence["recent_reports"],
        "previous_scam_case_count": intelligence["previous_scam_cases"],
        "suspicious_relationship_count": intelligence["suspicious_relationships"],
    }
