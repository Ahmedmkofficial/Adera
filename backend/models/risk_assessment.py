from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    __table_args__ = (
        # NEW: fast risk history for one recipient, ordered by time
        Index("ix_risk_assessments_phone_created", "recipient_phone", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    recommendation: Mapped[str] = mapped_column(String(50), nullable=False)

    # NEW: when this assessment was made. This is what turns the table into a
    # risk HISTORY (32 -> 48 -> 82). Filled in automatically.
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )
