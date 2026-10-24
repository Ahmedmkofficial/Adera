from pydantic import BaseModel, Field


class FraudReportCreate(BaseModel):
    recipient_phone: str = Field(..., min_length=7, max_length=20)
    scam_type: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=10, max_length=2000)


class FraudReportRead(BaseModel):
    id: int
    reporter_id: int
    recipient_phone: str
    scam_type: str
    description: str
    status: str
