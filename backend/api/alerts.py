"""
Alerts API Endpoints
Owner: Tigiste (Member 6) - Backend Support, Alerts, Integration & Security
Endpoints:
  GET   /alerts
  GET   /alerts/{id}
  PATCH /alerts/{id}
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.alert import (
    AlertResponse,
    AlertStatus,
    AlertStatusUpdate,
)
from backend.services.case_service import CaseService
from backend.api.dependencies import require_role, CurrentUser

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=list[AlertResponse],
    summary="Retrieve all alerts",
    description="Allows analysts to retrieve and inspect suspicious alerts. Protected (ANALYST/ADMIN only).",
)
def get_alerts(
    status: Optional[AlertStatus] = Query(
        default=None,
        description="Filter alerts by status (OPEN, INVESTIGATING, RESOLVED)",
    ),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["ANALYST", "ADMIN"])),
):
    status_filter = status.value if status else None
    return CaseService.get_alerts(db, status=status_filter)


@router.get(
    "/{id}",
    response_model=AlertResponse,
    summary="Get single alert details",
    description="Returns detailed information needed for the investigation page. Protected (ANALYST/ADMIN only).",
)
def get_alert_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["ANALYST", "ADMIN"])),
):
    alert = CaseService.get_alert_by_id(db, alert_id=id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {id} not found",
        )
    return alert


@router.patch(
    "/{id}",
    response_model=AlertResponse,
    summary="Update alert status",
    description="Updates the status of an alert (OPEN, INVESTIGATING, RESOLVED). Protected (ANALYST/ADMIN only).",
)
def update_alert(
    id: int,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["ANALYST", "ADMIN"])),
):
    updated = CaseService.update_alert_status(
        db,
        alert_id=id,
        new_status=payload.status.value,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with id {id} not found",
        )
    return updated
