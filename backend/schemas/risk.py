from pydantic import BaseModel, Field


class RiskCheckRequest(BaseModel):
    recipient_phone: str = Field(..., min_length=7, max_length=20)
    amount: float = Field(..., gt=0)


class RiskCheckResponse(BaseModel):
    score: int
    level: str
    recommendation: str
    reasons: list[str]