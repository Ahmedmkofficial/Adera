from pydantic import BaseModel


class DashboardSummary(BaseModel):
    alerts: int
    critical: int
    high: int
    open_cases: int
    reports: int
