from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class AlertSeverity(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatusUpdate(BaseModel):
    status: AlertStatus = Field(
        ...,
        description="Updated alert status (OPEN, INVESTIGATING, RESOLVED)",
    )


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_phone: str
    message: str
    severity: str
    status: str
    risk_score: Optional[int] = Field(
        default=None,
        description="Calculated risk score associated with the alert",
    )
