from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CaseDecisionType(str, Enum):
    FRAUD = "FRAUD"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION"


class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=1)
    scam_type: str = Field(..., min_length=1, max_length=50)
    status: str = Field(default="OPEN", max_length=30)


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    scam_type: str
    status: str
    decision: Optional[str] = None
    notes: Optional[str] = None


class CaseDecisionRequest(BaseModel):
    decision: CaseDecisionType = Field(
        ...,
        description="Analyst decision: FRAUD, FALSE_POSITIVE, or NEEDS_MORE_INFORMATION",
    )
    notes: str = Field(
        ...,
        min_length=1,
        description="Detailed notes explaining the analyst's conclusion",
    )


class CaseDecisionResponse(BaseModel):
    case_id: int
    status: str
    decision: str
