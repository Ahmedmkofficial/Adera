from pydantic import BaseModel


class FraudReportCreate(BaseModel):
    reporter_id: int
    recipient_phone: str
    description: str