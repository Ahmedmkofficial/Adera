from pydantic import BaseModel


class RiskCheckRequest(BaseModel):
    recipient_phone: str
    amount: float


class RiskCheckResponse(BaseModel):
    score: int
    level: str
    recommendation: str
    reasons: list[str]