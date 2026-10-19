from pydantic import BaseModel


class RecipientSummary(BaseModel):
    phone: str
    risk_score: int
    risk_level: str
    fraud_report_count: int
    independent_reporter_count: int
    recent_report_count: int
    previous_scam_case_count: int
    suspicious_relationship_count: int
