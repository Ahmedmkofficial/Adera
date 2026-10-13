from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

# NEW: join tables that link a case to the reports and accounts it covers.
scam_case_reports = Table(
    "scam_case_reports",
    Base.metadata,
    Column("case_id", ForeignKey("scam_cases.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "report_id",
        ForeignKey("fraud_reports.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)

scam_case_accounts = Table(
    "scam_case_accounts",
    Base.metadata,
    Column("case_id", ForeignKey("scam_cases.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "account_id",
        ForeignKey("payment_accounts.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)


class ScamCase(Base):
    __tablename__ = "scam_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scam_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="OPEN")

    # NEW columns (all have defaults, so existing code keeps working)
    priority: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    # NEW: the reports and accounts this case covers
    reports = relationship("FraudReport", secondary=scam_case_reports)
    accounts = relationship("PaymentAccount", secondary=scam_case_accounts)
