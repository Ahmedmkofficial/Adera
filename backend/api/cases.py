from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.security import get_current_user, require_roles
from backend.database.session import get_db
from backend.models.alert import Alert
from backend.models.fraud_report import FraudReport
from backend.models.risk_assessment import RiskAssessment
from backend.models.scam_case import ScamCase
from backend.models.transaction import Transaction
from backend.models.user import User
from backend.services.case_service import create_case, get_case, list_cases, record_decision

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("", response_model=list[dict])
def get_cases(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ANALYST", "ADMIN")),
):
    cases = list_cases(db, status=status)
    return [
        {
            "id": case.id,
            "title": case.title,
            "status": case.status,
            "recipient_phone": case.recipient_phone,
            "created_at": case.created_at,
        }
        for case in cases
    ]


@router.post("", response_model=dict)
def create_case_endpoint(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ANALYST", "ADMIN")),
):
    alert_id = payload.get("alert_id")
    title = payload.get("title")
    description = payload.get("description")
    if not title or not description:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="title and description are required")

    if alert_id is not None:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    recipient_phone = payload.get("recipient_phone")
    if recipient_phone is None and alert_id is not None:
        recipient_phone = db.query(Alert.recipient_phone).filter(Alert.id == alert_id).scalar()
    if recipient_phone is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="recipient_phone is required or alert_id must reference an alert")

    case = create_case(
        db,
        title=title,
        description=description,
        recipient_phone=recipient_phone,
        alert_id=alert_id,
        analyst_id=current_user.id,
    )
    return {
        "id": case.id,
        "title": case.title,
        "status": case.status,
        "recipient_phone": case.recipient_phone,
        "alert_id": case.alert_id,
        "created_at": case.created_at,
    }


@router.get("/{case_id}", response_model=dict)
def get_case_detail(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ANALYST", "ADMIN")),
):
    case = get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    alert = db.query(Alert).filter(Alert.id == case.alert_id).first() if case.alert_id else None
    risk_assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.recipient_phone == case.recipient_phone)
        .order_by(RiskAssessment.id.desc())
        .first()
    )
    reports = (
        db.query(FraudReport)
        .filter(FraudReport.recipient_phone == case.recipient_phone)
        .order_by(FraudReport.created_at.desc())
        .all()
    )
    transactions = (
        db.query(Transaction)
        .filter(Transaction.recipient_phone == case.recipient_phone)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "case": {
            "id": case.id,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "scam_type": case.scam_type,
            "recipient_phone": case.recipient_phone,
            "decision": case.decision,
            "decision_notes": case.decision_notes,
            "created_at": case.created_at,
            "alert_id": case.alert_id,
        },
        "alert": {
            "id": alert.id,
            "recipient_phone": alert.recipient_phone,
            "severity": alert.severity,
            "status": alert.status,
            "message": alert.message,
        } if alert else None,
        "risk_assessment": {
            "id": risk_assessment.id,
            "score": risk_assessment.score,
            "level": risk_assessment.level,
            "recommendation": risk_assessment.recommendation,
        } if risk_assessment else None,
        "fraud_reports": [
            {
                "id": report.id,
                "reporter_id": report.reporter_id,
                "scam_type": report.scam_type,
                "description": report.description,
                "created_at": report.created_at,
            }
            for report in reports
        ],
        "relevant_transactions": [
            {
                "id": txn.id,
                "amount": float(txn.amount),
                "status": txn.status,
                "created_at": txn.created_at,
            }
            for txn in transactions
        ],
    }


@router.post("/{case_id}/decision", response_model=dict)
def record_case_decision(
    case_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ANALYST", "ADMIN")),
):
    case = get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    decision = payload.get("decision")
    if not decision:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="decision is required")

    notes = payload.get("notes")
    try:
        case = record_decision(db, case, decision, notes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "id": case.id,
        "decision": case.decision,
        "notes": case.decision_notes,
        "status": case.status,
    }
