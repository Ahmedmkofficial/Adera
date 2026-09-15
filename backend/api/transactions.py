from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.models.fraud_report import FraudReport
from backend.models.transaction import Transaction
from backend.schemas.transaction import TransactionCreate
from backend.services.risk_engine import calculate_risk

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/simulate")
def simulate_payment(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    report_count = (
        db.query(FraudReport.reporter_id)
        .filter(
            FraudReport.recipient_phone == transaction.recipient_phone
        )
        .distinct()
        .count()
    )

    risk = calculate_risk(
        report_count=report_count,
        recent_report_count=0,
        related_case_count=0,
        suspicious_connection_count=0,
    )

    new_transaction = Transaction(
        sender_id=transaction.sender_id,
        recipient_phone=transaction.recipient_phone,
        amount=transaction.amount,
        status="SIMULATED",
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return {
        "message": "Payment simulation completed",
        "transaction_id": new_transaction.id,
        "status": new_transaction.status,
        "risk_score": risk["score"],
        "risk_level": risk["level"],
        "recommendation": risk["recommendation"],
        "risk_reasons": risk["reasons"],
    }