"""
Case & Alert Service Layer
Owner: Tigiste (Member 6) - Backend Co-developer (30%), Integration & Security Lead
Manages the workflow: Risk Engine -> Alert -> Investigation -> Case -> Analyst Decision
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.alert import Alert
from backend.models.scam_case import ScamCase
from backend.models.risk_assessment import RiskAssessment
from backend.schemas.case import CaseCreate, CaseDecisionType
from backend.schemas.alert import AlertStatus, AlertResponse

# In-memory audit storage for decisions and notes to support data retention
# until Reyyan adds 'decision' and 'notes' columns to the 'scam_cases' SQL table.
# TODO (Reyyan): Add 'decision' and 'notes' columns to ScamCase model.
CASE_DECISIONS_STORE: dict[int, dict] = {}


class CaseService:
    @staticmethod
    def get_alerts(
        db: Session,
        status: Optional[str] = None,
    ) -> list[AlertResponse]:
        query = db.query(Alert)
        if status:
            query = query.filter(Alert.status == status)
        alerts = query.order_by(desc(Alert.id)).all()

        results = []
        for alert in alerts:
            latest_assessment = (
                db.query(RiskAssessment)
                .filter(RiskAssessment.recipient_phone == alert.recipient_phone)
                .order_by(desc(RiskAssessment.id))
                .first()
            )
            risk_score = latest_assessment.score if latest_assessment else None

            results.append(
                AlertResponse(
                    id=alert.id,
                    recipient_phone=alert.recipient_phone,
                    message=alert.message,
                    severity=alert.severity,
                    status=alert.status,
                    risk_score=risk_score,
                )
            )
        return results

    @staticmethod
    def get_alert_by_id(db: Session, alert_id: int) -> Optional[AlertResponse]:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None

        latest_assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.recipient_phone == alert.recipient_phone)
            .order_by(desc(RiskAssessment.id))
            .first()
        )
        risk_score = latest_assessment.score if latest_assessment else None

        return AlertResponse(
            id=alert.id,
            recipient_phone=alert.recipient_phone,
            message=alert.message,
            severity=alert.severity,
            status=alert.status,
            risk_score=risk_score,
        )

    @staticmethod
    def update_alert_status(
        db: Session,
        alert_id: int,
        new_status: str,
    ) -> Optional[AlertResponse]:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None

        alert.status = new_status
        db.commit()
        db.refresh(alert)

        return CaseService.get_alert_by_id(db, alert.id)

    @staticmethod
    def create_alert_from_risk(
        db: Session,
        recipient_phone: str,
        risk_score: int,
        severity: str,
        message: str,
    ) -> Alert:
        """
        Creates an alert when high or critical risk is detected.
        """
        alert = Alert(
            recipient_phone=recipient_phone,
            message=message,
            severity=severity,
            status=AlertStatus.OPEN.value,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_cases(
        db: Session,
        status: Optional[str] = None,
    ) -> list[dict]:
        query = db.query(ScamCase)
        if status:
            query = query.filter(ScamCase.status == status)
        cases = query.order_by(desc(ScamCase.id)).all()

        results = []
        for case in cases:
            stored_decision = CASE_DECISIONS_STORE.get(case.id, {})
            results.append({
                "id": case.id,
                "title": case.title,
                "description": case.description,
                "scam_type": case.scam_type,
                "status": case.status,
                "decision": getattr(case, "decision", stored_decision.get("decision")),
                "notes": getattr(case, "notes", stored_decision.get("notes")),
            })
        return results

    @staticmethod
    def get_case_by_id(db: Session, case_id: int) -> Optional[dict]:
        case = db.query(ScamCase).filter(ScamCase.id == case_id).first()
        if not case:
            return None

        stored_decision = CASE_DECISIONS_STORE.get(case.id, {})
        return {
            "id": case.id,
            "title": case.title,
            "description": case.description,
            "scam_type": case.scam_type,
            "status": case.status,
            "decision": getattr(case, "decision", stored_decision.get("decision")),
            "notes": getattr(case, "notes", stored_decision.get("notes")),
        }

    @staticmethod
    def create_case(db: Session, case_data: CaseCreate) -> ScamCase:
        new_case = ScamCase(
            title=case_data.title,
            description=case_data.description,
            scam_type=case_data.scam_type,
            status=case_data.status or "OPEN",
        )
        db.add(new_case)
        db.commit()
        db.refresh(new_case)
        return new_case

    @staticmethod
    def record_case_decision(
        db: Session,
        case_id: int,
        decision: CaseDecisionType,
        notes: str,
        analyst_id: Optional[int] = None,
    ) -> Optional[dict]:
        case = db.query(ScamCase).filter(ScamCase.id == case_id).first()
        if not case:
            return None

        if decision in (CaseDecisionType.FRAUD, CaseDecisionType.FALSE_POSITIVE):
            new_status = "RESOLVED"
        else:
            new_status = "INVESTIGATING"

        case.status = new_status

        if hasattr(case, "decision"):
            setattr(case, "decision", decision.value)
        if hasattr(case, "notes"):
            setattr(case, "notes", notes)

        db.commit()
        db.refresh(case)

        CASE_DECISIONS_STORE[case.id] = {
            "decision": decision.value,
            "notes": notes,
            "analyst_id": analyst_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "case_id": case.id,
            "status": case.status,
            "decision": decision.value,
        }
