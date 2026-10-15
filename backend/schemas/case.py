from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class CaseDecisionType(str, Enum):
    FRAUD = "FRAUD"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION"


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=1)
    recipient_phone: str | None = None
    alert_id: int | None = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    recipient_phone: str
    scam_type: str
    status: str
    alert_id: int | None = None
    analyst_id: int | None = None
    decision: str | None = None
    decision_notes: str | None = None
    created_at: datetime


class CaseDecisionRequest(BaseModel):
    decision: CaseDecisionType
    notes: str | None = None


class CaseDecisionResponse(BaseModel):
    id: int
    decision: str
    notes: str | None = None
    status: str
