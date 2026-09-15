from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    recommendation: Mapped[str] = mapped_column(String(50), nullable=False)