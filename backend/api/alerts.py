from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.security import get_current_user, require_roles
from backend.database.session import get_db
from backend.models.alert import Alert
from backend.models.risk_assessment import RiskAssessment
from backend.models.user import User
from backend.services.alert_service import get_alert, list_alerts, update_alert_status

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
