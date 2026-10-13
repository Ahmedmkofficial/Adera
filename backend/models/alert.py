from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        # NEW: fast "does this recipient have an open alert?"
        Index("ix_alerts_phone_status", "recipient_phone", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="OPEN")

    # NEW: when the alert was raised
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )
