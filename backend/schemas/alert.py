from enum import Enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class AlertSeverity(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatusUpdate(BaseModel):
    status: AlertStatus = Field(
        ...,
        description="Updated alert status (OPEN, INVESTIGATING, RESOLVED, DISMISSED)",
    )


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_phone: str
    message: str
    severity: str
    status: str
    risk_score: int | None = None
    risk_level: str | None = None
    created_at: datetime | None = None
