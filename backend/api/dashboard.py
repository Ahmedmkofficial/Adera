from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.security import require_roles
from backend.database.session import get_db
from backend.models.alert import Alert
from backend.models.fraud_report import FraudReport
from backend.models.scam_case import ScamCase
from backend.schemas.dashboard import DashboardSummary

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(require_roles("ANALYST", "ADMIN"))],
)


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    return {
        "alerts": db.query(Alert).count(),
        "critical": db.query(Alert).filter(Alert.severity == "CRITICAL").count(),
        "high": db.query(Alert).filter(Alert.severity == "HIGH").count(),
        "open_cases": db.query(ScamCase)
        .filter(ScamCase.status.in_({"OPEN", "INVESTIGATING"}))
        .count(),
        "reports": db.query(FraudReport).count(),
    }
