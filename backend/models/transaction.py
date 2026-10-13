from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)

    # NEW: when the payment happened (filled in automatically if not given)
    timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), index=True, nullable=True
    )
