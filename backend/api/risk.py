from fastapi import APIRouter

from backend.schemas.risk import RiskCheckRequest, RiskCheckResponse
from backend.services.risk_engine import calculate_risk

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.post("/check", response_model=RiskCheckResponse)
def check_risk(request: RiskCheckRequest):
    result = calculate_risk(
        report_count=7,
        recent_report_count=3,
        related_case_count=2,
        suspicious_connection_count=2,
    )

    return result