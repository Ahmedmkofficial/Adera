from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.security import get_current_user, require_roles
from backend.database.session import get_db
from backend.models.alert import Alert
from backend.models.fraud_report import FraudReport
from backend.models.payment_account import PaymentAccount
from backend.models.relationship import AccountRelationship
from backend.models.risk_assessment import RiskAssessment
from backend.models.scam_case import ScamCase
from backend.models.transaction import Transaction
from backend.models.user import User
from backend.services.alert_service import get_alert, list_alerts, update_alert_status
from backend.services.recipient_graph import build_recipient_graph

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=list[dict])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ANALYST", "ADMIN")),
):
    alerts = list_alerts(db)
    response = []
    for alert in alerts:
        response.append(
            {
                "id": alert.id,
                "severity": alert.severity,
                "status": alert.status,
                "recipient_phone": alert.recipient_phone,
                "risk_score": (
                    db.query(RiskAssessment.score)
                    .filter(RiskAssessment.id == alert.risk_assessment_id)
                    .scalar()
                    if alert.risk_assessment_id is not None
                    else None
                ),
                "risk_level": (
                    db.query(RiskAssessment.level)
                    .filter(RiskAssessment.id == alert.risk_assessment_id)
                    .scalar()
                    if alert.risk_assessment_id is not None
                    else None
                ),
                "message": alert.message,
                "created_at": alert.created_at,
            }
        )
    return response


@router.get("/{alert_id}", response_model=dict)
def get_alert_detail(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ANALYST", "ADMIN")),
):
    alert = get_alert(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    risk_assessment = None
    if alert.risk_assessment_id is not None:
        risk_assessment = (
            db.query(RiskAssessment).filter(RiskAssessment.id == alert.risk_assessment_id).first()
        )

    reports = (
        db.query(FraudReport)
        .filter(FraudReport.recipient_phone == alert.recipient_phone)
        .order_by(FraudReport.created_at.desc())
        .all()
    )
    transactions = (
        db.query(Transaction)
        .filter(Transaction.recipient_phone == alert.recipient_phone)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )
    sender_ids = {transaction.sender_id for transaction in transactions}
    senders = (
        {
            user.id: user.phone
            for user in db.query(User).filter(User.id.in_(sender_ids)).all()
        }
        if sender_ids
        else {}
    )
    recipient = db.query(User).filter(User.phone == alert.recipient_phone).first()
    graph = build_recipient_graph(db, recipient) if recipient else None
    related_accounts = []
    if graph:
        account_nodes = {
            node["id"]: node for node in graph["nodes"] if node["kind"] == "account"
        }
        related_accounts = [
            {
                "phone": node["phone"],
                "relation": edge["type"],
                "level": node["level"],
            }
            for edge in graph["edges"]
            if edge["type"] != "REPORT"
            for node in [account_nodes.get(edge["target"] if edge["source"].startswith("subject-") else edge["source"])]
            if node is not None
        ]
    case_id = (
        db.query(ScamCase.id)
        .filter(ScamCase.alert_id == alert.id)
        .order_by(ScamCase.id.desc())
        .scalar()
    )

    return {
        "alert": {
            "id": alert.id,
            "recipient_phone": alert.recipient_phone,
            "message": alert.message,
            "severity": alert.severity,
            "status": alert.status,
            "created_at": alert.created_at,
        },
        "risk_assessment": (
            {
                "id": risk_assessment.id,
                "recipient_phone": risk_assessment.recipient_phone,
                "score": risk_assessment.score,
                "level": risk_assessment.level,
                "recommendation": risk_assessment.recommendation,
            }
            if risk_assessment is not None
            else None
        ),
        "reasons": [alert.message] if alert.message else [],
        "transactions": [
            {
                "id": transaction.id,
                "created_at": transaction.created_at,
                "counterparty": senders.get(transaction.sender_id),
                "amount": float(transaction.amount),
            }
            for transaction in transactions
        ],
        "reports_total": len(reports),
        "reports": [
            {
                "id": report.id,
                "created_at": report.created_at,
                "scam_type": report.scam_type,
                "summary": report.description,
            }
            for report in reports[:5]
        ],
        "related_accounts": related_accounts,
        "case_id": case_id,
    }


@router.patch("/{alert_id}", response_model=dict)
def patch_alert(
    alert_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ANALYST", "ADMIN")),
):
    alert = get_alert(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    status_value = payload.get("status")
    if status_value is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status is required")

    try:
        alert = update_alert_status(db, alert, status_value)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"id": alert.id, "status": alert.status, "severity": alert.severity, "recipient_phone": alert.recipient_phone}
