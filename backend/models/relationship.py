from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class AccountRelationship(Base):
    __tablename__ = "account_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_account_id: Mapped[int] = mapped_column(ForeignKey("payment_accounts.id"), nullable=False)
    target_account_id: Mapped[int] = mapped_column(ForeignKey("payment_accounts.id"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
