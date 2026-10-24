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
from backend.services.alert_service import update_alert_status
from backend.services.case_service import create_case, get_case, list_cases, record_decision
from backend.services.fraud_intelligence import get_recipient_intelligence

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("", response_model=list[dict])
def get_cases(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ANALYST", "ADMIN")),
):
    cases = list_cases(db, status=status)
    response = []
    for case in cases:
        alert = db.query(Alert).filter(Alert.id == case.alert_id).first() if case.alert_id else None
        risk_assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.id == alert.risk_assessment_id)
            .first()
            if alert and alert.risk_assessment_id
            else None
        )
        response.append({
            "id": case.id,
            "title": case.title,
            "status": case.status,
            "recipient_phone": case.recipient_phone,
            "alert_id": case.alert_id,
            "score": risk_assessment.score if risk_assessment else None,
            "level": risk_assessment.level if risk_assessment else (alert.severity if alert else None),
            "decision": case.decision,
            "created_at": case.created_at,
            "updated_at": case.created_at,
        })
    return response


@router.post("", response_model=dict)
def create_case_endpoint(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ANALYST", "ADMIN")),
):
    alert_id = payload.get("alert_id")
    title = payload.get("title")
    description = payload.get("description")

    alert = None
    if alert_id is not None:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    if not title or not description:
        if alert is None or not alert.message or not alert.message.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A selected alert with a recorded message is required to create a case without a title and description.",
            )
        title = title or alert.message
        description = description or alert.message

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
    if alert is not None:
        update_alert_status(db, alert, "INVESTIGATING")
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
    intelligence = get_recipient_intelligence(db, case.recipient_phone)
    analyst = db.query(User).filter(User.id == case.analyst_id).first() if case.analyst_id else None
    alert_created_at = alert.created_at if alert else None

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
            "analyst_id": case.analyst_id,
        },
        "alert": {
            "id": alert.id,
            "recipient_phone": alert.recipient_phone,
            "severity": alert.severity,
            "status": alert.status,
            "message": alert.message,
            "created_at": alert.created_at,
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
                "id": txn.id,
                "created_at": txn.created_at,
            }
            for txn in transactions
        ],
        "subject": case.recipient_phone,
        "score": risk_assessment.score if risk_assessment else None,
        "level": risk_assessment.level if risk_assessment else (alert.severity if alert else None),
        "recommendation": risk_assessment.recommendation if risk_assessment else None,
        "status": case.status,
        "decision": case.decision,
        "decided_by": analyst.name if analyst else None,
        "decided_at": None,
        "created_at": case.created_at,
        "updated_at": case.created_at,
        "events": (
            [
                {
                    "time": alert_created_at,
                    "title": "Alert raised",
                    "body": alert.message,
                },
                {
                    "time": case.created_at,
                    "title": "Case opened",
                    "body": "An analyst opened this case from the alert.",
                },
            ]
            if alert
            else [
                {
                    "time": case.created_at,
                    "title": "Case opened",
                    "body": case.title,
                }
            ]
        ),
        "evidence": {
            "reports": intelligence["total_reports"],
            "recent": intelligence["recent_reports"],
            "scam_cases": intelligence["previous_scam_cases"],
            "related_accounts": intelligence["suspicious_relationships"],
        },
        "payment": (
            {
                "amount": float(transactions[0].amount),
                "txn_id": transactions[0].id,
                "created_at": transactions[0].created_at,
            }
            if transactions
            else None
        ),
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
    if case.alert_id is not None:
        alert = db.query(Alert).filter(Alert.id == case.alert_id).first()
        if alert is not None:
            update_alert_status(
                db,
                alert,
                "RESOLVED" if decision in {"FRAUD", "FALSE_POSITIVE"} else "INVESTIGATING",
            )

    return {
        "id": case.id,
        "decision": case.decision,
        "notes": case.decision_notes,
        "status": case.status,
    }
