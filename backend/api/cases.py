"""
Cases & Analyst Decision API Endpoints
Owner: Tigiste (Member 6) - Backend Support, Alerts, Integration & Security (Shared with Ahmed)
Endpoints:
  GET   /cases
  POST  /cases
  GET   /cases/{id}
  POST  /cases/{id}/decision
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.schemas.case import (
    CaseCreate,
    CaseResponse,
    CaseDecisionRequest,
    CaseDecisionResponse,
)
from backend.services.case_service import CaseService
from backend.api.dependencies import require_role, CurrentUser

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get(
    "",
    response_model=list[CaseResponse],
    summary="Retrieve all scam cases",
    description="Allows analysts to list all fraud/scam investigation cases. Protected (ANALYST/ADMIN only).",
)
def get_cases(
    status: Optional[str] = Query(
        default=None,
        description="Filter cases by status (e.g. OPEN, INVESTIGATING, RESOLVED)",
    ),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["ANALYST", "ADMIN"])),
):
    return CaseService.get_cases(db, status=status)


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scam case",
    description="Creates a new scam investigation case from an alert or report. Protected (ANALYST/ADMIN only).",
)
def create_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["ANALYST", "ADMIN"])),
):
    case = CaseService.create_case(db, case_data=payload)
    return CaseService.get_case_by_id(db, case_id=case.id)


@router.get(
    "/{id}",
    response_model=CaseResponse,
    summary="Get case details",
    description="Retrieves single case information and evidence. Protected (ANALYST/ADMIN only).",
)
def get_case_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["ANALYST", "ADMIN"])),
):
    case = CaseService.get_case_by_id(db, case_id=id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {id} not found",
        )
    return case


@router.post(
    "/{id}/decision",
    response_model=CaseDecisionResponse,
    summary="Record analyst decision on a case",
    description="Records the analyst's conclusion (FRAUD, FALSE_POSITIVE, NEEDS_MORE_INFORMATION) and notes. Protected (ANALYST/ADMIN only).",
)
def record_decision(
    id: int,
    payload: CaseDecisionRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["ANALYST", "ADMIN"])),
):
    result = CaseService.record_case_decision(
        db,
        case_id=id,
        decision=payload.decision,
        notes=payload.notes,
        analyst_id=current_user.id,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with id {id} not found",
        )
    return result
