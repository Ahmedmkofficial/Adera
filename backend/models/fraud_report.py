from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class FraudReport(Base):
    __tablename__ = "fraud_reports"
    __table_args__ = (
        # NEW: speeds up "reports for this recipient in the last N days"
        Index("ix_fraud_reports_phone_created", "recipient_phone", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # NEW: index=True (used by the "independent reporters" count)
    reporter_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=True,
    )

    # NEW: what kind of scam was reported (optional, so existing code still works)
    scam_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
